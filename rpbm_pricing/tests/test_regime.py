from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..models.legacy_fields import INSURER_FIELD


@tagged("post_install", "-at_install")
class TestRegime(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Client régime RPBM Pricing"})
        cls.product = cls.env["product.product"].create({"name": "Article régime RPBM Pricing", "list_price": 100})
        cls.Template = cls.env["sale.order.template"]

    def _lead(self, insurer=False):
        vals = {"name": "Dossier régime RPBM Pricing", "type": "opportunity", "partner_id": self.partner.id}
        if insurer:
            if INSURER_FIELD not in self.env["crm.lead"]._fields:
                self.skipTest("champ Studio de l'assureur absent")
            comodel = self.env["crm.lead"]._fields[INSURER_FIELD].comodel_name
            vals[INSURER_FIELD] = self.env[comodel].name_create("Assureur RPBM Pricing test")[0]
        return self.env["crm.lead"].create(vals)

    def _order(self, lead=False, template=False, lines=()):
        return self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "opportunity_id": lead and lead.id,
            "sale_order_template_id": template and template.id,
            "order_line": [(0, 0, {"product_id": self.product.id, **vals}) for vals in lines],
        })

    def test_dossier_regime(self):
        self.assertFalse(self._order().rpbm_regime)
        self.assertEqual(self._order(self._lead()).rpbm_regime, "private")
        self.assertEqual(self._order(self._lead(insurer=True)).rpbm_regime, "insurance")

    def test_template_setup_is_idempotent_and_respects_existing_values(self):
        insurance = self.Template.create({"name": "Pare Brise V"})
        archived = self.Template.create({"name": "Lunette Arrière", "active": False})
        private = self.Template.create({"name": "Glace Hors Assurance"})
        unknown = self.Template.create({"name": "Pare Brise Avec Bandeau"})
        kept = self.Template.create({"name": "Glace Fixe", "rpbm_regime": "private"})

        self.Template._rpbm_template_regime_setup()
        expected = [(insurance, "insurance"), (archived, "insurance"), (private, "private"),
                    (unknown, False), (kept, "private")]
        self.assertEqual([(t, t.rpbm_regime) for t, _value in expected], expected)
        self.assertEqual(self.Template._rpbm_template_regime_setup(), 0)
        self.assertEqual([(t, t.rpbm_regime) for t, _value in expected], expected)

    def test_divergence_warning(self):
        template = self.Template.create({"name": "Modèle hors assurance test", "rpbm_regime": "private"})
        order = self._order(self._lead(insurer=True), template)
        self.assertIn("Le modèle de devis est « Hors assurance », le dossier est « Assurance ».",
                      order.rpbm_pricing_warning)
        template.rpbm_regime = "insurance"
        self.assertFalse(order.rpbm_pricing_warning)

    def test_xglass_labor_warning_on_private_dossier(self):
        order = self._order(self._lead())
        self.assertFalse(order.rpbm_pricing_warning)
        order.write({"order_line": [(0, 0, {"product_id": self.product.id,
                                            "rpbm_labor_operation_key": "rpbm-pricing-test"})]})
        self.assertIn("Main-d'œuvre X'Glass", order.rpbm_pricing_warning)
        self.assertFalse(self._order(lines=[{"rpbm_labor_operation_key": "rpbm-pricing-test"}]).rpbm_pricing_warning)
