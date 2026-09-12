from odoo.tests.common import TransactionCase

from ..hooks import FIELDS_TO_ENSURE, _replace_legacy_vehicle_text


class TestVehicleSynchronizationSchema(TransactionCase):
    def test_fleet_related_fields_are_declared_on_crm_and_sale_order(self):
        specs = {(spec["model"], spec["name"]): spec for spec in FIELDS_TO_ENSURE}

        crm_brand = specs[("crm.lead", "x_rpbm_vehicle_brand_id")]
        self.assertEqual(crm_brand["relation"], "fleet.vehicle.model.brand")
        self.assertEqual(crm_brand["related"], "x_studio_vehicle_id.model_id.brand_id")
        self.assertTrue(crm_brand["store"])

        sale_model = specs[("sale.order", "x_rpbm_vehicle_model_id")]
        self.assertEqual(sale_model["relation"], "fleet.vehicle.model")
        self.assertEqual(sale_model["related"], "opportunity_id.x_rpbm_vehicle_model_id")
        self.assertTrue(sale_model["store"])

    def test_legacy_qweb_references_are_replaced_without_touching_similar_names(self):
        source = (
            '<span t-field="doc.x_studio_field_KyCjB.x_name"/>'
            '<field name="x_studio_modle_"/>'
            '<field name="x_studio_modle_devis_"/>'
        )

        migrated = _replace_legacy_vehicle_text(source)

        self.assertIn("doc.x_rpbm_vehicle_brand_name", migrated)
        self.assertIn('name="x_rpbm_vehicle_model_name"', migrated)
        self.assertIn('name="x_studio_modle_devis_"', migrated)
