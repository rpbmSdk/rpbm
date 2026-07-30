import logging
from datetime import timedelta

from odoo import _, fields, models, tools
from odoo.exceptions import UserError

from ..controllers import vsf


_logger = logging.getLogger(__name__)

VSF_PARTNER_PARAM = "rpbm_agent.vsf_partner_id"
VSF_DISCOUNT_PARAM = "rpbm_agent.vsf_discount"
DEFAULT_VSF_PARTNER_ID = 5708


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _vsf_sync_configuration(self):
        """Lit et valide les paramètres nécessaires à une synchronisation VSF."""
        params = self.env["ir.config_parameter"].sudo()
        login = params.get_param("VSF_LOGIN")
        password = params.get_param("VSF_PASSWORD")
        if not login or not password:
            raise UserError(_("Les identifiants VSF ne sont pas configurés."))

        try:
            discount = float(
                params.get_param(VSF_DISCOUNT_PARAM, str(vsf.DEFAULT_RPBM_DISCOUNT))
            )
        except (TypeError, ValueError) as error:
            raise UserError(
                _("Le paramètre %s doit être un nombre compris entre 0 et 1.")
                % VSF_DISCOUNT_PARAM
            ) from error
        if not 0 <= discount <= 1:
            raise UserError(
                _("Le paramètre %s doit être compris entre 0 et 1.")
                % VSF_DISCOUNT_PARAM
            )

        try:
            partner_id = int(
                params.get_param(VSF_PARTNER_PARAM, str(DEFAULT_VSF_PARTNER_ID))
            )
        except (TypeError, ValueError) as error:
            raise UserError(
                _("Le paramètre %s doit contenir l'identifiant numérique d'un partenaire.")
                % VSF_PARTNER_PARAM
            ) from error
        if not self.env["res.partner"].browse(partner_id).exists():
            raise UserError(_("Le fournisseur VSF configuré (%s) n'existe pas.") % partner_id)
        return login, password, discount, partner_id

    def _active_vsf_supplierinfo(self, partner_id, today):
        """Retourne l'unique tarif VSF valable aujourd'hui pour ce modèle."""
        active_lines = self.seller_ids.filtered(
            lambda line: line.partner_id.id == partner_id
            and (not line.date_start or line.date_start <= today)
            and (not line.date_end or line.date_end >= today)
        )
        if len(active_lines) > 1:
            raise UserError(
                _("Plusieurs prix fournisseur VSF sont actifs pour ce produit ; "
                  "la synchronisation ne peut pas choisir lequel historiser.")
            )
        return active_lines

    def _sync_vsf_supplierinfo(self, article, partner_id, today=None):
        """Crée ou historise le prix fournisseur VSF de manière déterministe."""
        self.ensure_one()
        today = today or fields.Date.context_today(self)
        active_line = self._active_vsf_supplierinfo(partner_id, today)
        if not active_line:
            self.env["product.supplierinfo"].create(
                vsf.product_supplierinfo_values(
                    article, partner_id, product_tmpl_id=self.id, date_start=today
                )
            )
            return

        line = active_line
        same_price = tools.float_compare(
            line.price, article.prixVenteRPBM, precision_digits=2
        ) == 0
        labels = {"product_name": article.name, "product_code": article.code}
        if same_price:
            line.write(labels)
            return

        if line.date_start == today:
            line.write(
                {
                    **labels,
                    "delay": 1,
                    "min_qty": 0,
                    "price": article.prixVenteRPBM,
                }
            )
            return

        line.write({"date_end": today - timedelta(days=1)})
        self.env["product.supplierinfo"].create(
            vsf.product_supplierinfo_values(
                article, partner_id, product_tmpl_id=self.id, date_start=today
            )
        )

    def _sync_vsf_information(self, agent, discount, partner_id):
        """Synchronise un modèle à partir de sa fiche VSF, sans ses médias."""
        self.ensure_one()
        code = (self.x_studio_eurocode or "").strip()
        if not code:
            raise UserError(_("Synchronisation impossible : l'eurocode VSF est absent."))

        details = agent.getArticleDetails({"code": code}, include_suggestions=False)
        article = vsf.VSFArticle(_rpbm_discount=discount, **details)
        if article.prixVente is None or article.prixVenteRPBM is None:
            raise UserError(_("Synchronisation impossible : le prix de l'article VSF est absent."))

        self.write(vsf.product_sync_values(article, vsf.product_description(article)))
        self._sync_vsf_supplierinfo(article, partner_id)

    def sync_vsf_information(self):
        """Synchronise plusieurs modèles et isole les erreurs par enregistrement."""
        report = {"updated_ids": [], "errors": []}
        if not self:
            return report

        login, password, discount, partner_id = self._vsf_sync_configuration()
        agent = vsf.VSFAgent()
        try:
            agent.auth(login, password)
        except vsf.VSFError as error:
            _logger.exception("Échec de connexion VSF pour la synchronisation produit")
            raise UserError(
                _("Connexion au portail VSF impossible. Vérifiez les identifiants configurés.")
            ) from error

        for product_tmpl in self:
            try:
                with self.env.cr.savepoint():
                    product_tmpl._sync_vsf_information(agent, discount, partner_id)
            except (UserError, vsf.VSFError) as error:
                _logger.warning(
                    "Synchronisation VSF ignorée pour product.template #%s : %s",
                    product_tmpl.id,
                    error,
                )
                report["errors"].append(
                    {"id": product_tmpl.id, "name": product_tmpl.display_name, "message": str(error)}
                )
            except Exception:
                _logger.exception(
                    "Erreur inattendue lors de la synchronisation VSF de product.template #%s",
                    product_tmpl.id,
                )
                report["errors"].append(
                    {
                        "id": product_tmpl.id,
                        "name": product_tmpl.display_name,
                        "message": _("Erreur inattendue lors de la synchronisation VSF."),
                    }
                )
            else:
                report["updated_ids"].append(product_tmpl.id)
        return report

    def action_sync_vsf_information(self):
        """Point d'entrée du bouton de formulaire, masqué avant ouverture métier."""
        report = self.sync_vsf_information()
        errors = report["errors"]
        message = _("%s produit(s) synchronisé(s).") % len(report["updated_ids"])
        if errors:
            message += " " + _("%s erreur(s) à consulter dans les journaux.") % len(errors)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Synchronisation VSF"),
                "message": message,
                "type": "warning" if errors else "success",
                "sticky": bool(errors),
            },
        }
