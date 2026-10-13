from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Barème de la ligne de devis, gardé pour le contrôle (IMP-10) ; aucune vue ni impression ne l'affiche.
    rpbm_xglass_price = fields.Float("Barème X'Glass", digits="Product Price")
