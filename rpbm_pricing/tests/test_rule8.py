from odoo.tests import tagged

from ..models.legacy_fields import RULE8_GUARD_VALUE, RULE8_ORIGINAL_VALUE
from ..models.sale_order_line_rule8 import RULE8_ORIGINAL_PARAM
from .common import RpbmPricingCase


@tagged("post_install", "-at_install")
class TestRule8(RpbmPricingCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Line = cls.env["sale.order.line"]
        cls.ICP = cls.env["ir.config_parameter"].sudo()
        cls.categ = cls.env["product.category"].create({"name": "Pièces RPBM Pricing test"})
        cls.part = cls.env["product.product"].create({
            "name": "Pièce règle 8 RPBM Pricing", "detailed_type": "consu", "categ_id": cls.categ.id,
            "list_price": 100, "invoice_policy": "order"})
        cls.service = cls.env["product.product"].create({
            "name": "Service règle 8 RPBM Pricing", "detailed_type": "service", "list_price": 80})

    def setUp(self):
        super().setUp()
        # Valeurs par défaut, quel que soit le paramétrage de la base.
        self.ICP.set_param("rpbm_pricing.insurance_coefficient", "1.5")
        self.ICP.set_param("rpbm_pricing.price_rounding", "0")
        self.ICP.set_param("rpbm_pricing.rule8_insurance_only", "0")

    def _line(self, product, price=341.87, **values):
        order = self._confirmable_order(
            self.customer, [{"product_id": product.id, "rpbm_xglass_price": price}],
            sale_order_template_id=False, **values)
        return order.order_line.filtered(lambda line: line.product_id == product)

    def _action(self, value=RULE8_ORIGINAL_VALUE):
        return self.env["ir.actions.server"].create({
            "name": "Règle 8 RPBM Pricing test",
            "model_id": self.env.ref("sale.model_sale_order_line").id,
            "state": "object_write",
            "update_path": "price_unit",
            "evaluation_type": "equation",
            "value": value,
        })

    # Mise en place sur une action de test

    def test_install_and_uninstall(self):
        action = self._action()
        self.assertTrue(self.Line._rpbm_rule8_install(action))
        self.assertEqual(action.value, RULE8_GUARD_VALUE)
        self.assertEqual(self.ICP.get_param(RULE8_ORIGINAL_PARAM), RULE8_ORIGINAL_VALUE)
        self.assertTrue(self.Line._rpbm_rule8_install(action))
        self.assertEqual(action.value, RULE8_GUARD_VALUE)
        self.assertTrue(self.Line._rpbm_rule8_uninstall(action))
        self.assertEqual(action.value, RULE8_ORIGINAL_VALUE)
        self.assertFalse(self.Line._rpbm_rule8_uninstall(action))

    def test_install_keeps_spaced_original(self):
        spaced = RULE8_ORIGINAL_VALUE.replace("*", " * ")
        action = self._action(spaced)
        self.assertTrue(self.Line._rpbm_rule8_install(action))
        self.assertEqual(action.value, RULE8_GUARD_VALUE)
        self.Line._rpbm_rule8_uninstall(action)
        self.assertEqual(action.value, spaced)

    def test_install_never_overwrites_unexpected_value(self):
        unexpected = RULE8_ORIGINAL_VALUE.replace("1.5", "1.6")
        action = self._action(unexpected)
        self.assertFalse(self.Line._rpbm_rule8_install(action))
        self.assertEqual(action.value, unexpected)

    # Prix de la règle 8

    def test_rule8_price(self):
        self.assertAlmostEqual(self._line(self.part).rpbm_rule8_price, 512.805, places=4)
        self.assertAlmostEqual(self._line(self.part, 500).rpbm_rule8_price, 750.0, places=4)
        self.ICP.set_param("rpbm_pricing.price_rounding", "0.01")
        self.assertAlmostEqual(self._line(self.part).rpbm_rule8_price, 512.81, places=4)

    def test_service_is_not_raised(self):
        line = self._line(self.service, 500)
        self.assertIsNone(line._rpbm_rule8_value())
        # L'action gardée réécrit alors le prix tel quel, quel que soit l'état de l'automatisation de la base.
        self.assertAlmostEqual(line.rpbm_rule8_price, line.price_unit, places=4)

    def test_excluded_category_is_not_raised(self):
        consumables = self.env.ref("__import__.rpbm_categ_consommable", raise_if_not_found=False)
        if not consumables:
            self.skipTest("catégorie 19 « Consommable » absente")
        child = self.env["product.category"].create({"name": "Kits RPBM Pricing test", "parent_id": consumables.id})
        kit = self.env["product.product"].create({
            "name": "Kit règle 8 RPBM Pricing", "detailed_type": "consu", "categ_id": child.id, "list_price": 30})
        line = self._line(kit, 500)
        self.assertIsNone(line._rpbm_rule8_value())
        self.assertAlmostEqual(line.rpbm_rule8_price, line.price_unit, places=4)

    def test_insurance_only_filter(self):
        self.ICP.set_param("rpbm_pricing.rule8_insurance_only", "1")
        lead = self.env["crm.lead"].create({
            "name": "Dossier règle 8 RPBM Pricing", "type": "opportunity", "partner_id": self.customer.id})
        private = self._line(self.part, opportunity_id=lead.id)
        self.assertEqual(private.order_id.rpbm_regime, "private")
        self.assertIsNone(private._rpbm_rule8_value())
        self.assertAlmostEqual(private.rpbm_rule8_price, private.price_unit, places=4)
        self.assertAlmostEqual(self._line(self.part).rpbm_rule8_price, 512.805, places=4)

    # De bout en bout, sur l'automatisation réelle de la base

    def _require_real_guard(self):
        if not self.Line._rpbm_rule8_automation():
            self.skipTest("automatisation de la règle 8 absente")
        self.Line._rpbm_rule8_install()
        if not self.Line._rpbm_rule8_guard_active():
            self.skipTest("automatisation inactive ou action à une valeur inattendue")

    def test_end_to_end_quantity_and_scale(self):
        self._require_real_guard()
        line = self._line(self.part)
        self.assertAlmostEqual(line.price_unit, 512.805, places=4)
        line.product_uom_qty = 2
        self.assertAlmostEqual(line.price_unit, 512.805, places=4)
        # Ni l'automatisation (domaine barème non nul) ni la surcharge (barème nul) ne repassent.
        line.rpbm_xglass_price = 0
        self.assertAlmostEqual(line.price_unit, 512.805, places=4)

    def test_end_to_end_invoiced_line_is_kept(self):
        self._require_real_guard()
        line = self._line(self.part)
        order = line.order_id
        order.action_confirm()
        order._create_invoices()
        self.assertGreater(line.qty_invoiced, 0)
        if order.locked:
            order.action_unlock()
        line.price_unit = 600
        line.product_uom_qty = 3
        self.assertEqual(line.price_unit, 600)
