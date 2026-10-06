import functools
import json
import re
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from odoo import fields, _
from odoo.exceptions import AccessError, UserError
from odoo.http import Controller, request, route
import logging
import base64

from . import portal_trace
from . import vsf
from . import xglass
from .vsf import VSFError, VSFAuthError
from .vsf_config import get_vsf_discount, get_vsf_partner_id
from .xglass import XGlassError, XGlassAuthError
from ..models.legacy_fields import NameIndex, clean_vin, is_legacy_malformed_vin, month_year_to_date

_logger = logging.getLogger(__name__)

vsfAgent = vsf.VSFAgent()
xglassAgent = xglass.XGLASS()

# Produits de service contrôlés sur rpbm-preprod, surchargeables par les
# paramètres système rpbm_agent.labor_product_t1/t2/t3. Le widget ne calcule
# jamais leur prix : l'onchange Odoo applique prix, taxes et règle fiscale.
LABOR_PRODUCT_BY_RATE = {"T1": 24, "T2": 23, "T3": 113}

# Énergie X'Glass (champ `energie` du véhicule) -> clé native fleet.FUEL_TYPES.
# Créer une valeur de sélection sur le champ de base fuel_type est refusé par
# Odoo (ir.model.fields.selection.create) : une énergie inconnue laisse le
# champ vide plutôt que de faire échouer la création du véhicule.
# ponytail: « Électrique & X » lu comme plug-in, « X Hybride » comme full hybrid ;
# à ajuster si le métier distingue autrement.
XGLASS_ENERGY_TO_FUEL_TYPE = {
    233: "gasoline",
    234: "diesel",
    235: "cng",
    236: "lpg",
    240: "plug_in_hybrid_diesel",
    241: "plug_in_hybrid_gasoline",
    273: "electric",
    706853: "full_hybrid",
    706854: "full_hybrid",
}


def _xglass_fuel_type(energie):
    """Retourne la clé fleet.FUEL_TYPES d'une énergie X'Glass, ou False."""
    try:
        return XGLASS_ENERGY_TO_FUEL_TYPE.get(int(energie), False)
    except (TypeError, ValueError):
        return False


def _labor_products(env):
    """Produits de main-d'œuvre par taux, lus depuis les paramètres système."""
    params = env["ir.config_parameter"].sudo()
    products = {}
    for rate, default in LABOR_PRODUCT_BY_RATE.items():
        key = "rpbm_agent.labor_product_%s" % rate.lower()
        raw_value = params.get_param(key, str(default))
        try:
            products[rate] = int(raw_value)
        except (TypeError, ValueError) as error:
            raise UserError(_("Le paramètre %s doit contenir l'identifiant numérique d'un produit.") % key) from error
    return products


def _xglass_labor_rate(raw_temps):
    """Normalise exclusivement les taux X'Glass validés pour la facturation."""
    candidates = [raw_temps.get("taux"), raw_temps.get("activite", {}).get("code"),
                  raw_temps.get("activite", {}).get("libelle"),
                  raw_temps.get("operationTemps", {}).get("libelleCourt")]
    for candidate in candidates:
        match = re.search(r"(?:^|[^A-Z0-9])(?:[TCM])?([123])(?:$|[^A-Z0-9])", str(candidate or "").upper())
        if match:
            return "T%s" % match.group(1)
    return False


def _labor_operation_payload(piece_id, raw_temps, products=LABOR_PRODUCT_BY_RATE):
    """Retourne le contrat minimal et sûr consommé par le widget devis."""
    operation = raw_temps.get("operationTemps") or {}
    operation_id = raw_temps.get("id") or operation.get("id")
    duration = raw_temps.get("temps")
    rate = _xglass_labor_rate(raw_temps)
    label = operation.get("libelle") or operation.get("libelleCourt") or raw_temps.get("libelle") or _("Opération X'Glass")
    payload = {
        "key": "%s:%s" % (piece_id, operation_id) if operation_id else False,
        "label": label,
        "nature": (raw_temps.get("activite") or {}).get("nature"),
        "rate": rate,
        "duration": duration,
        "productId": products.get(rate),
        "unavailableReason": False,
    }
    if not payload["key"]:
        payload["unavailableReason"] = _("Identifiant d'opération X'Glass absent.")
    elif not isinstance(duration, (int, float)) or duration <= 0:
        payload["unavailableReason"] = _("Durée X'Glass absente ou invalide.")
    elif not payload["productId"]:
        payload["unavailableReason"] = _("Taux X'Glass non pris en charge : %s.") % (rate or _("inconnu"))
    return payload

# --- Verrou de concurrence -------------------------------------------------
# Le portail X'Glass n'autorise qu'une seule session active par identifiant,
# et RPBM ne dispose que d'un seul identifiant X'Glass pour toute
# l'entreprise : deux utilisateurs Odoo ne peuvent donc jamais utiliser
# X'Glass en même temps sans que l'un invalide la session de l'autre côté
# portail. Ce verrou sérialise des sessions X'Glass complètes (de
# /rpbm_agent_auth à /rpbm_agent_close), pas seulement l'appel de login.
# Il ne protège que X'Glass : VSF tolère plusieurs sessions sur le même compte
# (trace T1 du 2026-10-06) et ses routes passent par _vsf_call, sans verrou.
# Réutilise ir.config_parameter (déjà restreint à base.group_system, déjà
# utilisé pour les 4 identifiants) plutôt qu'un nouveau modèle dédié.
LOCK_KEY = 'rpbm_agent.session_lock'
AGENT_LOCK_TIMEOUT = timedelta(minutes=15)  # expiration glissante, filet de sécurité


class AgentSessionExpiredError(UserError):
    """Erreur JSON-RPC récupérable par le widget sans lire un texte traduit."""


def _raise_portal_error(error, user_message, log_message):
    """Préserve un marqueur stable pour une authentification X'Glass expirée."""
    _logger.exception(log_message)
    if isinstance(error, XGlassAuthError):
        raise AgentSessionExpiredError(_(
            "La session des portails a expiré. Reconnexion nécessaire."
        )) from error
    # VSF se reconnecte côté serveur (_vsf_call) : une VSFAuthError arrivée ici est un
    # échec de connexion, qui ne doit pas déclencher la reconnexion X'Glass du widget.
    if isinstance(error, VSFAuthError):
        raise UserError(_("Connexion au portail VSF impossible. Vérifiez les identifiants configurés.")) from error
    raise UserError(user_message) from error


def _configure_trace(params):
    """Relit le traçage portail ; remet à zéro la numérotation des requêtes tracées."""
    portal_trace.configure(
        params.get_param('rpbm_agent.trace') in ('1', 'true', 'True'),
        params.get_param('rpbm_agent.trace_dir'),
    )


def _vsf_call(fn):
    """Exécute ``fn(vsfAgent)`` avec la session VSF du processus, connectée à la demande."""
    # Les routes VSF n'ont plus le verrou X'Glass, qui les fermait de fait aux autres
    # utilisateurs ; /createProduct crée en sudo.
    if not request.env.user._is_internal():
        raise AccessError(_("Le portail VSF est réservé aux utilisateurs internes."))
    params = request.env['ir.config_parameter'].sudo()
    if not vsfAgent.logged_in:
        _configure_trace(params)
    return vsfAgent.with_session(params.get_param('VSF_LOGIN'), params.get_param('VSF_PASSWORD'), fn)


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
        raise AgentSessionExpiredError(_(
            "Votre session des portails a expiré ou a été reprise par un autre utilisateur."
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
    """Recherche un produit dans l'ordre métier : eurocode, référence interne, nom.

    Un produit qui porte l'eurocode d'un autre article n'est jamais retenu : la
    référence interne (quand l'eurocode est connu) et le nom ne rattachent qu'un
    produit sans eurocode, et le nom seulement s'il n'en désigne qu'un.
    """
    Product = env['product.product']
    # `= False` ne couvre que NULL ; un eurocode vide compte aussi comme absent.
    without_eurocode = [('product_tmpl_id.rpbm_eurocode', 'in', [False, ''])]
    if eurocode:
        product = Product.search(
            [('product_tmpl_id.rpbm_eurocode', '=', eurocode)], limit=1
        )
        if product:
            return product, 'eurocode'
    if product_code:
        product = Product.search(
            [('default_code', '=', product_code)] + (without_eurocode if eurocode else []),
            limit=1,
        )
        if product:
            return product, 'reference_interne'
    if product_name:
        products = Product.search(
            [('name', '=ilike', product_name)] + without_eurocode, limit=2
        )
        if len(products) == 1:
            return products, 'nom'
    return Product.browse(), None


def _article_constructor_reference(article_info):
    """Référence interne attendue par le métier, avec repli VSF stable."""
    return vsf.constructor_reference_or_vsf_code(
        article_info.get('refConstructeur'), article_info.get('code')
    ).strip()


def _vsf_article_payload(article_details, discount):
    """Normalise aussi les suggestions pour que le frontend ait un contrat unique."""
    article = vsf.VSFArticle(_rpbm_discount=discount, **article_details)
    article.suggestedArticles = [
        vsf.VSFArticle(_rpbm_discount=discount, **suggestion).__dict__
        for suggestion in article.suggestedArticles
    ]
    return article


def _fleet_vehicle_metadata_values(vehicule_meta, warnings):
    """Convertit les métadonnées X'Glass (VIN, date MEC) en valeurs Fleet sûres."""
    if not isinstance(vehicule_meta, dict):
        return {}
    values = {}
    vin = clean_vin(vehicule_meta.get('vin'))
    if vin:
        values['vin_sn'] = vin
    raw_date_mec = vehicule_meta.get('dateMec')
    if raw_date_mec:
        date_mec = month_year_to_date(raw_date_mec)
        if date_mec is None:
            warnings.append(_("Date MEC X'Glass invalide ; la valeur Fleet reste inchangée."))
        else:
            values['rpbm_first_registration_date'] = date_mec
    return values


def _enrich_fleet_vehicle_from_metadata(vehicle, vehicule_meta, warnings):
    """Complète uniquement les champs Fleet manquants depuis X'Glass ; le seul remplacement
    admis est un VIN de l'ancienne forme ``var = <VIN>;``."""
    metadata_values = _fleet_vehicle_metadata_values(vehicule_meta, warnings)
    if not metadata_values:
        return {}
    try:
        values_to_write = {
            name: value for name, value in metadata_values.items()
            if not vehicle[name] or (name == 'vin_sn' and is_legacy_malformed_vin(vehicle.vin_sn))
        }
        if values_to_write:
            vehicle.sudo().write(values_to_write)
        return values_to_write
    except AccessError:
        warnings.append(_("Écriture des métadonnées Fleet interdite ; véhicule laissé tel quel."))
        return {}


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
        global xglassAgent
        acquire_agent_lock(request.env)
        _logger.info("rpbm_agent_auth")
        params = request.env['ir.config_parameter'].sudo()
        _configure_trace(params)
        XGLASS_USER = params.get_param('XGLASS_USER')
        XGLASS_PASS = params.get_param('XGLASS_PASS')
        # Déconnecte la session portail précédente *avant* de repartir de zéro :
        # l'agent encore en mémoire porte ses cookies, donc son logout aboutit.
        # (Fermer un agent fraîchement construit, comme auparavant, ne
        # déconnectait rien et laissait la session traîner côté X'Glass.)
        # VSF n'est plus connecté ici : voir _vsf_call.
        xglassAgent.close()
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
        _logger.info("rpbm_agent_auth done")
        return

    @route('/rpbm_agent_close', auth='user', type='json')
    def rpbm_agent_close(self):
        _logger.info("rpbm_agent_close")
        # Les routes VSF ne prolongent plus le verrou : après 15 min de travail VSF seul, un autre
        # utilisateur a pu le reprendre et charger X'Glass. Sa session n'est alors pas déconnectée.
        state = _lock_row(request.env.cr)
        if not state or state.get('uid') == request.env.uid:
            xglassAgent.close()
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
        except XGlassError as error:
            _raise_portal_error(
                error,
                _("Recherche impossible : le portail X'Glass est inaccessible."),
                "Erreur X'Glass lors de la recherche immatriculation %s" % immatriculation,
            )

    @route('/rpbm_agent/getVehiculeMeta', auth='user', type='json')
    @_touch_agent_lock
    def getVehiculeMeta(self,vehiculeId:str):
        _logger.info(f"getVehiculeMeta {vehiculeId}")
        try:
            # selectVehicule() pose la sélection côté portail et met en cache la
            # page, que getVehiculeMeta() relit : un seul aller-retour X'Glass
            # pour la planche et les métadonnées.
            planche = xglassAgent.selectVehicule(str(vehiculeId))
            return {'meta': xglassAgent.getVehiculeMeta(vehiculeId), 'planche': planche}
        except XGlassError as error:
            _raise_portal_error(
                error,
                _("Lecture impossible : le portail X'Glass est inaccessible."),
                "Erreur X'Glass lors de la lecture des métadonnées véhicule %s" % vehiculeId,
            )

    @route('/getOdooVehicule', auth='user', type='json')
    def getVehicule(self,immatriculation:str):
        """
            Permet de retourner l'ID du véhicule enregistré en BDD de Odoo, si 
            le véhicule n'existe pas, retourne False
        """
        vehicules = request.env['fleet.vehicle'].search([('license_plate', '=', immatriculation)])
        if not vehicules:
            return False
        if len(vehicules) > 1:
            _logger.warning(f"Plusieurs véhicules avec la même immatriculation {immatriculation}")
        return vehicules[0].read(['name', 'driver_id'])[0]

    @route('/enrichVehicule', auth='user', type='json')
    def enrich_vehicule(self, vehicle_id: int, vehicule_meta=None):
        """Complète un véhicule Fleet existant sans remplacer ses données."""
        if isinstance(vehicle_id, bool) or not isinstance(vehicle_id, int) or vehicle_id <= 0:
            raise UserError(_("vehicle_id doit être un entier strictement positif."))

        warnings = []
        try:
            vehicles = request.env['fleet.vehicle'].search(
                [('id', '=', vehicle_id)], limit=1
            )
        except AccessError:
            warnings.append(_("Lecture du véhicule Fleet interdite ; aucun enrichissement."))
            return {'values': {}, 'warnings': warnings}
        if not vehicles:
            warnings.append(_("Véhicule %s introuvable ou inaccessible.") % vehicle_id)
            return {'values': {}, 'warnings': warnings}

        _enrich_fleet_vehicle_from_metadata(vehicles[0], vehicule_meta, warnings)
        return {'values': {}, 'warnings': warnings}

    @route('/createVehicule', auth='user', type='json')
    def createVehicule(
        self, immatriculation: str, partner_id: int,
        vehicule_info=None, vehicule_meta=None,
    ):
        """
            Permet de créer un véhicule en BDD de Odoo

            Cette route crée avant tout un enregistrement Odoo. Elle ne doit
            pas échouer si un client obsolète a déjà fermé la session X'Glass :
            l'image portail est facultative et les autres données ont déjà été
            reçues dans ``vehicule_info``.
        """
        vehicule_info = vehicule_info or {}
        vehicule_meta = vehicule_meta or {}
        _logger.info("createVehicule %s", immatriculation)
        vehicule = xglass.XGlassVehicule(**vehicule_info)
        # Deux appels concurrents pour la même plaque (bouton « Créer » puis « Confirmer » avant la fin
        # du premier) créaient deux véhicules (recette 2026-09-20) : verrou transactionnel par plaque.
        request.env.cr.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ("rpbm_agent.vehicle:" + immatriculation,))
        vehicules = request.env['fleet.vehicle'].search([('license_plate', '=', immatriculation)])
        if vehicules:
            if len(vehicules) > 1:
                _logger.warning(f"Plusieurs véhicules avec la même immatriculation {immatriculation}")
            vehicule = vehicules[0]
            warnings = []
            _enrich_fleet_vehicle_from_metadata(vehicule, vehicule_meta, warnings)
            for warning in warnings:
                _logger.warning(warning)
        else:
            # Référentiels Fleet par nom normalisé (casse, accents), modèle restreint à sa marque :
            # la base porte des homonymes (« Renault »/« RENAULT », deux « MEGANE »), un search par
            # nom seul renvoyait plusieurs enregistrements (Expected singleton, recette 2026-09-20).
            marque_id = NameIndex(request.env, 'fleet.vehicle.model.brand', 'name').get_or_create(
                vehicule.xGlassModele.xGlassMarque.nom)
            marque = request.env['fleet.vehicle.model.brand'].browse(marque_id)
            modele_id = NameIndex(request.env, 'fleet.vehicle.model', 'name', [('brand_id', '=', marque.id)]).get_or_create(
                vehicule.xGlassModele.gamme, {'brand_id': marque.id})
            modele = request.env['fleet.vehicle.model'].browse(modele_id)
            metadata_warnings = []
            data = _fleet_vehicle_metadata_values(vehicule_meta, metadata_warnings)
            for warning in metadata_warnings:
                _logger.warning(warning)
            fuel_type = _xglass_fuel_type(getattr(vehicule, 'energie', None))
            if not fuel_type:
                _logger.warning(
                    "Énergie X'Glass %s (%s) sans équivalent Fleet : véhicule %s créé sans énergie",
                    getattr(vehicule, 'energie', None), vehicule.energieLibelle, immatriculation,
                )
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
            # sudo : les commerciaux n'ont que la lecture sur Fleet (security/ir.model.access.csv) ;
            # la création passe uniquement par ce widget, avec les données X'Glass.
            vehicule = request.env['fleet.vehicle'].sudo().create({
                'driver_id': partner_id,
                'model_id': modele.id,
                'license_plate': immatriculation,
                'description': vehicule.libelleCourt,
                'power': vehicule.puissanceKw,
                'doors': vehicule.portesNbr,
                'fuel_type': fuel_type,
                'rpbm_detail_model': vehicule.libelleCourt,
                'image_1920': image,
                **data,

            })
            _logger.info(f"Véhicule créé {vehicule}")

        return {'id': vehicule.id, 'name': vehicule.name}


    @route('/getPlanche', auth='user', type='json')
    @_touch_agent_lock
    def getPlanche(self,vehiculeId:int):
        _logger.info(f"getPlanche {vehiculeId}")
        try:
            return xglassAgent.selectVehicule(str(vehiculeId))
        except XGlassError as error:
            _raise_portal_error(
                error,
                _("Chargement impossible : le portail X'Glass est inaccessible."),
                "Erreur X'Glass lors du chargement de la planche véhicule %s" % vehiculeId,
            )

    @route('/getPieces', auth='user', type='json')
    @_touch_agent_lock
    def getPieces(self,plancheId:int, calqueId:int):
        _logger.info(f"getPieces {plancheId} {calqueId}")
        try:
            raw = xglassAgent.getPiecesData(plancheId, calqueId)
        except XGlassError as error:
            _raise_portal_error(
                error,
                _("Recherche impossible : le portail X'Glass est inaccessible."),
                "Erreur X'Glass lors de la recherche des pièces",
            )
        rawData = {
            'ELEMENTSIT_PRINCIPAUX': [xglass.XGlassElement(**element) for element in raw.get('ELEMENTSIT_PRINCIPAUX', [])],
            'ELEMENTSIT_COMPLEMENTAIRES': [xglass.XGlassElement(**element) for element in raw.get('ELEMENTSIT_COMPLEMENTAIRES', [])],
        }
        pieces = []
        labor_products = _labor_products(request.env)
        # Drapeaux et clés tracés sans prix ni corps de réponse : ils décideront plus tard quelles
        # familles montrent l'encart « Autres marques AM » (aujourd'hui toutes, repliées).
        unknown_keys = {
            key: len(value) if isinstance(value, (list, dict)) else type(value).__name__
            for key, value in raw.items() if key not in rawData
        }
        if unknown_keys:
            _logger.info("getPieces %s %s : clés elementSitMapData ignorées %s", plancheId, calqueId, unknown_keys)

        for elementKey,Elements in rawData.items():
            for Element in Elements:
                _logger.info(
                    "getPieces %s %s : %s elementSitId=%s libellé=%s affichageAm=%s containsPiecesAm=%s "
                    "elementVitre=%s pièces=%s",
                    plancheId, calqueId, elementKey, Element.elementSitId, Element.libelle,
                    getattr(Element, 'affichageAm', None), getattr(Element, 'containsPiecesAm', None),
                    getattr(Element, 'elementVitre', None), len(Element.pieces),
                )
                for XGLasspiece in Element.pieces:
                    piece = XGLasspiece.__dict__
                    piece['elementKey'] = elementKey
                    piece['element.withPiecesAm'] = Element.withPiecesAm
                    piece['elementSitId'] = Element.elementSitId
                    piece['elementSitLibelle'] = Element.libelle
                    piece['laborOperations'] = [
                        _labor_operation_payload(piece['id'], temps, labor_products)
                        for temps in piece.get('tempsList', [])
                    ]
                    pieces.append(piece)
        return pieces

    @route('/getPieceAm', auth='user', type='json')
    @_touch_agent_lock
    def getPieceAm(self,element_withPiecesAm, pieceId:int=None, elementSitId:int=None):
        _logger.info(f"getPieceAm {element_withPiecesAm} {pieceId} {elementSitId}")
        # Réutilise XGLASS.findSelectionsPiecesAmView() : la liste `selectionsPiecesAmView` est
        # renvoyée telle quelle (forme consommée par le widget) ; une réponse illisible y devient
        # une XGlassError, donc une erreur utilisateur typée ci-dessous.
        element = SimpleNamespace(withPiecesAm=element_withPiecesAm, elementSitId=elementSitId)
        piece = SimpleNamespace(id=pieceId) if pieceId else None
        try:
            return xglassAgent.findSelectionsPiecesAmView(element, piece)
        except XGlassError as error:
            _raise_portal_error(
                error,
                _("Recherche impossible : le portail X'Glass est inaccessible."),
                "Erreur X'Glass lors de la recherche des pièces après-marché",
            )

    @route('/searchBaseEurocode', auth='user', type='json')
    def searchBaseEurocode(self,baseEurocode:str):
        _logger.info(f"searchBaseEurocode {baseEurocode}")
        try:
            discount = get_vsf_discount(request.env)
            vsfArticles = _vsf_call(lambda agent: agent.searchEurocodeArticlesClient(baseEurocode))
            for vsf_article in vsfArticles:
                vsf_article.set_rpbm_discount(discount)
            return [vsfArticle.__dict__ for vsfArticle in vsfArticles]
        except VSFError as error:
            _raise_portal_error(
                error,
                _("Recherche impossible : le portail VSF est inaccessible."),
                "Erreur VSF lors de la recherche eurocode %s" % baseEurocode,
            )

    @route('/doesProductExists', auth='user', type='json')
    def doesProductExists(self, articleVsfInfo=None, productCode=None):
        """Cherche un produit VSF par eurocode, référence interne, puis nom.

        Règles de rattachement : voir ``_find_existing_product``.
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
    def get_vsf_article_details(self, articleVsfInfo=None, enrichSuggestions=True):
        """Retourne les détails de fiche nécessaires au widget, sans écriture Odoo."""
        article_info = articleVsfInfo or {}
        code = str(article_info.get('code') or '').strip()
        if not code:
            raise UserError(_("Lecture impossible : le code VSF de l'article est absent."))
        try:
            discount = get_vsf_discount(request.env)
            details = _vsf_call(lambda agent: agent.getArticleDetails(
                article_info,
                include_suggestions=bool(enrichSuggestions),
                enrich_suggestions=bool(enrichSuggestions),
            ))
            article = _vsf_article_payload(details, discount)
            return article.__dict__
        except VSFError as error:
            _raise_portal_error(
                error,
                _("Lecture impossible : la fiche article VSF est inaccessible."),
                "Erreur VSF lors de la lecture de l'article %s" % code,
            )

    @route('/createProduct', auth='user', type='json')
    def createProduct(self,articleVsfInfo:dict):
        _logger.info(f"createProduct {articleVsfInfo}")
        product_code = str(articleVsfInfo.get('code') or '').strip()
        if not product_code:
            raise UserError(_("Création impossible : le code VSF de l'article est absent."))

        # Sérialise les créations par code : un double-clic ou deux requêtes
        # simultanées ne peuvent pas créer deux produits avec le même code, à
        # condition de chercher l'existant avec un curseur neuf (voir plus bas).
        request.env.cr.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))",
            (f"rpbm_agent.product:{product_code}",),
        )
        try:
            # Seule la lecture est rejouée après une reconnexion : les créations
            # ci-dessous restent hors de _vsf_call pour ne jamais être faites deux fois.
            article_details = _vsf_call(lambda agent: agent.getArticleDetails(
                articleVsfInfo, include_suggestions=False
            ))
            article_vsf = vsf.VSFArticle(
                _rpbm_discount=get_vsf_discount(request.env), **article_details
            )
            constructor_reference = _article_constructor_reference(article_vsf.__dict__)
            # REPEATABLE READ : l'instantané de cette requête précède le verrou consultatif et ne
            # voit pas le produit qu'une requête concurrente a créé avant de le relâcher.
            with request.env.registry.cursor() as fresh_cr:
                existing_product, matched_by = _find_existing_product(
                    request.env(cr=fresh_cr),
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
                except VSFAuthError:
                    raise
                except VSFError:
                    _logger.warning("Image VSF indisponible pour %s ; produit créé sans image", article_vsf.code)

            # sudo : création réservée au widget, les commerciaux n'ont que la lecture sur les articles.
            product = request.env['product.product'].sudo().create(
                vsf.product_creation_values(
                    article_vsf,
                    vsf.product_description(article_vsf),
                    image=image,
                )
            )
            request.env['product.supplierinfo'].sudo().create(
                vsf.product_supplierinfo_values(
                    article_vsf,
                    get_vsf_partner_id(request.env),
                    product_id=product.id,
                    date_start=fields.Date.today(),
                )
            )
        except VSFError as error:
            _raise_portal_error(
                error,
                _("Création impossible pour l'article VSF %s.") % product_code,
                "Erreur VSF lors de la création du produit %s" % product_code,
            )
        except UserError:
            raise
        except Exception as error:
            _logger.exception("Erreur lors de la création du produit VSF %s", product_code)
            raise UserError(_("Création impossible pour l'article VSF %s.") % product_code) from error

        _logger.info("Produit VSF créé %s", product)
        return _product_payload(product, 'créé')


