from odoo.tests.common import TransactionCase

from ..hooks import FIELDS_TO_ENSURE


class TestVehicleSynchronizationSchema(TransactionCase):
    def test_duplicate_fleet_aliases_are_not_declared_for_future_creation(self):
        specs = {(spec["model"], spec["name"]): spec for spec in FIELDS_TO_ENSURE}

        duplicate_names = {
            "x_rpbm_vehicle_brand_id",
            "x_rpbm_vehicle_model_id",
            "x_rpbm_vehicle_brand_name",
            "x_rpbm_vehicle_model_name",
            "x_rpbm_vehicle_vin",
            "x_rpbm_vehicle_detail_model",
            "x_rpbm_vehicle_fuel_type",
            "x_rpbm_vehicle_date_mec",
        }
        self.assertFalse(
            duplicate_names.intersection(spec["name"] for spec in FIELDS_TO_ENSURE)
        )
        self.assertFalse(
            any(
                spec["name"] in duplicate_names
                for spec in FIELDS_TO_ENSURE
                if spec["model"] in {"crm.lead", "sale.order"}
            )
        )

    def test_canonical_and_existing_fleet_fields_remain_declared(self):
        specs = {(spec["model"], spec["name"]): spec for spec in FIELDS_TO_ENSURE}

        for model in ("crm.lead", "sale.order"):
            self.assertIn((model, "x_studio_vehicle_id"), specs)

        crm_vehicle = specs[("crm.lead", "x_studio_vehicle_id")]
        self.assertEqual(crm_vehicle["relation"], "fleet.vehicle")

        sale_vehicle = specs[("sale.order", "x_studio_vehicle_id")]
        self.assertEqual(sale_vehicle["relation"], "fleet.vehicle")
        self.assertEqual(sale_vehicle["related"], "opportunity_id.x_studio_vehicle_id")
        self.assertTrue(sale_vehicle["store"])

        for field_name, field_type in (
            ("x_studio_detail_model", "char"),
            ("x_studio_date_mec", "date"),
        ):
            fleet_field = specs[("fleet.vehicle", field_name)]
            self.assertEqual(fleet_field["ttype"], field_type)

        vsf_reference = specs[("sale.order", "x_rpbm_vsf_constructor_reference")]
        self.assertEqual(vsf_reference["related"], "opportunity_id.x_studio_field_MNzfJ")
        self.assertTrue(vsf_reference["store"])
