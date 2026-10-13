"""Colisage VSF : lecture des références, classement des lignes et coefficient, sans base."""
try:
    from odoo.tests.common import BaseCase as TestCase
    from odoo.addons.rpbm_pricing.lib import colisage
except ImportError:
    from unittest import TestCase
    from lib import colisage


class TestColisagePure(TestCase):
    def test_parse_bill_ref_on_real_forms(self):
        # Références des factures VSF de la préprod (lues le 2026-10-12).
        self.assertEqual(colisage.parse_bill_ref("941797 - MARCH"), (colisage.MARCH, "941797"))
        self.assertEqual(colisage.parse_bill_ref("916930 - MARCH BATEAU"), (colisage.MARCH, "916930"))
        self.assertEqual(colisage.parse_bill_ref("942352 - COMPL"), (colisage.COMPL, "942352"))
        self.assertEqual(colisage.parse_bill_ref("931052 - COMPL MARITIME 2/2"), (colisage.COMPL, "931052"))
        self.assertEqual(colisage.parse_bill_ref(" 942260-pack vin"), (colisage.PACK_VIN, "942260"))
        for ref in ("787500 - AVOIR", "94179 - MARCH", "941797 - MARCHANDISE", "", None):
            self.assertEqual(colisage.parse_bill_ref(ref), (None, None), ref)

    def test_compl_target(self):
        self.assertEqual(colisage.compl_target("FRAIS TRANSPORT 935879 DU 300726"), "935879")
        self.assertEqual(colisage.compl_target("COMP AERIEN FAC749977 DU 020125"), "749977")
        self.assertEqual(colisage.compl_target("VSF - COMPL AERIEN SUR F759807 DU130225"), "759807")
        self.assertEqual(colisage.compl_target("VSF - COMPL AERIEN SUR F769741 du 270325"), "769741")
        for label in ("F817816", "VITRO SERVICE FRANCE - COMPL AERIEN SUR F767521 ", "1935879 DU 300726",
                      "935879 DUPLICATA", "", None):
            self.assertIsNone(colisage.compl_target(label), label)

    def test_classify_line(self):
        self.assertEqual(colisage.classify_line("60710000", "VITRO SERVICE FRANCE - 2025-01-02"), colisage.PIECE)
        self.assertEqual(colisage.classify_line("60870000", "VSF - PIECESC"), colisage.PIECE)
        self.assertEqual(colisage.classify_line("60870000", "FRAIS DE PORT"), colisage.FEE)
        self.assertEqual(colisage.classify_line(False, "COMP MARITIME FAC751102 DU 090125"), colisage.FEE)
        self.assertEqual(colisage.classify_line("60710000", "VSF - 2025-01-30 - PACK VIN"), colisage.EXCLUDED)

    def test_totals_deduct_refunds_and_skip_pack_vin(self):
        lines = [
            ("60710000", "VSF PIECES", 1000.0, False),
            ("60870000", "FRAIS AERIEN", 629.01, False),
            ("60870000", "COMPL AERIEN F900001 DU 010199", 300.0, False),
            ("60710000", "AVOIR PIECE", 50.0, True),
            ("60710000", "PACK VIN", 99.0, False),
        ]
        pieces, fees = colisage.totals(lines)
        self.assertAlmostEqual(pieces, 950.0)
        self.assertAlmostEqual(fees, 929.01)
        self.assertEqual(colisage.totals([]), (0.0, 0.0))

    def test_coefficient(self):
        self.assertAlmostEqual(colisage.coefficient(950.0, 929.01), 1.9779, places=4)
        self.assertEqual(colisage.coefficient(0.0, 629.0), 0.0)
        self.assertEqual(colisage.coefficient(-50.0, 629.0), 0.0)

    def test_is_retained_strictly_above_thresholds(self):
        self.assertTrue(colisage.is_retained(500.01, 629.01, 500, 629))
        self.assertFalse(colisage.is_retained(500.0, 1000.0, 500, 629))
        self.assertFalse(colisage.is_retained(1000.0, 629.0, 500, 629))

    def test_is_boat(self):
        boats = {"751102", "795714"}
        self.assertTrue(colisage.is_boat("751102", ["751102 - MARCH"], boats))
        self.assertTrue(colisage.is_boat("931052", ["931052 - COMPL MARITIME 2/2"], boats))
        self.assertTrue(colisage.is_boat("999999", ["999999 - MARCH", "COMP MARITIME FAC999999 DU 090125"], boats))
        self.assertTrue(colisage.is_boat("916930", ["916930 - MARCH BATEAU"], set()))
        self.assertFalse(colisage.is_boat("941797", ["941797 - MARCH", "VSF PIECES", None], boats))
