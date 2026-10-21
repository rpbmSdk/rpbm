from odoo.exceptions import UserError
from odoo.tests.common import Form, TransactionCase


class TestStockPickingRack(TransactionCase):
    """M4 : une réception ne se valide pas tant qu'une ligne reste sur un emplacement à racks."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Location = cls.env["stock.location"]
        company = cls.env.company
        view = Location.create({"name": "Vue M4", "usage": "view", "company_id": company.id})
        cls.depot = Location.create({"name": "Dépôt M4", "usage": "internal", "location_id": view.id})
        cls.rack = Location.create({"name": "Rack M4", "usage": "internal", "location_id": cls.depot.id})
        cls.supplier = cls.env.ref("stock.stock_location_suppliers")
        cls.picking_type = cls.env["stock.picking.type"].create({
            "name": "Réception M4",
            "code": "incoming",
            "sequence_code": "M4IN",
            "company_id": company.id,
            "default_location_src_id": cls.supplier.id,
            "default_location_dest_id": cls.depot.id,
        })
        cls.product = cls.env["product.product"].create({"name": "Pare-brise M4", "type": "product"})

    def _receipt(self, quantity, dest=None):
        dest = dest or self.depot
        picking = self.env["stock.picking"].create({
            "picking_type_id": self.picking_type.id,
            "location_id": self.supplier.id,
            "location_dest_id": dest.id,
        })
        move = self.env["stock.move"].create({
            "name": self.product.name,
            "product_id": self.product.id,
            "product_uom_qty": 2,
            "product_uom": self.product.uom_id.id,
            "picking_id": picking.id,
            "location_id": self.supplier.id,
            "location_dest_id": dest.id,
        })
        picking.action_confirm()
        move.quantity = quantity
        move.picked = True
        return picking

    def test_line_on_depot_with_racks_is_refused(self):
        picking = self._receipt(2)
        self.assertEqual(picking.move_line_ids.location_dest_id, self.depot)
        with self.assertRaisesRegex(UserError, "Stocker dans"):
            picking.button_validate()
        self.assertNotEqual(picking.state, "done")

    def test_line_on_rack_is_validated(self):
        picking = self._receipt(2)
        picking.move_line_ids.location_dest_id = self.rack
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertEqual(self.product.with_context(location=self.rack.id).qty_available, 2)

    def test_partial_receipt_on_rack_with_backorder(self):
        picking = self._receipt(1)
        picking.move_line_ids.location_dest_id = self.rack
        action = picking.button_validate()
        Form(self.env[action["res_model"]].with_context(action["context"])).save().process()
        self.assertEqual(picking.state, "done")
        self.assertTrue(self.env["stock.picking"].search([("backorder_id", "=", picking.id)]))

    def test_location_without_rack_is_not_blocked(self):
        picking = self._receipt(2, dest=self.rack)
        self.assertEqual(picking.move_line_ids.location_dest_id, self.rack)
        picking.button_validate()
        self.assertEqual(picking.state, "done")
