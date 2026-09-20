from unittest import TestCase

from ..controllers.main import XGLASS_ENERGY_TO_FUEL_TYPE, _xglass_fuel_type

# Clés de fleet.models.fleet_vehicle_model.FUEL_TYPES (Odoo 17).
FLEET_FUEL_TYPES = {
    "diesel", "gasoline", "full_hybrid", "plug_in_hybrid_diesel",
    "plug_in_hybrid_gasoline", "cng", "lpg", "hydrogen", "electric",
}


class TestXGlassFuelType(TestCase):
    def test_mapping_only_targets_native_fleet_keys(self):
        self.assertTrue(set(XGLASS_ENERGY_TO_FUEL_TYPE.values()) <= FLEET_FUEL_TYPES)

    def test_known_energies_are_mapped_even_when_received_as_strings(self):
        self.assertEqual(_xglass_fuel_type(233), "gasoline")
        self.assertEqual(_xglass_fuel_type("234"), "diesel")
        self.assertEqual(_xglass_fuel_type(273), "electric")

    def test_unknown_or_invalid_energy_leaves_the_field_empty(self):
        # 238 = Éthanol : aucun équivalent Fleet, le véhicule doit quand même être créé.
        self.assertFalse(_xglass_fuel_type(238))
        self.assertFalse(_xglass_fuel_type(None))
        self.assertFalse(_xglass_fuel_type("Essence"))
