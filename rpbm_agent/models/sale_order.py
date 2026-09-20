import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

from .legacy_fields import INTERVENTION_LOCATIONS, normalize

_logger = logging.getLogger(__name__)

# Lieu d'intervention de l'opportunité -> transporteur (« mode de remise ») du devis.
LOCATION_TO_CARRIER = {
    "galleria": "Retrait / pose Galleria",
    "genipa": "Retrait / pose Genipa",
    "domicile": "Pose sur site (Camion)",
}


def carrier_name_for_location(location):
    """Nom canonique du transporteur pour un lieu d'intervention, ou None."""
    return LOCATION_TO_CARRIER.get(location)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Miroirs de l'opportunité, écrivables depuis le devis (la valeur remonte à l'opportunité).
    # Stockés seulement pour la recherche et le regroupement.
    rpbm_vehicle_id = fields.Many2one(related="opportunity_id.rpbm_vehicle_id", store=True, readonly=False, index=True)
    rpbm_vehicle_brand_id = fields.Many2one(related="opportunity_id.rpbm_vehicle_brand_id", store=True, readonly=False, index=True)
    rpbm_vehicle_model_id = fields.Many2one(related="opportunity_id.rpbm_vehicle_model_id", store=True, readonly=False, index=True)
    rpbm_license_plate = fields.Char(related="opportunity_id.rpbm_license_plate", store=True, readonly=False)
    rpbm_vin = fields.Char(related="opportunity_id.rpbm_vin", readonly=False)
    rpbm_fuel_type = fields.Selection(related="opportunity_id.rpbm_fuel_type", readonly=False)
    rpbm_vehicle_detail_model = fields.Char(related="opportunity_id.rpbm_vehicle_detail_model", readonly=False)
    rpbm_first_registration_date = fields.Date(related="opportunity_id.rpbm_first_registration_date", readonly=False)
    rpbm_xglass_category = fields.Char(related="opportunity_id.rpbm_xglass_category", readonly=False)
    rpbm_part_type = fields.Selection(related="opportunity_id.rpbm_part_type", readonly=False)
    rpbm_eurocode_base = fields.Char(related="opportunity_id.rpbm_eurocode_base", readonly=False)
    rpbm_eurocode = fields.Char(related="opportunity_id.rpbm_eurocode", readonly=False)
    rpbm_vsf_designation = fields.Char(related="opportunity_id.rpbm_vsf_designation", readonly=False)
    rpbm_vsf_stock = fields.Integer(related="opportunity_id.rpbm_vsf_stock", readonly=False)
    rpbm_constructor_reference = fields.Char(related="opportunity_id.rpbm_constructor_reference", readonly=False)
    rpbm_intervention_location = fields.Selection(related="opportunity_id.rpbm_intervention_location", readonly=False)
    rpbm_xglass_piece_id = fields.Char(related="opportunity_id.rpbm_xglass_piece_id", readonly=False)
    rpbm_piece_oe_id = fields.Char(related="opportunity_id.rpbm_piece_oe_id", readonly=False)
    rpbm_piece_am_id = fields.Char(related="opportunity_id.rpbm_piece_am_id", readonly=False)

    @api.model
    def _rpbm_carrier_name(self, opportunity):
        location = opportunity.rpbm_intervention_location
        if not location:
            return False, _("Le lieu d'intervention de l'opportunité est vide ; choisissez le mode de remise.")
        carrier_name = carrier_name_for_location(location)
        if not carrier_name:
            label = dict(INTERVENTION_LOCATIONS).get(location, location)
            return False, _(
                "Le lieu d'intervention « %s » n'a pas de transporteur automatique ; "
                "choisissez le mode de remise."
            ) % label
        return carrier_name, False

    @api.model
    def _rpbm_find_carrier_for_opportunity(self, opportunity, company_id=None):
        carrier_name, warning = self._rpbm_carrier_name(opportunity)
        carrier_model = self.env["delivery.carrier"]
        if warning:
            return carrier_model, warning

        company_id = company_id or self.env.company.id
        try:
            candidates = carrier_model.search([
                ("active", "=", True),
                ("name", "ilike", carrier_name),
                "|", ("company_id", "=", False), ("company_id", "=", company_id),
            ]).filtered(lambda carrier: normalize(carrier.name) == normalize(carrier_name))
        except AccessError:
            return carrier_model, _("Le mode de remise « %s » n'est pas accessible à cet utilisateur.") % carrier_name

        if not candidates:
            return carrier_model, _(
                "Le transporteur « %s » est introuvable ; choisissez manuellement le mode de remise."
            ) % carrier_name
        if len(candidates) > 1:
            return carrier_model, _(
                "Plusieurs transporteurs « %s » sont compatibles ; le choix doit être fait manuellement."
            ) % carrier_name
        return candidates, False

    @api.model_create_multi
    def create(self, vals_list):
        prepared_vals_list = []
        for original_vals in vals_list:
            vals = dict(original_vals)
            if not vals.get("carrier_id") and vals.get("opportunity_id"):
                try:
                    opportunity = self.env["crm.lead"].browse(vals["opportunity_id"]).exists()
                except AccessError:
                    _logger.warning(
                        "Préremplissage carrier_id impossible : opportunité inaccessible (%s)",
                        vals["opportunity_id"],
                    )
                    opportunity = self.env["crm.lead"]
                if opportunity:
                    carrier, warning = self._rpbm_find_carrier_for_opportunity(opportunity, vals.get("company_id"))
                    if carrier:
                        vals["carrier_id"] = carrier.id
                    if warning:
                        _logger.warning(
                            "Préremplissage carrier_id ignoré pour l'opportunité #%s : %s", opportunity.id, warning,
                        )
                else:
                    _logger.warning(
                        "Préremplissage carrier_id impossible : opportunité #%s introuvable ou inaccessible",
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

        carrier, warning = self._rpbm_find_carrier_for_opportunity(self.opportunity_id, self.company_id.id)
        if carrier:
            self.carrier_id = carrier
        if warning:
            return {"warning": {"title": _("Mode de remise"), "message": warning}}

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


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = ["sale.order.line", "rpbm.legacy.sync.mixin"]

    # Prix RPBM de l'article VSF ; l'automatisation Studio « Tarif x glass » en dérive price_unit.
    rpbm_xglass_price = fields.Float("Prix X'Glass", digits="Product Price")
    # Provenance stable des lignes de main-d'œuvre créées par le widget.
    rpbm_labor_operation_key = fields.Char("Clé opération main-d'œuvre X'Glass", copy=False, index=True)
