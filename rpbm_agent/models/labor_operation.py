from odoo import fields, models


class SaleOrderLine(models.Model):
    """Provenance stable des lignes de main-d'oeuvre creees par le widget."""

    _inherit = "sale.order.line"

    x_rpbm_labor_operation_key = fields.Char(
        string="Clé opération main-d'œuvre X'Glass",
        copy=False,
        index=True,
    )
