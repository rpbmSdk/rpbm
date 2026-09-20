from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    rpbm_vehicle_id = fields.Many2one(
        "fleet.vehicle", string="Véhicule", compute="_compute_rpbm_vehicle_id",
        store=True, readonly=False, index=True,
    )
    rpbm_license_plate = fields.Char(related="rpbm_vehicle_id.license_plate", string="Immatriculation")

    @api.depends("invoice_line_ids.sale_line_ids.order_id.rpbm_vehicle_id")
    def _compute_rpbm_vehicle_id(self):
        for move in self:
            vehicles = move.invoice_line_ids.sale_line_ids.order_id.rpbm_vehicle_id
            move.rpbm_vehicle_id = vehicles[:1] or move.rpbm_vehicle_id
