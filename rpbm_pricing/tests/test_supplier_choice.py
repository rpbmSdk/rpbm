from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import RpbmPricingCase


@tagged("post_install", "-at_install")
class TestSupplierChoice(RpbmPricingCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Routes de test, pas celles des transporteurs (propres à la base) : la chaîne réelle passe en recette.
        mto = cls.env.ref("stock.route_warehouse0_mto")
        mto.active = True
        buy = cls.env.ref("purchase_stock.route_warehouse0_buy")
        # Le client est aussi fournisseur de l'article, mais après VSF dans la séquence.
        cls.product = cls.env["product.product"].create({
            "name": "Article choix fournisseur RPBM Pricing test",
            "detailed_type": "product",
            "route_ids": [Command.set([mto.id, buy.id])],
            "seller_ids": [
                Command.create({"partner_id": cls.vsf_partner.id, "price": 100, "sequence": 1}),
                Command.create({"partner_id": cls.customer.id, "price": 50, "sequence": 10}),
            ],
        })

    def _purchase_lines(self):
        return self.env["purchase.order.line"].search([("product_id", "=", self.product.id)])

    def _vsf_draft(self, order, mode):
        """Brouillon VSF qui satisfait le domaine natif de regroupement (stock_rule.py:312-319)."""
        rule = order.warehouse_id.buy_pull_id
        return self.env["purchase.order"].create({
            "partner_id": self.vsf_partner.id,
            "user_id": False,  # partner.buyer_id est vide ; le défaut serait l'utilisateur courant
            "picking_type_id": rule.picking_type_id.id,
            "company_id": order.company_id.id,
            "currency_id": self.product.seller_ids[:1].currency_id.id,
            "rpbm_transport_mode": mode,
        })

    def test_customer_is_never_the_vendor(self):
        self._confirmable_order(self.customer, [self.product]).action_confirm()
        purchase = self._purchase_lines().order_id
        self.assertEqual(purchase.partner_id, self.vsf_partner)
        self.assertEqual(purchase.rpbm_transport_mode, "plane")

    def test_boat_draft_is_not_merged(self):
        order = self._confirmable_order(self.customer, [self.product])
        boat = self._vsf_draft(order, "boat")
        order.action_confirm()
        purchase = self._purchase_lines().order_id
        self.assertEqual(len(purchase), 1)
        self.assertNotEqual(purchase, boat)
        self.assertEqual(purchase.partner_id, self.vsf_partner)
        self.assertFalse(boat.order_line)

    def test_plane_draft_is_merged(self):
        order = self._confirmable_order(self.customer, [self.product])
        plane = self._vsf_draft(order, "plane")
        order.action_confirm()
        self.assertEqual(self._purchase_lines().order_id, plane)

    def test_confirmation_without_carrier_still_refused(self):
        order = self._confirmable_order(self.customer, [self.product], carrier_id=False)
        with self.assertRaises(UserError):
            order.action_confirm()
        self.assertFalse(self._purchase_lines())
