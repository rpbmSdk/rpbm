from odoo import api, fields, models

from ..lib import regime
from .legacy_fields import lead_has_insurer


class SaleOrder(models.Model):
    _inherit = "sale.order"

    rpbm_regime = fields.Selection(regime.SELECTION, "Régime du dossier", compute="_compute_rpbm_regime")
    rpbm_pricing_warning = fields.Text("Avertissement tarifaire", compute="_compute_rpbm_pricing_warning")

    def _rpbm_dossier_regime(self):
        """``None`` sans opportunité, ``insurance`` si elle porte un assureur, sinon ``private``."""
        self.ensure_one()
        # En superutilisateur, comme les champs related de rpbm_agent : lire le devis suffit.
        lead = self.opportunity_id.sudo()
        return regime.dossier_regime(bool(lead), lead_has_insurer(lead))

    @api.depends("opportunity_id")
    def _compute_rpbm_regime(self):
        for order in self:
            order.rpbm_regime = order._rpbm_dossier_regime() or False

    @api.depends("sale_order_template_id.rpbm_regime", "opportunity_id", "order_line.rpbm_labor_operation_key")
    def _compute_rpbm_pricing_warning(self):
        for order in self:
            messages = regime.warnings(
                order.sale_order_template_id.rpbm_regime or None,
                order._rpbm_dossier_regime(),
                any(order.order_line.mapped("rpbm_labor_operation_key")),
            )
            order.rpbm_pricing_warning = "\n".join(messages) or False
