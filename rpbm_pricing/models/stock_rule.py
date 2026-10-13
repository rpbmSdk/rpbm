from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_partner_id(self, values, rule):
        # P-36 : le client livré (group_id.partner_id) n'est jamais retenu comme fournisseur ;
        # _select_seller prend alors le premier prix fournisseur valable par séquence.
        return values.get("supplierinfo_name") or self.env["res.partner"]

    def _make_po_get_domain(self, company_id, values, partner):
        # P-47 : une demande de prix bateau en brouillon ne reçoit pas les besoins automatiques.
        return super()._make_po_get_domain(company_id, values, partner) + (("rpbm_transport_mode", "!=", "boat"),)
