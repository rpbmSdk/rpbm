"""Synchronisation natif <-> Studio, avec et sans champs Studio historiques.

Les champs Studio sont créés dans le test lui-même (``ir.model.fields``, ``state='manual'``)
pour que la suite reste jouable sur une base vierge de toute personnalisation Studio.
"""
from datetime import date

from odoo.tests.common import TransactionCase

from ..controllers.main import _enrich_fleet_vehicle_from_metadata
from ..models.legacy_fields import LEGACY_FIELDS

STUDIO_SELECTIONS = {
    "x_studio_field_TAhpP": ["Diesel", "Essence", "Électrique", "Hybride"],
    "x_studio_field_eENQz": ["Pare-Brise", "Lunette arrière", "Glace Latérale", "Autre..."],
    "x_studio_lieu_intervention": ["GALLERIA", "GENIPA", "DOMICILE", "LAVAGE PLACE D'ARMES", "LAVAGE MARIN"],
}
STUDIO_REFERENTIALS = {
    "x_studio_field_KyCjB": ("x_rpbm_marques_voitures", "RPBM_Marques_Voitures"),
    "x_studio_field_ZhaeY": ("x_rpbm_modeles_voitures", "RPBM_Modeles_Voitures"),
}


def _create_studio_fields(env, model_name, mapping):
    """Recrée les champs Studio historiques consommés par le module sur un modèle."""
    Model = env["ir.model"].sudo()
    Fields = env["ir.model.fields"].sudo()
    model = Model.search([("model", "=", model_name)], limit=1)
    for native, (studio, kind) in mapping.items():
        if studio in env[model_name]._fields:
            continue
        vals = {"name": studio, "model_id": model.id, "field_description": studio, "state": "manual"}
        if studio in STUDIO_SELECTIONS:
            vals["ttype"] = "selection"
            vals["selection_ids"] = [(0, 0, {"value": value, "name": value, "sequence": index})
                                     for index, value in enumerate(STUDIO_SELECTIONS[studio])]
        elif studio in STUDIO_REFERENTIALS:
            relation, description = STUDIO_REFERENTIALS[studio]
            if not Model.search([("model", "=", relation)], limit=1):
                Model.create({"name": description, "model": relation, "state": "manual"})
            vals.update({"ttype": "many2one", "relation": relation})
        elif native == "rpbm_xglass_price":
            vals["ttype"] = "float"
        else:
            vals["ttype"] = "char"
        Fields.create(vals)


class TestLegacySyncWithStudio(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for model_name, mapping in LEGACY_FIELDS.items():
            _create_studio_fields(cls.env, model_name, mapping)
        cls.partner = cls.env["res.partner"].create({"name": "Client sync"})
        cls.brand = cls.env["fleet.vehicle.model.brand"].create({"name": "RENAULT"})
        cls.model = cls.env["fleet.vehicle.model"].create({"name": "CLIO", "brand_id": cls.brand.id})

    def _lead(self, **vals):
        return self.env["crm.lead"].create({"name": "Sync", "partner_id": self.partner.id, **vals})

    def test_studio_fields_are_mapped(self):
        self.assertEqual(set(self.env["crm.lead"]._rpbm_legacy_map()), set(LEGACY_FIELDS["crm.lead"]))

    def test_native_values_are_copied_to_studio(self):
        lead = self._lead(
            rpbm_license_plate="AB-123-CD", rpbm_part_type="windshield", rpbm_fuel_type="gasoline",
            rpbm_first_registration_date=date(2020, 9, 1), rpbm_vsf_stock=5,
            rpbm_intervention_location="galleria", rpbm_eurocode="7275AGNMV1P",
        )
        self.assertEqual(lead.x_studio_field_NVioD, "AB-123-CD")
        self.assertEqual(lead.x_studio_field_eENQz, "Pare-Brise")
        self.assertEqual(lead.x_studio_field_TAhpP, "Essence")
        self.assertEqual(lead.x_studio_field_Eh6Wd, "09/2020")
        self.assertEqual(lead.x_studio_field_BKtpw, "5")
        self.assertEqual(lead.x_studio_lieu_intervention, "GALLERIA")
        self.assertEqual(lead.x_studio_field_NwRik, "7275AGNMV1P")

    def test_studio_values_update_native_fields(self):
        lead = self._lead()
        lead.write({
            "x_studio_field_eENQz": "Lunette arrière", "x_studio_field_TAhpP": "Hybride",
            "x_studio_field_Eh6Wd": "03/2019", "x_studio_field_BKtpw": "12", "x_studio_field_NVioD": "ZZ-999-ZZ",
        })
        self.assertEqual(lead.rpbm_part_type, "rear_window")
        self.assertEqual(lead.rpbm_fuel_type, "full_hybrid")
        self.assertEqual(lead.rpbm_first_registration_date, date(2019, 3, 1))
        self.assertEqual(lead.rpbm_vsf_stock, 12)
        self.assertEqual(lead.rpbm_license_plate, "ZZ-999-ZZ")

        lead.write({"x_studio_field_BKtpw": "n/a"})
        self.assertEqual(lead.rpbm_vsf_stock, 12, "valeur Studio non convertible : natif inchangé")

    def test_native_wins_when_both_are_written(self):
        lead = self._lead(rpbm_part_type="side_window", x_studio_field_eENQz="Pare-Brise")
        self.assertEqual(lead.rpbm_part_type, "side_window")
        self.assertEqual(lead.x_studio_field_eENQz, "Glace Latérale")

    def test_unconvertible_native_leaves_studio_untouched(self):
        lead = self._lead(rpbm_fuel_type="gasoline")
        lead.write({"rpbm_fuel_type": "lpg"})
        self.assertEqual(lead.x_studio_field_TAhpP, "Essence")

    def test_brand_and_model_round_trip_through_studio_referentials(self):
        lead = self._lead(rpbm_vehicle_brand_id=self.brand.id, rpbm_vehicle_model_id=self.model.id)
        self.assertEqual(lead.x_studio_field_KyCjB.x_name, "RENAULT")
        self.assertEqual(lead.x_studio_field_ZhaeY.x_name, "CLIO")

        studio_brand = self.env["x_rpbm_marques_voitures"].create({"x_name": "Peugeot"})
        studio_model = self.env["x_rpbm_modeles_voitures"].create({"x_name": "3008"})
        lead.write({"x_studio_field_KyCjB": studio_brand.id, "x_studio_field_ZhaeY": studio_model.id})
        self.assertEqual(lead.rpbm_vehicle_brand_id.name, "Peugeot")
        self.assertEqual(lead.rpbm_vehicle_model_id.name, "3008")
        self.assertEqual(lead.rpbm_vehicle_model_id.brand_id, lead.rpbm_vehicle_brand_id)

        # Un homonyme d'orthographe différente réutilise le référentiel existant.
        other = self._lead(rpbm_vehicle_brand_id=self.env["fleet.vehicle.model.brand"].create({"name": "PEUGEOT"}).id)
        self.assertEqual(other.x_studio_field_KyCjB, studio_brand)

    def test_vehicle_link_derives_fields_and_syncs_studio(self):
        vehicle = self.env["fleet.vehicle"].create({
            "model_id": self.model.id, "license_plate": "BF857CZ", "vin_sn": "var = VF1RJA00X64812285;",
            "fuel_type": "diesel", "rpbm_detail_model": "CLIO V 1.0 TCe", "rpbm_first_registration_date": date(2020, 6, 1),
        })
        lead = self._lead(rpbm_vin="ANCIEN")
        lead.write({"rpbm_vehicle_id": vehicle.id})
        self.assertEqual(lead.rpbm_license_plate, "BF857CZ")
        self.assertEqual(lead.rpbm_vehicle_brand_id, self.brand)
        self.assertEqual(lead.rpbm_vehicle_model_id, self.model)
        self.assertEqual(lead.rpbm_vin, "VF1RJA00X64812285")
        self.assertEqual(lead.rpbm_fuel_type, "diesel")
        self.assertEqual(lead.x_studio_field_PfJlB, "VF1RJA00X64812285")
        self.assertEqual(lead.x_studio_field_TAhpP, "Diesel")
        self.assertEqual(lead.x_studio_field_Eh6Wd, "06/2020")
        self.assertEqual(lead.x_studio_field_i8fWl, "CLIO V 1.0 TCe")
        self.assertEqual(lead.x_studio_field_KyCjB.x_name, "RENAULT")

        lead.write({"rpbm_vehicle_id": False})
        self.assertEqual(lead.rpbm_vin, "VF1RJA00X64812285", "sans véhicule, les valeurs sont conservées")

    def test_sale_order_mirrors_write_through_to_the_opportunity(self):
        lead = self._lead(rpbm_eurocode_base="7275A")
        order = self.env["sale.order"].create({"partner_id": self.partner.id, "opportunity_id": lead.id})
        self.assertEqual(order.rpbm_eurocode_base, "7275A")
        order.write({"rpbm_eurocode_base": "7310A", "rpbm_part_type": "other"})
        self.assertEqual(lead.rpbm_eurocode_base, "7310A")
        self.assertEqual(lead.x_studio_field_ORIyy, "7310A")
        self.assertEqual(lead.x_studio_field_eENQz, "Autre...")

    def test_sale_order_line_price_is_synced_both_ways(self):
        product = self.env["product.product"].create({"name": "Vitrage", "detailed_type": "consu"})
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        line = self.env["sale.order.line"].create({
            "order_id": order.id, "product_id": product.id, "product_uom_qty": 1, "rpbm_xglass_price": 100.0,
        })
        self.assertEqual(line.x_studio_prix_x_glass, 100.0)
        line.write({"x_studio_prix_x_glass": 80.0})
        self.assertEqual(line.rpbm_xglass_price, 80.0)

    def test_fleet_enrichment_only_fills_missing_or_malformed_values(self):
        vehicle = self.env["fleet.vehicle"].create({"model_id": self.model.id, "license_plate": "FQ581EN"})
        warnings = []
        written = _enrich_fleet_vehicle_from_metadata(vehicle, {"vin": " VF1RJA00X64812285 ", "dateMec": "06/2020"}, warnings)
        self.assertEqual(written, {"vin_sn": "VF1RJA00X64812285", "rpbm_first_registration_date": date(2020, 6, 1)})
        self.assertEqual(warnings, [])

        written = _enrich_fleet_vehicle_from_metadata(vehicle, {"vin": "VF3MRHNSMNS091999", "dateMec": "01/2022"}, warnings)
        self.assertEqual(written, {}, "valeurs Fleet existantes jamais remplacées")

        vehicle.vin_sn = "var = VF3MRHNSMNS091999;"
        written = _enrich_fleet_vehicle_from_metadata(vehicle, {"vin": "VF3MRHNSMNS091999"}, warnings)
        self.assertEqual(written, {"vin_sn": "VF3MRHNSMNS091999"})

        _enrich_fleet_vehicle_from_metadata(vehicle, {"dateMec": "date-invalide"}, warnings)
        self.assertTrue(any("Date MEC" in warning for warning in warnings))


class TestLegacySyncWithoutStudio(TransactionCase):
    def test_module_works_without_any_studio_field(self):
        lead_fields = self.env["crm.lead"]._fields
        if any(studio in lead_fields for studio, _kind in LEGACY_FIELDS["crm.lead"].values()):
            self.skipTest("des champs Studio historiques existent sur cette base")
        self.assertEqual(self.env["crm.lead"]._rpbm_legacy_map(), {})

        partner = self.env["res.partner"].create({"name": "Client sans Studio"})
        lead = self.env["crm.lead"].create({
            "name": "Sans Studio", "partner_id": partner.id, "rpbm_license_plate": "AB-123-CD",
            "rpbm_part_type": "windshield", "rpbm_intervention_location": "genipa",
        })
        lead.write({"rpbm_eurocode_base": "7275A"})
        self.assertEqual(lead.rpbm_eurocode_base, "7275A")

        order = self.env["sale.order"].create({"partner_id": partner.id, "opportunity_id": lead.id})
        self.assertEqual(order.carrier_id.name if order.carrier_id else False, False,
                         "sans transporteur configuré, le préremplissage laisse le champ vide sans erreur")
        self.assertEqual(order.rpbm_license_plate, "AB-123-CD")
