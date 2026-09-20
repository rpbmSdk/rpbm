from odoo import fields, models


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    rpbm_detail_model = fields.Char("Détail du modèle")
    rpbm_first_registration_date = fields.Date("Date de 1re mise en circulation")
