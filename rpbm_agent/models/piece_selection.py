from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    x_rpbm_xglass_piece_id = fields.Char(
        string="Identifiant pièce X'Glass sélectionnée"
    )
    x_rpbm_piece_oe_id = fields.Char(
        string="Identifiant pièce OE sélectionnée"
    )
    x_rpbm_piece_am_id = fields.Char(
        string="Identifiant pièce après-marché sélectionnée"
    )


class SaleOrder(models.Model):
    _inherit = "sale.order"

    x_rpbm_xglass_piece_id = fields.Char(
        string="Identifiant pièce X'Glass sélectionnée",
        related="opportunity_id.x_rpbm_xglass_piece_id",
        store=True,
    )
    x_rpbm_piece_oe_id = fields.Char(
        string="Identifiant pièce OE sélectionnée",
        related="opportunity_id.x_rpbm_piece_oe_id",
        store=True,
    )
    x_rpbm_piece_am_id = fields.Char(
        string="Identifiant pièce après-marché sélectionnée",
        related="opportunity_id.x_rpbm_piece_am_id",
        store=True,
    )
