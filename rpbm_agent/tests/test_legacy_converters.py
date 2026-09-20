"""Convertisseurs natif <-> Studio, sans base Odoo."""
from datetime import date
from unittest import TestCase

from ..models.legacy_fields import (
    CONVERTERS,
    LEGACY_FIELDS,
    clean_vin,
    date_to_month_year,
    is_legacy_malformed_vin,
    month_year_to_date,
    normalize,
)


def to_legacy(kind, value):
    return CONVERTERS[kind][0](None, None, value, None, {})


def to_native(kind, value):
    return CONVERTERS[kind][1](None, None, value, None, {})


class TestLegacyConverters(TestCase):
    def test_normalize_ignores_accents_case_and_spaces(self):
        self.assertEqual(normalize("  CITROËN  "), "citroen")
        self.assertEqual(normalize("Pare-Brise"), normalize("pare-brise"))

    def test_vin_legacy_syntax_is_detected_and_cleaned(self):
        self.assertTrue(is_legacy_malformed_vin("var  = VF3MRHNSMNS091999;"))
        self.assertFalse(is_legacy_malformed_vin("VF3MRHNSMNS091999"))
        self.assertEqual(clean_vin(" var = VF3MRHNSMNS091999; "), "VF3MRHNSMNS091999")
        self.assertEqual(clean_vin(" VF3MRHNSMNS091999 "), "VF3MRHNSMNS091999")

    def test_month_year_round_trip(self):
        self.assertEqual(month_year_to_date("09/2020"), date(2020, 9, 1))
        self.assertEqual(month_year_to_date("2021-04-16"), date(2021, 4, 16))
        self.assertIsNone(month_year_to_date("date-invalide"))
        self.assertEqual(month_year_to_date("12/08"), date(2008, 12, 1))
        self.assertEqual(month_year_to_date("10/99"), date(1999, 10, 1))
        self.assertEqual(month_year_to_date("2015"), date(2015, 1, 1))
        self.assertEqual(month_year_to_date("15/06/2019"), date(2019, 6, 1))
        self.assertEqual(date_to_month_year(date(2020, 9, 15)), "09/2020")
        self.assertEqual(to_legacy("month_year", date(2019, 3, 1)), "03/2019")
        self.assertEqual(to_native("month_year", "03/2019"), date(2019, 3, 1))
        self.assertIsNone(to_native("month_year", "mars 2019"))

    def test_fuel_mapping_and_unconvertible_values(self):
        self.assertEqual(to_legacy("fuel", "gasoline"), "Essence")
        self.assertEqual(to_legacy("fuel", "plug_in_hybrid_diesel"), "Hybride")
        self.assertIsNone(to_legacy("fuel", "lpg"))
        self.assertEqual(to_native("fuel", "Électrique"), "electric")
        self.assertEqual(to_native("fuel", "hybride"), "full_hybrid")
        self.assertIsNone(to_native("fuel", "GPL"))

    def test_part_type_and_location_are_bijective_on_known_values(self):
        for key, label in (("windshield", "Pare-Brise"), ("rear_window", "Lunette arrière"),
                           ("side_window", "Glace Latérale"), ("other", "Autre...")):
            self.assertEqual(to_legacy("part_type", key), label)
            self.assertEqual(to_native("part_type", label), key)
        self.assertIsNone(to_native("part_type", "Vitre de toit"))
        self.assertEqual(to_legacy("location", "lavage_place_armes"), "LAVAGE PLACE D'ARMES")
        self.assertEqual(to_native("location", "GALLERIA"), "galleria")
        self.assertIsNone(to_native("location", "AILLEURS"))

    def test_int_char_conversion(self):
        self.assertEqual(to_legacy("int_char", 5), "5")
        self.assertEqual(to_legacy("int_char", 0), "0")
        self.assertEqual(to_native("int_char", " 12 "), 12)
        self.assertFalse(to_native("int_char", ""))
        self.assertIsNone(to_native("int_char", "abc"))

    def test_identity_normalizes_empty_values(self):
        self.assertFalse(to_legacy(None, ""))
        self.assertFalse(to_legacy(None, None))
        self.assertEqual(to_legacy(None, "AB-123-CD"), "AB-123-CD")

    def test_mapping_only_targets_native_prefixed_fields(self):
        for model_map in LEGACY_FIELDS.values():
            for native, (studio, kind) in model_map.items():
                self.assertTrue(native.startswith("rpbm_"), native)
                self.assertTrue(studio.startswith("x_studio_"), studio)
                self.assertIn(kind, CONVERTERS)
