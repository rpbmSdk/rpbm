from odoo import api, fields, models

from .legacy_fields import PART_TYPES

# Repris du premier devis facturé ; gardent leur valeur si le devis n'est plus lié.
ORDER_DERIVED_FIELDS = (
    "rpbm_license_plate",
    "rpbm_vehicle_brand_id",
    "rpbm_vehicle_model_id",
    "rpbm_eurocode",
    "rpbm_part_type",
)


class AccountMove(models.Model):
    _inherit = "account.move"

    rpbm_vehicle_id = fields.Many2one(
        "fleet.vehicle", string="Véhicule", compute="_compute_rpbm_vehicle_id",
        store=True, readonly=False, index=True,
    )
    # Lecture seule, comme les anciens related Studio de la facture.
    rpbm_license_plate = fields.Char("Immatriculation", compute="_compute_rpbm_order_fields", store=True)
    rpbm_vehicle_brand_id = fields.Many2one(
        "fleet.vehicle.model.brand", string="Marque du véhicule",
        compute="_compute_rpbm_order_fields", store=True, index=True,
    )
    rpbm_vehicle_model_id = fields.Many2one(
        "fleet.vehicle.model", string="Modèle du véhicule",
        compute="_compute_rpbm_order_fields", store=True, index=True,
    )
    rpbm_eurocode = fields.Char("Eurocode", compute="_compute_rpbm_order_fields", store=True)
    rpbm_part_type = fields.Selection(
        PART_TYPES, string="Pièce concernée", compute="_compute_rpbm_order_fields", store=True,
    )

    @api.depends("invoice_line_ids.sale_line_ids.order_id.rpbm_vehicle_id")
    def _compute_rpbm_vehicle_id(self):
        for move in self:
            vehicles = move.invoice_line_ids.sale_line_ids.order_id.rpbm_vehicle_id
            move.rpbm_vehicle_id = vehicles[:1] or move.rpbm_vehicle_id

    # Les related non stockés du devis (eurocode, pièce) propagent les déclencheurs jusqu'à l'opportunité.
    @api.depends(*(f"invoice_line_ids.sale_line_ids.order_id.{name}" for name in ORDER_DERIVED_FIELDS))
    def _compute_rpbm_order_fields(self):
        for move in self:
            order = move.invoice_line_ids.sale_line_ids.order_id[:1]
            for name in ORDER_DERIVED_FIELDS:
                # _origin : en onchange, le champ protégé de l'enregistrement virtuel vaudrait False.
                move[name] = order[name] or move._origin[name]
