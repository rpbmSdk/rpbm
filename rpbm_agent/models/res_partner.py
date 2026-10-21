from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Procédure FFC ; donnée personnelle, réservée aux vendeurs.
    rpbm_birth_date = fields.Date("Date de naissance", groups="sales_team.group_sale_salesman")
    rpbm_birth_place = fields.Char("Lieu de naissance", groups="sales_team.group_sale_salesman")
