from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    rpbm_vehicle_id = fields.Many2one(related="sale_id.rpbm_vehicle_id", store=True, index=True)
