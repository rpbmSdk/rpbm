"""Base des TransactionCase du module, écrits pour tourner sur la base de préprod."""
from odoo import Command
from odoo.tests.common import TransactionCase

from odoo.addons.rpbm_agent.controllers.vsf_config import VSF_PARTNER_PARAM


class RpbmPricingCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # rpbm_agent refuse de confirmer un devis sans transporteur (sale_order.py, action_confirm).
        cls.carrier_product = cls.env["product.product"].create(
            {"name": "Service transporteur RPBM Pricing test", "detailed_type": "service"})
        cls.carrier = cls.env["delivery.carrier"].create({
            "name": "Transporteur RPBM Pricing test",
            "product_id": cls.carrier_product.id,
            "delivery_type": "fixed",
        })
        # get_vsf_partner_id lit ce paramètre : les tests ne dépendent pas du VSF réel (5708).
        cls.vsf_partner = cls.env["res.partner"].create({"name": "VSF RPBM Pricing test", "is_company": True})
        cls.env["ir.config_parameter"].sudo().set_param(VSF_PARTNER_PARAM, str(cls.vsf_partner.id))
        cls.customer = cls.env["res.partner"].create({"name": "Client RPBM Pricing test"})

    def _confirmable_order(self, partner, lines, **values):
        """Devis brouillon avec transporteur ; ``lines`` : valeurs de ligne ou articles (quantité 1)."""
        line_vals = [line if isinstance(line, dict) else {"product_id": line.id} for line in lines]
        return self.env["sale.order"].create({
            "partner_id": partner.id,
            "carrier_id": self.carrier.id,
            "order_line": [Command.create(vals) for vals in line_vals],
            **values,
        })
