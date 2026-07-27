import functools
import html
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from odoo import fields, _
from odoo.exceptions import UserError
from odoo.http import Controller, request, route
import logging
import base64

from . import portal_trace
from . import vsf
from . import xglass
from .vsf import VSFError
from .xglass import XGlassError

_logger = logging.getLogger(__name__)

vsfAgent = vsf.VSFAgent()
xglassAgent = xglass.XGLASS()

VSF_PARTNER_PARAM = "rpbm_agent.vsf_partner_id"
VSF_DISCOUNT_PARAM = "rpbm_agent.vsf_discount"
DEFAULT_VSF_PARTNER_ID = 5708

# --- Verrou de concurrence -------------------------------------------------
# Le portail X'Glass n'autorise qu'une seule session active par identifiant,
# et RPBM ne dispose que d'un seul identifiant partagé X'Glass/VSF pour toute
# l'entreprise : deux utilisateurs Odoo ne peuvent donc jamais utiliser le
# widget en même temps sans que l'un invalide la session de l'autre côté
# portail. Ce verrou sérialise des sessions widget complètes (de
# /rpbm_agent_auth à /rpbm_agent_close), pas seulement l'appel de login.
# Réutilise ir.config_parameter (déjà restreint à base.group_system, déjà
# utilisé pour les 4 identifiants) plutôt qu'un nouveau modèle dédié.
LOCK_KEY = 'rpbm_agent.session_lock'
AGENT_LOCK_TIMEOUT = timedelta(minutes=15)  # expiration glissante, filet de sécurité


def _lock_row(cr):
    """Garantit l'existence de la ligne puis la verrouille (FOR UPDATE) pour
    la durée de la transaction courante — nécessaire pour un compare-and-set
    atomique entre deux requêtes concurrentes. Le verrou ne peut pas, et n'a
    pas besoin d'être maintenu à travers plusieurs requêtes HTTP : l'état
    {uid, touched_at} persisté dans la ligne fait foi d'une requête à l'autre.
    """
    cr.execute(
        "INSERT INTO ir_config_parameter (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING",
        (LOCK_KEY, ''),
    )
    cr.execute("SELECT value FROM ir_config_parameter WHERE key = %s FOR UPDATE", (LOCK_KEY,))
    (raw,) = cr.fetchone()
    try:
        return json.loads(raw) if raw else None
    except (TypeError, ValueError):
        return None


def _write_lock_row(cr, state):
    cr.execute(
        "UPDATE ir_config_parameter SET value = %s WHERE key = %s",
        (json.dumps(state) if state else '', LOCK_KEY),
    )


def _holder_name(env, uid):
    user = env['res.users'].sudo().browse(uid)
    return user.name if user.exists() else _("un autre utilisateur")


def acquire_agent_lock(env):
    cr, uid, now = env.cr, env.uid, datetime.now(timezone.utc)
    state = _lock_row(cr)
    if state and state['uid'] != uid:
        expired = now - datetime.fromisoformat(state['touched_at']) > AGENT_LOCK_TIMEOUT
        if not expired:
            raise UserError(_(
                "Le module véhicule/pièces est actuellement utilisé par %s. "
                "Merci de réessayer dans quelques minutes."
            ) % _holder_name(env, state['uid']))
        _logger.warning(
            "rpbm_agent: verrou expiré, récupéré de l'utilisateur #%s au profit de #%s",
            state['uid'], uid,
        )
    _write_lock_row(cr, {'uid': uid, 'touched_at': now.isoformat()})
    cr.commit()


def touch_agent_lock(env):
    cr, uid, now = env.cr, env.uid, datetime.now(timezone.utc)
    state = _lock_row(cr)
    if (not state or state['uid'] != uid
            or now - datetime.fromisoformat(state['touched_at']) > AGENT_LOCK_TIMEOUT):
        raise UserError(_(
            "Votre session a expiré ou a été reprise par un autre utilisateur. "
            "Merci de rouvrir le widget."
        ))
    state['touched_at'] = now.isoformat()
    _write_lock_row(cr, state)
    cr.commit()


def release_agent_lock(env):
    cr = env.cr
    state = _lock_row(cr)
    if state and state['uid'] == env.uid:
        _write_lock_row(cr, None)
    cr.commit()


def has_active_agent_lock(env):
    """Indique si l'appelant possède encore la session portail.

    La création Odoo d'un véhicule ne doit pas dépendre de ce verrou : les
    données métier nécessaires sont déjà envoyées par le widget. En revanche,
    le téléchargement facultatif de l'image X'Glass ne peut être tenté que
    pendant une session portail encore détenue par l'appelant.
    """
    state = _lock_row(env.cr)
    if not state or state.get('uid') != env.uid:
        return False
    try:
        return datetime.now(timezone.utc) - datetime.fromisoformat(state['touched_at']) <= AGENT_LOCK_TIMEOUT
    except (KeyError, TypeError, ValueError):
        return False


def _get_vsf_discount(env):
    """Retourne la remise RPBM configurée, avec le défaut historique à 20 %."""
    raw_value = env['ir.config_parameter'].sudo().get_param(
        VSF_DISCOUNT_PARAM, str(vsf.DEFAULT_RPBM_DISCOUNT)
    )
    try:
        discount = float(raw_value)
    except (TypeError, ValueError) as error:
        raise UserError(_("Le paramètre %s doit être un nombre compris entre 0 et 1.") % VSF_DISCOUNT_PARAM) from error
    if not 0 <= discount <= 1:
        raise UserError(_("Le paramètre %s doit être compris entre 0 et 1.") % VSF_DISCOUNT_PARAM)
    return discount


def _get_vsf_partner_id(env):
    """Retourne le fournisseur VSF configuré et vérifie qu'il existe."""
    raw_value = env['ir.config_parameter'].sudo().get_param(
        VSF_PARTNER_PARAM, str(DEFAULT_VSF_PARTNER_ID)
    )
    try:
        partner_id = int(raw_value)
    except (TypeError, ValueError) as error:
        raise UserError(_("Le paramètre %s doit contenir l'identifiant numérique d'un partenaire.") % VSF_PARTNER_PARAM) from error
    if not env['res.partner'].browse(partner_id).exists():
        raise UserError(_("Le fournisseur VSF configuré (%s) n'existe pas.") % partner_id)
    return partner_id


def _product_payload(product, matched_by=None):
    """Forme de réponse partagée par la recherche et la création de produit."""
    payload = {
        'id': product.id,
        'name': product.name,
        'default_code': product.default_code,
    }
    if matched_by:
        payload['matched_by'] = matched_by
    return payload


def _find_existing_product(env, product_code, eurocode, product_name):
    """Recherche un produit dans l'ordre métier : référence, eurocode, nom."""
    Product = env['product.product']
    if product_code:
        product = Product.search([('default_code', '=', product_code)], limit=1)
        if product:
            return product, 'reference_interne'
    if eurocode:
        product = Product.search(
            [('product_tmpl_id.x_studio_eurocode', '=', eurocode)], limit=1
        )
        if product:
            return product, 'eurocode'
    if product_name:
        product = Product.search([('name', '=ilike', product_name)], limit=1)
        if product:
            return product, 'nom'
    return Product.browse(), None


def _article_constructor_reference(article_info):
    """Référence interne attendue par le métier, avec repli VSF stable."""
    return str(
        article_info.get('refConstructeur')
        or article_info.get('code')
        or ''
    ).strip()


def _vsf_product_description(article):
    """Construit une note interne depuis les valeurs textuelles déjà parsées."""
    lines = [
        '<section class="rpbm-vsf-note">',
        '<h3>Informations VSF</h3>',
        '<p><a href="%s" target="_blank" rel="noopener">Voir la fiche VSF</a></p>'
        % html.escape(article.url or '', quote=True),
    ]
    details = list(getattr(article, 'technicalDetails', []) or [])
    if details:
        lines.append('<ul>')
        for detail in details:
            label = html.escape(str(detail.get('label') or 'Information'))
            value = html.escape(str(detail.get('value') or ''))
            if value:
                lines.append(f'<li><strong>{label} :</strong> {value}</li>')
        lines.append('</ul>')
    lines.append('</section>')
    return ''.join(lines)


def _touch_agent_lock(f):
    """À placer directement sous @route, pour que le UserError levé ici ne
    soit jamais avalé par le try/except propre à certaines routes."""
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        touch_agent_lock(request.env)
        return f(self, *args, **kwargs)
    return wrapper


class AgentController(Controller):

    @route('/rpbm_agent_auth', auth='user', type='json')
    def rpbm_agent_auth(self):
        global vsfAgent
        global xglassAgent
        acquire_agent_lock(request.env)
        _logger.info("rpbm_agent_auth")
        params = request.env['ir.config_parameter'].sudo()
        portal_trace.configure(
            params.get_param('rpbm_agent.trace') in ('1', 'true', 'True'),
            params.get_param('rpbm_agent.trace_dir'),
        )
        VSF_LOGIN = params.get_param('VSF_LOGIN')
        VSF_PASSWORD = params.get_param('VSF_PASSWORD')
        XGLASS_USER = params.get_param('XGLASS_USER')
        XGLASS_PASS = params.get_param('XGLASS_PASS')
        # Déconnecte la session portail précédente *avant* de repartir de zéro :
        # l'agent encore en mémoire porte ses cookies, donc son logout aboutit.
        # (Fermer un agent fraîchement construit, comme auparavant, ne
        # déconnectait rien et laissait la session traîner côté X'Glass.)
        xglassAgent.close()
        vsfAgent = vsf.VSFAgent()
        xglassAgent = xglass.XGLASS()
        # Pas de nouvelle tentative ici : XGLASS.auth() gère déjà la reprise
        # d'une session restée ouverte côté portail.
        try:
            xglassAgent.auth(XGLASS_USER, XGLASS_PASS)
        except XGlassError:
            _logger.exception("Échec de connexion à X'Glass")
            release_agent_lock(request.env)
            raise UserError(_(
                "Connexion au portail X'Glass impossible. Vérifiez les identifiants "
                "configurés, ou réessayez dans quelques instants."
            ))
        try:
            vsfAgent.auth(VSF_LOGIN, VSF_PASSWORD)
        except VSFError:
            _logger.exception("Échec de connexion à VSF")
            release_agent_lock(request.env)
            raise UserError(_("Connexion au portail VSF impossible. Vérifiez les identifiants configurés."))
        _logger.info("rpbm_agent_auth done")
        return

    @route('/rpbm_agent_close', auth='user', type='json')
    def rpbm_agent_close(self):
        _logger.info("rpbm_agent_close")
        xglassAgent.close()
        # vsfAgent.close()
        release_agent_lock(request.env)
        _logger.info("rpbm_agent_close done")
        return

    @route('/searchImmatriculation', auth='user', type='json')
    @_touch_agent_lock
    def searchImmatriculation(self,immatriculation: str):
        _logger.info(f"searchImmatriculation {immatriculation}")
        try:
            vehicules = xglassAgent.searchVehiculeImmat(immatriculation)
            return [vehicule.__dict__ for vehicule in vehicules]
        except XGlassError:
            _logger.exception("Erreur X'Glass lors de la recherche immatriculation %s", immatriculation)
            raise UserError(_("Recherche impossible : le portail X'Glass est inaccessible ou la session a expiré."))

    @route(['/rpbm_agent/getVehiculeMeta', '/rbm_agent/getVehiculeMeta'], auth='user', type='json')
    @_touch_agent_lock
    def getVehiculeMeta(self,vehiculeId:str):
        _logger.info(f"getVehiculeMeta {vehiculeId}")
        # Il faut d'abord réinitialiser la planche
        self.getPlanche(int(vehiculeId))
        return xglassAgent.getVehiculeMeta(vehiculeId)

    @route('/getOdooVehicule', auth='user', type='json')
    def getVehicule(self,immatriculation:str):
        """
            Permet de retourner l'ID du véhicule enregistré en BDD de Odoo, si 
            le véhicule n'existe pas, retourne False
        """
        # _logger.info(f"getVehicule {vehicule}")
        vehicules = request.env['fleet.vehicle'].search([('license_plate', '=', immatriculation)])
        if vehicules:
            if len(vehicules) > 1:
                _logger.warning(f"Plusieurs véhicules avec la même immatriculation {immatriculation}")
            vehicule = vehicules[0]
            return vehicule.read()[0]
        else:
            return False

    @route('/createVehicule', auth='user', type='json')
    def createVehicule(self,immatriculation:str, partner_id:int, vehicule_info:dict={}, vehicule_meta:dict={}):
        """
            Permet de créer un véhicule en BDD de Odoo

            Cette route crée avant tout un enregistrement Odoo. Elle ne doit
            pas échouer si un client obsolète a déjà fermé la session X'Glass :
            l'image portail est facultative et les autres données ont déjà été
            reçues dans ``vehicule_info``.
        """
        _logger.info(f"getVehicule {vehicule_info}")
        vehicule = xglass.XGlassVehicule(**vehicule_info)
        vehicules = request.env['fleet.vehicle'].search([('license_plate', '=', immatriculation)])
        if vehicules:
            if len(vehicules) > 1:
                _logger.warning(f"Plusieurs véhicules avec la même immatriculation {immatriculation}")
            vehicule = vehicules[0]
        else:
            marque = request.env['fleet.vehicle.model.brand'].search([('name', '=', vehicule.xGlassModele.xGlassMarque.nom)])
            if not marque:
                marque = request.env['fleet.vehicle.model.brand'].create({
                    'name': vehicule.xGlassModele.xGlassMarque.nom
                })
            modele = request.env['fleet.vehicle.model'].search([('name', '=', vehicule.xGlassModele.gamme)])
            if not modele:
                modele = request.env['fleet.vehicle.model'].create({
                    'name': vehicule.xGlassModele.gamme,
                    'brand_id': marque.id
                })
            data = {}
            if vehicule_meta is not None:
                vin = vehicule_meta.get('vin', False)
                dateMec = vehicule_meta.get('dateMec', False)
                _logger.info(f"vin {vin} dateMec {dateMec}")
                if vin:
                    data['vin_sn'] = vin
                if dateMec:
                    # convert %m/%Y to date format
                    import datetime
                    date:datetime.date = datetime.datetime.strptime(dateMec, '%m/%Y').date()
                    _logger.info(f"date {date}")
                    data['x_studio_date_mec'] = fields.Date.from_string(date)
                    _logger.info(f"x_studio_date_mec {data['x_studio_date_mec']}")
            fuel_type_field = request.env['ir.model.fields'].search([('name', '=', 'fuel_type'),('model_id.model','=','fleet.vehicle')], limit=1)
            _logger.info(f"fuel_type_field {fuel_type_field}")
            fuel_type = request.env['ir.model.fields.selection'].search([
                ('field_id','=',fuel_type_field.id),  # fuel_type field
                ('name', '=', vehicule.energieLibelle)
            ])
            _logger.info(f"fuel_type {fuel_type}")
            if not fuel_type:
                fuel_type = request.env['ir.model.fields.selection'].create({
                    'field_id': fuel_type_field.id,  # fuel_type field
                    'name': vehicule.energieLibelle,
                    'value': vehicule.energieLibelle,
                })
            # L'image X'Glass est un enrichissement facultatif. Après la
            # fermeture de la session portail, on crée tout de même le véhicule
            # sans image plutôt que de transformer un cache d'asset frontend en
            # erreur bloquante de création.
            image = False
            if vehicule.imgUrl and has_active_agent_lock(request.env):
                try:
                    response = xglassAgent.get(vehicule.imgUrl)
                    xglassAgent.ensure_logged(response)
                    if response.status_code == 200:
                        image = base64.b64encode(response.content).replace(b"\n", b"")
                    else:
                        _logger.warning("Image X'Glass introuvable pour %s", vehicule.imgUrl)
                except XGlassError:
                    _logger.warning(
                        "Image X'Glass indisponible pour %s ; véhicule créé sans image",
                        immatriculation,
                    )
            elif vehicule.imgUrl:
                _logger.info(
                    "Session X'Glass déjà fermée : véhicule %s créé sans image",
                    immatriculation,
                )
            vehicule = request.env['fleet.vehicle'].create({
                'driver_id': partner_id,
                'model_id': modele.id,
                'license_plate': immatriculation,
                'description': vehicule.libelleCourt,
                'power': vehicule.puissanceKw,
                'doors': vehicule.portesNbr,
                'fuel_type': fuel_type.value,
                'x_studio_detail_model':vehicule.libelleCourt,
                'image_1920': image,
                **data,

            })
            _logger.info(f"Véhicule créé {vehicule}")

        return vehicule.id


    @route('/getPlanche', auth='user', type='json')
    @_touch_agent_lock
    def getPlanche(self,vehiculeId:int):
        _logger.info(f"getPlanche {vehiculeId}")
        planche = xglassAgent.selectVehicule(str(vehiculeId))
        return planche

    @route('/getPieces', auth='user', type='json')
    @_touch_agent_lock
    def getPieces(self,plancheId:int, calqueId:int):
        _logger.info(f"getPieces {plancheId} {calqueId}")
        raw = xglassAgent.getPiecesData(plancheId, calqueId)
        rawData = {
            'ELEMENTSIT_PRINCIPAUX': [xglass.XGlassElement(**element) for element in raw.get('ELEMENTSIT_PRINCIPAUX', [])],
            'ELEMENTSIT_COMPLEMENTAIRES': [xglass.XGlassElement(**element) for element in raw.get('ELEMENTSIT_COMPLEMENTAIRES', [])],
        }
        pieces = []

        for elementKey,Elements in rawData.items():
            for Element in Elements:
                for XGLasspiece in Element.pieces:
                    piece = XGLasspiece.__dict__
                    piece['elementKey'] = elementKey
                    piece['element.withPiecesAm'] = Element.withPiecesAm
                    piece['elementSitId'] = Element.elementSitId
                    pieces.append(piece)
        return pieces

    @route('/getPieceAm', auth='user', type='json')
    @_touch_agent_lock
    def getPieceAm(self,element_withPiecesAm, pieceId:int=None, elementSitId:int=None):
        _logger.info(f"getPieceAm {element_withPiecesAm} {pieceId} {elementSitId}")
        # Réutilise XGLASS.findSelectionsPiecesAmView() au lieu de dupliquer
        # l'appel HTTP (URL/payload) — voir docs/etat-des-lieux.md. On ne
        # réutilise pas XGLASS.getPieceAm() (qui construit des XGlassPieceAm)
        # pour ne pas changer la forme de la réponse déjà consommée par le widget.
        element = SimpleNamespace(withPiecesAm=element_withPiecesAm, elementSitId=elementSitId)
        piece = SimpleNamespace(id=pieceId) if pieceId else None
        try:
            r = xglassAgent.findSelectionsPiecesAmView(element, piece)
            return r.json().get('selectionsPiecesAmView', [])
        except XGlassError:
            _logger.exception("Erreur X'Glass lors de la recherche des pièces après-marché")
            raise UserError(_("Recherche impossible : le portail X'Glass est inaccessible ou la session a expiré."))

    @route('/searchBaseEurocode', auth='user', type='json')
    @_touch_agent_lock
    def searchBaseEurocode(self,baseEurocode:str):
        _logger.info(f"searchBaseEurocode {baseEurocode}")
        try:
            discount = _get_vsf_discount(request.env)
            vsfArticles = vsfAgent.searchEurocodeArticlesClient(baseEurocode)
            for vsf_article in vsfArticles:
                vsf_article.set_rpbm_discount(discount)
            return [vsfArticle.__dict__ for vsfArticle in vsfArticles]
        except VSFError:
            _logger.exception("Erreur VSF lors de la recherche eurocode %s", baseEurocode)
            raise UserError(_("Recherche impossible : le portail VSF est inaccessible ou la session a expiré."))

    @route('/doesProductExists', auth='user', type='json')
    def doesProductExists(self, articleVsfInfo=None, productCode=None):
        """Cherche un produit VSF par référence interne, eurocode, puis nom.

        ``productCode`` est conservé temporairement pour les anciens assets
        frontend ; le contrat courant envoie l'article VSF complet.
        """
        article_info = articleVsfInfo or {'code': productCode}
        product_code = _article_constructor_reference(article_info)
        eurocode = str(article_info.get('code') or '').strip()
        product_name = str(article_info.get('name') or '').strip()
        product, matched_by = _find_existing_product(
            request.env, product_code, eurocode, product_name
        )
        return _product_payload(product, matched_by) if product else False

    @route('/getVsfArticleDetails', auth='user', type='json')
    @_touch_agent_lock
    def get_vsf_article_details(self, articleVsfInfo=None):
        """Retourne les détails de fiche nécessaires au widget, sans écriture Odoo."""
        article_info = articleVsfInfo or {}
        code = str(article_info.get('code') or '').strip()
        if not code:
            raise UserError(_("Lecture impossible : le code VSF de l'article est absent."))
        try:
            details = vsfAgent.getArticleDetails(article_info)
            article = vsf.VSFArticle(
                _rpbm_discount=_get_vsf_discount(request.env), **details
            )
            return article.__dict__
        except VSFError:
            _logger.exception("Erreur VSF lors de la lecture de l'article %s", code)
            raise UserError(_("Lecture impossible : la fiche article VSF est inaccessible."))

    @route('/createProduct', auth='user', type='json')
    @_touch_agent_lock
    def createProduct(self,articleVsfInfo:dict):
        _logger.info(f"createProduct {articleVsfInfo}")
        product_code = str(articleVsfInfo.get('code') or '').strip()
        if not product_code:
            raise UserError(_("Création impossible : le code VSF de l'article est absent."))

        # Sérialise les créations par code : un double-clic ou deux requêtes
        # simultanées ne peuvent pas créer deux produits avec le même code.
        request.env.cr.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))",
            (f"rpbm_agent.product:{product_code}",),
        )
        try:
            article_details = vsfAgent.getArticleDetails(articleVsfInfo)
            article_vsf = vsf.VSFArticle(
                _rpbm_discount=_get_vsf_discount(request.env), **article_details
            )
            constructor_reference = _article_constructor_reference(article_vsf.__dict__)
            existing_product, matched_by = _find_existing_product(
                request.env,
                constructor_reference,
                article_vsf.code,
                str(article_vsf.name or '').strip(),
            )
            if existing_product:
                return _product_payload(existing_product, matched_by)
            if article_vsf.prixVente is None or article_vsf.prixVenteRPBM is None:
                raise UserError(_("Création impossible : le prix de l'article VSF est absent."))

            image = False
            image_urls = article_vsf.fullImageUrls or article_vsf.absoluteImgUrls
            if image_urls:
                try:
                    response = vsfAgent.get(image_urls[0])
                    if response.status_code == 200:
                        image = base64.b64encode(response.content).replace(b"\n", b"")
                    else:
                        _logger.warning("Image VSF introuvable pour %s", article_vsf.code)
                except VSFError:
                    _logger.warning("Image VSF indisponible pour %s ; produit créé sans image", article_vsf.code)

            product = request.env['product.product'].create(
                vsf.product_creation_values(
                    article_vsf,
                    _vsf_product_description(article_vsf),
                    image=image,
                )
            )
            request.env['product.supplierinfo'].create({
                'partner_id': _get_vsf_partner_id(request.env),
                'product_id': product.id,
                'delay': 1,
                'min_qty': 0,
                'price': article_vsf.prixVenteRPBM,
            })
        except UserError:
            raise
        except Exception as error:
            _logger.exception("Erreur lors de la création du produit VSF %s", product_code)
            raise UserError(_("Création impossible pour l'article VSF %s.") % product_code) from error

        _logger.info("Produit VSF créé %s", product)
        return _product_payload(product, 'créé')


