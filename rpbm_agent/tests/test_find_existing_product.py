from odoo.tests.common import TransactionCase

from odoo.addons.rpbm_agent.controllers.main import _find_existing_product


class TestFindExistingProduct(TransactionCase):
    """Rattachement d'un article VSF à un produit Odoo (lot E1.1).

    Codes et noms propres au test : le résultat ne dépend pas des produits de la base.
    """

    def _product(self, name, default_code=False, eurocode=False):
        return self.env["product.product"].create(
            {"name": name, "default_code": default_code, "rpbm_eurocode": eurocode}
        )

    def _find(self, product_code, eurocode, name):
        return _find_existing_product(self.env, product_code, eurocode, name)

    def test_name_of_a_product_with_another_eurocode_is_not_matched(self):
        # Pre-prod : la suggestion 6108AXSR « GEL CAPTEUR SILICONE » était rattachée
        # par le nom au produit 3420, dont la référence et l'eurocode valent 6574AXSH.
        name = "GEL CAPTEUR SILICONE (test E1.1)"
        self._product(name, "TEST6574AXSH", "TEST6574AXSH")
        self.assertEqual(self._find("TEST6108AXSR", "TEST6108AXSR", name), (self.env["product.product"], None))

    def test_exact_eurocode_comes_first(self):
        product = self._product("Pare-brise (test E1.1)", "TEST-REF-A", "TEST6108AGNSMVZ")
        self._product("Ancien pare-brise (test E1.1)", "TEST-REF-SHARED")
        self.assertEqual(
            self._find("TEST-REF-SHARED", "TEST6108AGNSMVZ", "Ancien pare-brise (test E1.1)"),
            (product, "eurocode"),
        )

    def test_internal_reference_matches_a_product_without_eurocode(self):
        legacy = self._product("Ancien article B (test E1.1)", "TEST-REF-B")
        empty = self._product("Ancien article B2 (test E1.1)", "TEST-REF-B2", "")
        self.assertEqual(self._find("TEST-REF-B", "TEST-NEW-B", "Autre nom"), (legacy, "reference_interne"))
        self.assertEqual(self._find("TEST-REF-B2", "TEST-NEW-B2", "Autre nom"), (empty, "reference_interne"))

    def test_internal_reference_of_a_product_with_another_eurocode_is_not_matched(self):
        product = self._product("Article C (test E1.1)", "TEST-REF-C", "TEST-EUROCODE-C")
        self.assertEqual(
            self._find("TEST-REF-C", "TEST-EUROCODE-OTHER", "Autre nom"),
            (self.env["product.product"], None),
        )
        # Sans eurocode connu, la référence interne suffit.
        self.assertEqual(self._find("TEST-REF-C", "", "Autre nom"), (product, "reference_interne"))

    def test_unique_name_matches_a_legacy_product_without_eurocode(self):
        legacy = self._product("Ancien article D (test E1.1)")
        self.assertEqual(
            self._find("TEST-REF-NONE", "TEST-EUROCODE-NONE", "ancien article d (test e1.1)"),
            (legacy, "nom"),
        )

    def test_duplicate_legacy_names_are_not_matched(self):
        self._product("Ancien article E (test E1.1)")
        self._product("Ancien article E (test E1.1)")
        self.assertEqual(
            self._find("TEST-REF-NONE", "TEST-EUROCODE-NONE", "Ancien article E (test E1.1)"),
            (self.env["product.product"], None),
        )
