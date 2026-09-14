from pathlib import Path
from unittest import SkipTest, TestCase
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase

from ..models.sale_order import (
    HISTORICAL_LOCATION_TO_CARRIER,
    carrier_name_for_historical_location,
    normalize_historical_location,
)


class TestHistoricalLocationMapping(TestCase):
    def test_mapping_is_normalized_and_limited_to_the_three_supported_locations(self):
        self.assertEqual(
            carrier_name_for_historical_location(" Galleria "),
            "Retrait / pose Galleria",
        )
        self.assertEqual(
            carrier_name_for_historical_location("DOMICILE"),
            "Pose sur site (Camion)",
        )
        self.assertIsNone(carrier_name_for_historical_location("LAVAGE MARIN"))
        self.assertIsNone(carrier_name_for_historical_location("AUTRE"))
        self.assertEqual(
            set(HISTORICAL_LOCATION_TO_CARRIER),
            {"galleria", "genipa", "domicile"},
        )

    def test_normalizer_removes_accents_and_collapses_spaces(self):
        self.assertEqual(
            normalize_historical_location("  Pose   à domicile "),
            "pose a domicile",
        )


class TestSaleOrderCarrier(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if "x_studio_lieu_intervention" not in cls.env["crm.lead"]._fields:
            raise SkipTest(
                "Le test d'intégration exige le champ historique CRM "
                "x_studio_lieu_intervention sur la base de recette."
            )
        cls.partner = cls.env["res.partner"].create({"name": "Client transporteur AG01-03"})
        cls.carriers = {}
        for name in (
            "Retrait / pose Galleria",
            "Retrait / pose Genipa",
            "Pose sur site (Camion)",
        ):
            product = cls.env["product.product"].create(
                {"name": "Service AG01-03 - %s" % name, "detailed_type": "service"}
            )
            cls.carriers[name] = cls.env["delivery.carrier"].create(
                {"name": name, "product_id": product.id, "delivery_type": "fixed"}
            )

    def _lead(self, location=False):
        return self.env["crm.lead"].create(
            {
                "name": "Opportunité AG01-03",
                "type": "opportunity",
                "partner_id": self.partner.id,
                "x_studio_lieu_intervention": location,
            }
        )

    def _order(self, **values):
        return self.env["sale.order"].create(
            {"partner_id": self.partner.id, **values}
        )

    def test_create_prefills_the_three_supported_carriers(self):
        for location, expected_name in (
            ("GALLERIA", "Retrait / pose Galleria"),
            ("GENIPA", "Retrait / pose Genipa"),
            ("DOMICILE", "Pose sur site (Camion)"),
        ):
            order = self._order(opportunity_id=self._lead(location).id)
            self.assertEqual(order.carrier_id, self.carriers[expected_name])

    def test_create_does_not_guess_unmapped_location_or_empty_source(self):
        for location in ("LAVAGE MARIN", False):
            order = self._order(opportunity_id=self._lead(location).id)
            self.assertFalse(order.carrier_id)

    def test_missing_or_ambiguous_carrier_is_left_empty(self):
        missing = self.carriers["Retrait / pose Galleria"]
        missing.active = False
        missing_order = self._order(opportunity_id=self._lead("GALLERIA").id)
        self.assertFalse(missing_order.carrier_id)

        missing.active = True
        self.env["delivery.carrier"].create(
            {"name": missing.name, "product_id": missing.product_id.id}
        )
        ambiguous_order = self._order(opportunity_id=self._lead("GALLERIA").id)
        self.assertFalse(ambiguous_order.carrier_id)

    def test_carrier_access_error_is_non_blocking_at_creation(self):
        lead = self._lead("GENIPA")
        carrier_model_class = type(self.env["delivery.carrier"])
        with patch.object(
            carrier_model_class,
            "search",
            side_effect=AccessError("lecture interdite"),
        ):
            order = self._order(opportunity_id=lead.id)
        self.assertFalse(order.carrier_id)

    def test_explicit_carrier_wins_and_existing_write_is_not_retrofilled(self):
        lead = self._lead("GALLERIA")
        explicit = self.carriers["Retrait / pose Genipa"]
        order = self._order(opportunity_id=lead.id, carrier_id=explicit.id)
        self.assertEqual(order.carrier_id, explicit)

        empty_order = self._order()
        empty_order.write({"opportunity_id": lead.id})
        self.assertFalse(empty_order.carrier_id)

    def test_onchange_prefills_only_a_new_empty_draft(self):
        lead = self._lead("GENIPA")
        new_order = self.env["sale.order"].new({"partner_id": self.partner.id})
        new_order.opportunity_id = lead
        new_order._onchange_rpbm_opportunity_carrier()
        self.assertEqual(new_order.carrier_id, self.carriers["Retrait / pose Genipa"])

        existing_order = self._order()
        existing_order.opportunity_id = lead
        existing_order._onchange_rpbm_opportunity_carrier()
        self.assertFalse(existing_order.carrier_id)

    def test_onchange_warns_for_manual_or_unknown_locations(self):
        for location in ("LAVAGE MARIN", "INCONNU", False):
            order = self.env["sale.order"].new({"partner_id": self.partner.id})
            order.opportunity_id = self._lead(location)
            result = order._onchange_rpbm_opportunity_carrier()
            self.assertFalse(order.carrier_id)
            self.assertIn("choisissez", result["warning"]["message"])

    def test_confirmation_requires_carrier_without_creating_delivery_side_effects(self):
        order = self._order()
        with self.assertRaises(UserError):
            order.action_confirm()
        self.assertEqual(len(order.order_line), 0)
        self.assertEqual(len(order.picking_ids), 0)

        order.carrier_id = self.carriers["Retrait / pose Galleria"]
        order.action_confirm()
        self.assertEqual(order.state, "sale")
        self.assertEqual(len(order.order_line), 0)
        self.assertEqual(len(order.picking_ids), 0)

        linked_missing = self._order(opportunity_id=self._lead("DOMICILE").id)
        with self.assertRaises(UserError):
            linked_missing.action_confirm()
        self.assertEqual(len(linked_missing.order_line), 0)
        self.assertEqual(len(linked_missing.picking_ids), 0)

        linked_order = self._order(
            opportunity_id=self._lead("DOMICILE").id,
            carrier_id=self.carriers["Pose sur site (Camion)"].id,
        )
        linked_order.action_confirm()
        self.assertEqual(linked_order.state, "sale")
        self.assertEqual(len(linked_order.order_line), 0)
        self.assertEqual(len(linked_order.picking_ids), 0)


class TestSaleOrderCarrierView(TestCase):
    def test_manifest_and_versioned_view_declare_carrier_contract(self):
        root = Path(__file__).parents[1]
        manifest = (root / "__manifest__.py").read_text(encoding="utf-8")
        sale_view = (root / "views" / "sale_order_views.xml").read_text(
            encoding="utf-8"
        )
        view = (root / "views" / "sale_order_carrier_views.xml").read_text(
            encoding="utf-8"
        )

        self.assertIn('"delivery"', manifest)
        self.assertNotIn('"stock_delivery"', manifest)
        self.assertIn('id="view_order_form_rpbm_carrier"', view)
        self.assertIn('<field name="priority" eval="110"/>', view)
        self.assertIn('string="Transporteur / mode de remise"', view)
        self.assertIn("options=\"{'no_create': True, 'no_open': True}\"", view)
        self.assertIn("readonly=\"state in ['sale', 'cancel'] or locked\"", view)
        self.assertNotIn('required="1"', view)
        self.assertIn("//sheet//field[@name='partner_id']", view)
        self.assertEqual(view.count('<field name="carrier_id"'), 1)
        self.assertNotIn("carrier_id", sale_view)
