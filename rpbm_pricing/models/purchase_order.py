from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # Posé à la main par l'acheteur ; un brouillon bateau est exclu du regroupement automatique (stock_rule.py).
    rpbm_transport_mode = fields.Selection(
        [("plane", "Avion"), ("boat", "Bateau")], "Mode", default="plane", required=True, tracking=True)
