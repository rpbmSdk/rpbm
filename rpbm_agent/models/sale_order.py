import logging
import re
import unicodedata

from odoo import _, api, models
from odoo.exceptions import AccessError, UserError


_logger = logging.getLogger(__name__)

HISTORICAL_LOCATION_TO_CARRIER = {
    "galleria": "Retrait / pose Galleria",
    "genipa": "Retrait / pose Genipa",
    "domicile": "Pose sur site (Camion)",
}
UNMAPPED_HISTORICAL_LOCATIONS = {
    "lavage place d'armes",
    "lavage marin",
}


def normalize_historical_location(value):
    """Normalise les libellés CRM sans rendre les valeurs métier permissives."""
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(
        character for character in text if not unicodedata.combining(character)
    )
    return re.sub(r"\s+", " ", text).strip().casefold()


def carrier_name_for_historical_location(value):
    """Retourne le nom canonique du transporteur, ou None si aucun mapping n'existe."""
    return HISTORICAL_LOCATION_TO_CARRIER.get(normalize_historical_location(value))


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _rpbm_historical_location(self, opportunity):
        field_name = "x_studio_lieu_intervention"
        if field_name not in opportunity._fields:
            return False, _(
                "Le champ historique du lieu d'intervention est absent de l'opportunité."
            )

        try:
            value = getattr(opportunity, field_name, False)
        except AccessError:
            return False, _(
                "Le lieu d'intervention historique n'est pas accessible à cet utilisateur."
            )
        normalized = normalize_historical_location(value)
        if not normalized:
            return False, _(
                "Le lieu d'intervention historique est vide ; choisissez le mode de remise."
            )
        if normalized in UNMAPPED_HISTORICAL_LOCATIONS:
            return False, _(
                "Le lieu d'intervention historique « %s » n'a pas de transporteur automatique ; "
                "choisissez le mode de remise."
            ) % value

        carrier_name = carrier_name_for_historical_location(value)
        if not carrier_name:
            return False, _(
                "Le lieu d'intervention historique « %s » n'est pas reconnu ; "
                "choisissez le mode de remise."
            ) % value
        return carrier_name, False

    @api.model
    def _rpbm_find_carrier_for_opportunity(self, opportunity, company_id=None):
        carrier_name, warning = self._rpbm_historical_location(opportunity)
        if warning:
            return self.env["delivery.carrier"], warning
        if not carrier_name:
            return self.env["delivery.carrier"], False

        company_id = company_id or self.env.company.id
        carrier_model = self.env["delivery.carrier"]
        try:
            candidates = carrier_model.search(
                [
                    ("active", "=", True),
                    ("name", "ilike", carrier_name),
                    "|",
                    ("company_id", "=", False),
                    ("company_id", "=", company_id),
                ]
            ).filtered(
                lambda carrier: normalize_historical_location(carrier.name)
                == normalize_historical_location(carrier_name)
            )
        except AccessError:
            return carrier_model, _(
                "Le mode de remise « %s » n'est pas accessible à cet utilisateur."
            ) % carrier_name

        if not candidates:
            return carrier_model, _(
                "Le transporteur « %s » est introuvable ; choisissez manuellement "
                "le mode de remise."
            ) % carrier_name
        if len(candidates) > 1:
            return carrier_model, _(
                "Plusieurs transporteurs « %s » sont compatibles ; le choix doit "
                "être fait manuellement."
            ) % carrier_name
        return candidates, False

    @api.model_create_multi
    def create(self, vals_list):
        prepared_vals_list = []
        for original_vals in vals_list:
            vals = dict(original_vals)
            if not vals.get("carrier_id") and vals.get("opportunity_id"):
                try:
                    opportunity = (
                        self.env["crm.lead"].browse(vals["opportunity_id"]).exists()
                    )
                except AccessError:
                    _logger.warning(
                        "Préremplissage carrier_id impossible : opportunité inaccessible (%s)",
                        vals["opportunity_id"],
                    )
                    opportunity = self.env["crm.lead"]
                if opportunity:
                    carrier, warning = self._rpbm_find_carrier_for_opportunity(
                        opportunity, vals.get("company_id")
                    )
                    if carrier:
                        vals["carrier_id"] = carrier.id
                    if warning:
                        _logger.warning(
                            "Préremplissage carrier_id ignoré pour l'opportunité #%s : %s",
                            opportunity.id,
                            warning,
                        )
                else:
                    _logger.warning(
                        "Préremplissage carrier_id impossible : opportunité #%s "
                        "introuvable ou inaccessible",
                        vals["opportunity_id"],
                    )
            prepared_vals_list.append(vals)
        return super().create(prepared_vals_list)

    @api.onchange("opportunity_id")
    def _onchange_rpbm_opportunity_carrier(self):
        """Préremplit uniquement un nouveau brouillon vide, jamais un devis existant."""
        if len(self) != 1 or self._origin or self.carrier_id or self.order_line:
            return
        if not self.opportunity_id:
            return

        carrier, warning = self._rpbm_find_carrier_for_opportunity(
            self.opportunity_id, self.company_id.id
        )
        if carrier:
            self.carrier_id = carrier
        if warning:
            return {
                "warning": {
                    "title": _("Mode de remise"),
                    "message": warning,
                }
            }

    def action_confirm(self):
        orders_to_confirm = self.filtered(lambda order: order.state in ("draft", "sent"))
        missing_carrier = orders_to_confirm.filtered(lambda order: not order.carrier_id)
        if missing_carrier:
            raise UserError(
                _(
                    "Sélectionnez un transporteur / mode de remise avant de confirmer : %s",
                    ", ".join(missing_carrier.mapped("display_name")),
                )
            )
        return super().action_confirm()
