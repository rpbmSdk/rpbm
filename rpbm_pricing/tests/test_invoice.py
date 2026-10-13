from odoo import Command
from odoo.tests import tagged

from .common import RpbmPricingCase


@tagged("post_install", "-at_install")
class TestInvoice(RpbmPricingCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Prix fournisseur net 139,91 avec remise : ni l'un ni l'autre ne doit sortir sur la facture (P-24).
        cls.product = cls.env["product.product"].create({
            "name": "Pare-brise facture RPBM Pricing test",
            "detailed_type": "consu",
            "invoice_policy": "order",
            "list_price": 1000,
            "seller_ids": [Command.create({"partner_id": cls.vsf_partner.id, "price": 139.91, "discount": 20})],
        })

    def _invoice(self):
        order = self._confirmable_order(self.customer, [
            {"display_type": "line_section", "name": "Section RPBM Pricing test", "rpbm_xglass_price": 500},
            {"product_id": self.product.id, "rpbm_xglass_price": 500},
        ])
        order.action_confirm()
        return order._create_invoices()

    def test_xglass_price_copied_to_invoice_line(self):
        lines = self._invoice().invoice_line_ids
        product_line = lines.filtered(lambda line: line.product_id == self.product)
        self.assertEqual(product_line.rpbm_xglass_price, 500)
        self.assertFalse(lines.filtered(lambda line: line.display_type == "line_section").rpbm_xglass_price)

    def test_invoice_report_hides_supplier_net_and_discount(self):
        invoice = self._invoice()
        html, _report_type = self.env["ir.actions.report"]._render_qweb_html("account.account_invoices", invoice.ids)
        html = html.decode().casefold()
        for text in ("139,91", "139.91", "remise fournisseur"):
            self.assertNotIn(text, html)
