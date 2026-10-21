from datetime import date

from odoo.tests.common import TransactionCase


class TestPartnerBirth(TransactionCase):
    """M7 : date et lieu de naissance portés par le client, saisissables depuis l'opportunité."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Assuré M7"})
        cls.lead = cls.env["crm.lead"].create({
            "name": "Opportunité M7", "type": "opportunity", "partner_id": cls.partner.id,
        })

    def test_lead_input_is_written_on_partner(self):
        self.lead.write({"rpbm_birth_date": date(1980, 5, 17), "rpbm_birth_place": "Fort-de-France"})
        self.assertEqual(self.partner.rpbm_birth_date, date(1980, 5, 17))
        self.assertEqual(self.partner.rpbm_birth_place, "Fort-de-France")

    def test_partner_value_is_read_on_lead(self):
        self.partner.write({"rpbm_birth_date": date(1975, 1, 2), "rpbm_birth_place": "Le Lamentin"})
        self.assertEqual(self.lead.rpbm_birth_date, date(1975, 1, 2))
        self.assertEqual(self.lead.rpbm_birth_place, "Le Lamentin")
