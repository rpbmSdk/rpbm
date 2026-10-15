"""Barème X'Glass de la pièce d'origine (miroir opportunité -> devis) et prix fournisseur des lignes."""
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestSaleLinePrices(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Client prix"})
        cls.first = cls.env["res.partner"].create({"name": "Fournisseur prioritaire"})
        cls.second = cls.env["res.partner"].create({"name": "Fournisseur second"})
        cls.product = cls.env["product.product"].create({"name": "Vitrage", "detailed_type": "consu", "seller_ids": [
            (0, 0, {"partner_id": cls.second.id, "price": 50.0, "sequence": 2}),
            (0, 0, {"partner_id": cls.first.id, "price": 100.0, "discount": 10.0, "sequence": 1}),
        ]})
        cls.other = cls.env["product.product"].create({"name": "Joint", "detailed_type": "consu", "seller_ids": [
            (0, 0, {"partner_id": cls.second.id, "price": 7.0}),
        ]})
        cls.order = cls.env["sale.order"].create({"partner_id": cls.partner.id})

    def _line(self, product=None, **vals):
        return self.env["sale.order.line"].create({
            "order_id": self.order.id, "product_id": (product or self.product).id, "product_uom_qty": 1, **vals,
        })

    def test_supplier_price_from_first_vendor_by_sequence(self):
        line = self._line()
        self.assertEqual(line.rpbm_supplier_id, self.first, "séquence d'abord, pas le moins cher")
        self.assertAlmostEqual(line.rpbm_supplier_price, 90.0, msg="prix net de remise")
        no_vendor = self._line(self.env["product.product"].create({"name": "Sans fournisseur", "detailed_type": "consu"}))
        self.assertEqual((no_vendor.rpbm_supplier_id.id, no_vendor.rpbm_supplier_price), (False, 0.0))

    def test_expired_vendor_is_ignored(self):
        self.product.seller_ids.filtered(lambda seller: seller.partner_id == self.first).date_end = (
            fields.Date.today() - timedelta(days=2)
        )
        line = self._line()
        self.assertEqual((line.rpbm_supplier_id, line.rpbm_supplier_price), (self.second, 50.0))

    def test_given_value_kept_until_product_changes(self):
        line = self._line(rpbm_supplier_price=211.16, rpbm_supplier_id=self.second.id)
        self.assertEqual((line.rpbm_supplier_id, line.rpbm_supplier_price), (self.second, 211.16))
        line.rpbm_supplier_price = 205.0
        line.product_uom_qty = 3
        self.assertEqual(line.rpbm_supplier_price, 205.0, "la quantité ne recalcule pas")
        line.product_id = self.other
        self.assertEqual((line.rpbm_supplier_id, line.rpbm_supplier_price), (self.second, 7.0))

    def test_piece_price_mirrors_the_opportunity(self):
        lead = self.env["crm.lead"].create({"name": "Barème", "partner_id": self.partner.id, "rpbm_xglass_piece_price": 322.38})
        order = self.env["sale.order"].create({"partner_id": self.partner.id, "opportunity_id": lead.id})
        self.assertEqual(order.rpbm_xglass_piece_price, 322.38)
        order.rpbm_xglass_piece_price = 300.0
        self.assertEqual(lead.rpbm_xglass_piece_price, 300.0)
