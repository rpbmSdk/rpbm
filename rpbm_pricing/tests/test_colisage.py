"""Colisage VSF sur la base : reprise, montants, coefficient annuel.

Factures datées 2099 : elles ne se mêlent pas aux colisages réels et ne butent sur aucune date de
verrouillage. Le partenaire VSF est celui de test (tests/common.py).
"""
from psycopg2 import IntegrityError

from odoo import Command
from odoo.tests import tagged
from odoo.tools import mute_logger

from ..models import params
from .common import RpbmPricingCase


@tagged("post_install", "-at_install")
class TestColisage(RpbmPricingCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_param = cls.env["ir.config_parameter"].sudo().set_param
        set_param(params.COLISAGE_MIN_PIECES[0], "500")
        set_param(params.COLISAGE_MIN_FEES[0], "629")
        # Compte de frais de test : celui du journal pourrait être le 60710000 (pièces) de la préprod.
        cls.fee_account = cls.env["account.account"].create({
            "name": "Frais VSF RPBM Pricing test",
            "code": "RPBMTEST6087",
            "account_type": "expense",
        })
        cls.Colisage = cls.env["rpbm.colisage"]

    def _bill(self, ref, lines, move_type="in_invoice", invoice_date="2099-01-05"):
        """Facture (ou avoir) VSF postée, par défaut le 2099-01-05 ; ``lines`` : couples (libellé, montant HT)."""
        move = self.env["account.move"].create({
            "move_type": move_type,
            "partner_id": self.vsf_partner.id,
            "ref": ref,
            "invoice_date": invoice_date,
            "invoice_line_ids": [Command.create({
                "name": name,
                "quantity": 1,
                "price_unit": amount,
                "account_id": self.fee_account.id,
                "tax_ids": [Command.clear()],
            }) for name, amount in lines],
        })
        move.action_post()
        return move

    def test_import_history_amounts_and_year_report(self):
        march = self._bill("900001 - MARCH", [("VSF PIECES", 1000.0), ("VSF FRAIS AERIEN", 629.01)])
        compl = self._bill("900002 - COMPL", [("VSF - COMPL AERIEN SUR F900001 DU 050199", 300.0)])
        refund = self._bill("900003 - AVOIR", [("AVOIR PIECE", 50.0)], move_type="in_refund")
        self._bill("900004 - COMPL", [("VSF - COMPL AERIEN F817816", 120.0)])
        self._bill("900005 - PACK VIN", [("VSF PACK VIN", 99.0)])

        report = self.Colisage._rpbm_import_history(since="2099-01-01")
        self.assertEqual(report["created"], 1)
        self.assertEqual(report["attached"], 2)
        self.assertEqual(report["refunds_to_attach"], 1)
        self.assertEqual(report["exceptions"], ["900004 - COMPL"])

        colisage = self.Colisage.search([("name", "=", "900001")])
        self.assertEqual(colisage.march_move_id, march)
        self.assertEqual(colisage.move_ids, march | compl)
        self.assertEqual(colisage.partner_id, self.vsf_partner)
        self.assertEqual(colisage.rpbm_mode, "plane")
        self.assertEqual(colisage.year, 2099)

        # L'avoir se rattache à la main ; il est déduit des pièces.
        refund.rpbm_colisage_id = colisage
        self.assertAlmostEqual(colisage.amount_pieces, 950.0)
        self.assertAlmostEqual(colisage.amount_fees, 929.01)
        self.assertAlmostEqual(colisage.coefficient, 1.9779, places=4)
        self.assertTrue(colisage.is_retained)

        # Rejouée, la reprise ne crée ni ne rattache rien ; la COMPL orpheline reste en exception.
        report = self.Colisage._rpbm_import_history(since="2099-01-01")
        self.assertEqual((report["created"], report["attached"], report["refunds_to_attach"]), (0, 0, 0))
        self.assertEqual(report["exceptions"], ["900004 - COMPL"])
        self.assertEqual(self.Colisage.search_count([("name", "=", "900001")]), 1)

        self.env.flush_all()
        line = self.env["rpbm.colisage.year.report"].search([("year", "=", 2099)])
        self.assertEqual(line.colisage_count, 1)
        self.assertAlmostEqual(line.coefficient, (950.0 + 929.01) / 950.0, places=4)

    def test_maritime_compl_switches_to_boat(self):
        self._bill("900011 - MARCH", [("VSF PIECES", 800.0), ("FRAIS DE PORT", 589.0)])
        self._bill("900012 - COMPL MARITIME 1/2", [("COMP MARITIME FAC900011 DU 050199", 900.0)])
        self.Colisage._rpbm_import_history(since="2099-01-01")
        self.assertEqual(self.Colisage.search([("name", "=", "900011")]).rpbm_mode, "boat")

    def test_compl_posted_before_its_march(self):
        # Cas réel de la préprod (826641 avant 826099) : la COMPL est rattachée dès le premier passage.
        compl = self._bill("900042 - COMPL", [("VSF - COMPL SUR F900041 DU 030199", 700.0)], invoice_date="2099-01-03")
        march = self._bill("900041 - MARCH", [("VSF PIECES", 800.0)])
        report = self.Colisage._rpbm_import_history(since="2099-01-01")
        self.assertEqual((report["created"], report["attached"], report["exceptions"]), (1, 2, []))
        self.assertEqual(self.Colisage.search([("name", "=", "900041")]).move_ids, march | compl)
        self.assertEqual(self.Colisage._rpbm_import_history(since="2099-01-01")["attached"], 0)

    def test_duplicate_name_refused(self):
        colisage = self.Colisage.create({"name": "900021"})
        self.assertEqual(colisage.partner_id, self.vsf_partner)
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.cr.savepoint():
            self.Colisage.create({"name": "900021"})

    def test_march_already_held_by_other_name(self):
        march = self._bill("900031 - MARCH", [("VSF PIECES", 800.0)])
        colisage = self.Colisage.create({"name": "900031-A", "march_move_id": march.id})
        report = self.Colisage._rpbm_import_history(since="2099-01-01")
        self.assertEqual((report["created"], report["attached"]), (0, 1))
        self.assertEqual(march.rpbm_colisage_id, colisage)
        self.assertFalse(self.Colisage.search_count([("name", "=", "900031")]))
