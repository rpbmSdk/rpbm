from unittest import TestCase

from odoo.tests.common import TransactionCase

from ..hooks import (
    FIELDS_TO_ENSURE,
    _replace_legacy_vehicle_text,
    _write_view_reference_replacement,
)


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
