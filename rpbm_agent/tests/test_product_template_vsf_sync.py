from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase

from ..controllers import vsf


class TestProductTemplateVSFSync(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "VSF test"})
        cls.env["ir.config_parameter"].sudo().set_param("VSF_LOGIN", "login-test")
        cls.env["ir.config_parameter"].sudo().set_param("VSF_PASSWORD", "secret-test")
        cls.env["ir.config_parameter"].sudo().set_param(
            "rpbm_agent.vsf_partner_id", cls.partner.id
        )
        cls.env["ir.config_parameter"].sudo().set_param(
            "rpbm_agent.vsf_discount", "0.2"
        )

    def _article(self, price="100,00 €", name="Désignation VSF"):
        return vsf.VSFArticle(
            code="6571AGRCHIMVZ",
            name=name,
            prix_vente=price,
            total_stock="1",
            largeurMm=1240,
            longueurMm=560,
            url="https://client.myvsf.fr/catalogue/article/6571AGRCHIMVZ",
        )

    def _template(self, **values):
        return self.env["product.template"].create(
            {
                "name": "Nom commercial client",
                "x_studio_eurocode": "6571AGRCHIMVZ",
                **values,
            }
        )

    def test_supplierinfo_creation_and_same_price_update(self):
        template = self._template()
        today = fields.Date.context_today(template)

        template._sync_vsf_supplierinfo(self._article(), self.partner.id, today)
        line = template.seller_ids
        self.assertEqual(len(line), 1)
        self.assertFalse(line.product_id)
        self.assertEqual(line.product_name, "Désignation VSF")
        self.assertEqual(line.product_code, "6571AGRCHIMVZ")
        self.assertEqual(line.date_start, today)
        self.assertEqual(line.price, 80.0)

        template._sync_vsf_supplierinfo(
            self._article(name="Désignation VSF mise à jour"), self.partner.id, today
        )
        self.assertEqual(len(template.seller_ids), 1)
        self.assertEqual(template.seller_ids.product_name, "Désignation VSF mise à jour")

    def test_supplierinfo_price_history_and_same_day_change(self):
        template = self._template()
        today = fields.Date.context_today(template)
        tomorrow = today + timedelta(days=1)

        template._sync_vsf_supplierinfo(self._article(), self.partner.id, today)
        template._sync_vsf_supplierinfo(self._article("120,00 €"), self.partner.id, tomorrow)
        lines = template.seller_ids.sorted("date_start")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0].date_end, today)
        self.assertEqual(lines[1].date_start, tomorrow)
        self.assertEqual(lines[1].price, 96.0)

        template._sync_vsf_supplierinfo(self._article("125,00 €"), self.partner.id, tomorrow)
        lines = template.seller_ids.sorted("date_start")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[1].date_start, tomorrow)
        self.assertEqual(lines[1].price, 100.0)

    @patch("rpbm_agent.models.product_template.vsf.VSFAgent")
    def test_batch_sync_isolates_failures_and_preserves_identity(self, agent_class):
        valid = self._template(list_price=1.0)
        invalid = self.env["product.template"].create({"name": "Sans eurocode"})
        agent = agent_class.return_value
        agent.getArticleDetails.return_value = {
            "code": "6571AGRCHIMVZ",
            "name": "Désignation VSF",
            "prix_vente": "100,00 €",
            "total_stock": "1",
            "largeurMm": 1240,
            "longueurMm": 560,
            "url": "https://client.myvsf.fr/catalogue/article/6571AGRCHIMVZ",
        }

        report = (valid | invalid).sync_vsf_information()

        self.assertEqual(report["updated_ids"], [valid.id])
        self.assertEqual(report["errors"][0]["id"], invalid.id)
        self.assertEqual(valid.name, "Nom commercial client")
        self.assertEqual(valid.x_studio_eurocode, "6571AGRCHIMVZ")
        self.assertEqual(valid.list_price, 100.0)
        self.assertIn("Informations VSF", valid.description)
