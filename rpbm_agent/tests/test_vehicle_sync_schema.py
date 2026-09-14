from unittest import TestCase

from odoo.tests.common import TransactionCase

from ..hooks import (
    FIELDS_TO_ENSURE,
    _replace_legacy_vehicle_references,
    _replace_legacy_vehicle_text,
    _write_view_reference_replacement,
)


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

    def test_legacy_view_rewrite_migration_is_now_a_noop(self):
        self.assertIsNone(_replace_legacy_vehicle_references(object()))


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


class _Savepoint:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class _Cursor:
    def savepoint(self):
        return _Savepoint()


class _ViewRecord:
    id = 42

    def __init__(
        self,
        replacement,
        *,
        original_invalid,
        replacement_error="invalid inherited view",
    ):
        self.replacement = replacement
        self.original_invalid = original_invalid
        self.replacement_error = replacement_error
        self.writes = []
        self.invalidated = []

    def write(self, values):
        value = values["arch_db"]
        self.writes.append(value)
        if value == self.replacement:
            raise ValueError(self.replacement_error)
        if self.original_invalid and "validation probe" in value:
            raise ValueError("x_studio_y_a_t_il_un_parrain absent")

    def invalidate_recordset(self, fields):
        self.invalidated.append(fields)


class _ViewEnvironment:
    cr = _Cursor()


class TestLegacyViewMigrationGuard(TestCase):
    def test_invalid_original_view_is_skipped_after_failed_replacement(self):
        original = '<field name="x_studio_field_KyCjB"/>'
        replacement = _replace_legacy_vehicle_text(original)
        record = _ViewRecord(replacement, original_invalid=True)

        migrated = _write_view_reference_replacement(
            _ViewEnvironment(), record, "arch_db", original, replacement
        )

        self.assertFalse(migrated)
        self.assertEqual(
            record.writes,
            [replacement, original + "\n<!-- rpbm_agent validation probe -->"],
        )
        self.assertEqual(len(record.invalidated), 2)

    def test_valid_original_view_still_raises_replacement_error(self):
        original = '<field name="x_studio_field_KyCjB"/>'
        replacement = _replace_legacy_vehicle_text(original)
        record = _ViewRecord(replacement, original_invalid=False)

        with self.assertRaisesRegex(ValueError, "invalid inherited view"):
            _write_view_reference_replacement(
                _ViewEnvironment(), record, "arch_db", original, replacement
            )

        self.assertEqual(len(record.writes), 2)

    def test_error_on_new_reference_is_never_hidden_by_existing_invalidity(self):
        original = '<field name="x_studio_field_KyCjB"/>'
        replacement = _replace_legacy_vehicle_text(original)
        record = _ViewRecord(
            replacement,
            original_invalid=True,
            replacement_error="unknown x_rpbm_vehicle_brand_id",
        )

        with self.assertRaisesRegex(ValueError, "x_rpbm_vehicle_brand_id"):
            _write_view_reference_replacement(
                _ViewEnvironment(), record, "arch_db", original, replacement
            )

        self.assertEqual(record.writes, [replacement])
