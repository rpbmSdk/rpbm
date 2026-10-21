from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    rpbm_vehicle_id = fields.Many2one(related="sale_id.rpbm_vehicle_id", store=True, index=True)

    def _action_done(self):
        # Rangement manuel (pas de règle vers les racks) : sans ce refus, la marchandise reste sur le
        # dépôt parent. Seules les lignes que stock.move._action_done garde (cochées, quantité > 0).
        for picking in self.filtered(lambda p: p.picking_type_code == "incoming"):
            lines = picking.move_line_ids.filtered(
                lambda ml: ml.picked and ml.quantity > 0 and ml.move_id.state not in ("done", "cancel")
                and ml.location_dest_id.child_internal_location_ids - ml.location_dest_id
            )
            if lines:
                raise UserError(_(
                    "Réception %(name)s : choisissez le rack de chaque ligne (☰ › colonne « Stocker dans ») "
                    "avant de valider. Lignes encore sur un emplacement qui contient des racks : %(lines)s",
                    name=picking.name,
                    lines=", ".join(f"{ml.product_id.display_name} → {ml.location_dest_id.display_name}" for ml in lines),
                ))
        return super()._action_done()
