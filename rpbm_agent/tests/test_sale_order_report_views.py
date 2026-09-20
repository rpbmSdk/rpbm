"""AG01-04 — contrat des vues module qui font evoluer les rapports Studio.

Le rendu QWeb complet ne peut etre verifie qu'en recette Odoo.sh (les vues
Studio heritees vivent en base, pas dans le depot). Ces tests verifient donc ce
qui est verifiable hors instance : le fichier est du XML bien forme, il est
declare au manifest, chaque rapport herite de l'external id attendu, le bloc
transporteur y est ajoute exactement une fois avec son repli historique, et
aucune des contraintes de non-suppression du lot AG-01 n'est enfreinte.
"""
from pathlib import Path
from unittest import TestCase
from xml.etree import ElementTree

ROOT = Path(__file__).parents[1]
VIEW_PATH = ROOT / "views" / "sale_order_report_views.xml"

# Rapport -> external id de la vue Studio heritee (verifie sur rpbm-preprod).
EXPECTED_INHERITS = {
    "report_rpbm_devis_commande_carrier":
        "studio_customization.odoo_studio_report_s_ac7d3db8-340a-4fdd-807c-2dbafe95bb60",
    "report_rpbm_ordre_reparation_vehicule":
        "studio_customization.odoo_studio_studio_c_5f4f5a86-237d-4056-ab5d-5cd23f66c22c",
    "report_rpbm_or_vehicule":
        "studio_customization.odoo_studio_report_s_a834eac1-0318-4f74-bc4e-6d416f0ce2e1",
    "report_rpbm_devis_brouillon_carrier":
        "studio_customization.report_saleorder_doc_51c4118c-4f77-4aac-aea2-16fb8c467006",
    "report_rpbm_dbdg_carrier":
        "studio_customization.odoo_studio_studio_c_0f4704bf-cc93-4c06-8b4d-880b08a2ec5b",
}

# Seuls ces deux affichages sont retires, et uniquement sur 1505 et 1513 :
# ce sont les variantes char autonomes (2 devis renseignes sur 7353), doublons
# des related alimentes par AG01-01/02 dans la meme cellule.
EXPECTED_REMOVALS = {
    "report_rpbm_ordre_reparation_vehicule": {
        "//span[@t-field='doc.x_studio_marque__1']",
        "//span[@t-field='doc.x_studio_modle_']",
    },
    "report_rpbm_or_vehicule": {
        "//span[@t-field='doc.x_studio_marque__1']",
        "//span[@t-field='doc.x_studio_modle_']",
    },
}


class TestSaleOrderReportViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.source = VIEW_PATH.read_text(encoding="utf-8")
        cls.root = ElementTree.fromstring(cls.source)
        cls.templates = {tpl.get("id"): tpl for tpl in cls.root.iter("template")}

    def test_file_is_declared_in_the_manifest(self):
        manifest = (ROOT / "__manifest__.py").read_text(encoding="utf-8")
        self.assertIn('"views/sale_order_report_views.xml"', manifest)

    def test_each_report_extends_its_expected_studio_view(self):
        self.assertEqual(set(self.templates), set(EXPECTED_INHERITS))
        for tpl_id, xml_id in EXPECTED_INHERITS.items():
            template = self.templates[tpl_id]
            self.assertEqual(template.get("inherit_id"), xml_id)
            # priorite superieure a celle des personnalisations Studio (99) :
            # la couche module doit s'appliquer en dernier.
            self.assertEqual(template.get("priority"), "110")

    def test_every_report_shows_the_carrier_once_with_its_historical_fallback(self):
        for tpl_id, template in self.templates.items():
            blocks = [
                node for node in template.iter("div")
                if node.get("name") == "rpbm_carrier"
            ]
            self.assertEqual(len(blocks), 1, tpl_id)
            block = blocks[0]
            conditions = [
                node.get("t-if") or node.get("t-elif")
                for node in block.iter()
                if node.get("t-if") or node.get("t-elif")
            ]
            self.assertIn("doc.carrier_id", conditions, tpl_id)
            self.assertIn(
                "doc.opportunity_id.rpbm_intervention_location", conditions, tpl_id
            )
            fields = {node.get("t-field") for node in block.iter()}
            self.assertIn("doc.carrier_id", fields, tpl_id)
            self.assertIn(
                "doc.opportunity_id.rpbm_intervention_location", fields, tpl_id
            )

    def test_only_the_two_duplicate_brand_and_model_displays_are_removed(self):
        for tpl_id, template in self.templates.items():
            removed = {
                spec.get("expr") for spec in template.iter("xpath")
                if spec.get("position") == "replace" and len(spec) == 0
            }
            self.assertEqual(removed, EXPECTED_REMOVALS.get(tpl_id, set()), tpl_id)

    def _expressions(self):
        """Toutes les expressions executables du fichier (hors commentaires)."""
        values = set()
        for template in self.root.iter("template"):
            for node in template.iter():
                for attribute in ("expr", "t-field", "t-out", "t-if", "t-elif"):
                    value = node.get(attribute)
                    if value:
                        values.add(value)
        return values

    def test_kilometrage_and_insurance_location_are_left_untouched(self):
        # AG01-F05 n'est pas tranche cote metier : aucune des deux variantes de
        # kilometrage ne doit etre retiree ni substituee par ce lot. Le lieu du
        # sinistre assurance de 1591 est hors perimetre logistique.
        expressions = self._expressions()
        for name in (
            "x_studio_kilomtrage__1",
            "x_studio_kilomtrage_1",
            "x_studio_lieu_de_sinistre_",
            "x_studio_lieu_sinistre_",
        ):
            matches = sorted(expr for expr in expressions if name in expr)
            self.assertEqual(matches, [], name)

    def test_no_studio_view_is_replaced_wholesale(self):
        # La contrainte AG-01 interdit toute suppression de champ Studio : les
        # seules operations autorisees sont l'insertion et le retrait cible des
        # deux spans en double.
        for template in self.root.iter("template"):
            for spec in template.iter("xpath"):
                self.assertIn(spec.get("position"), ("after", "replace"))
                if spec.get("position") == "replace":
                    self.assertEqual(len(spec), 0)
