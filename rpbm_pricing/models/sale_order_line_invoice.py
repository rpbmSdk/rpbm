from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        """Recopie le barème X'Glass sur la ligne de facture (lignes produit seulement)."""
        values = super()._prepare_invoice_line(**optional_values)
        if not self.display_type:
            values["rpbm_xglass_price"] = self.rpbm_xglass_price
        return values
