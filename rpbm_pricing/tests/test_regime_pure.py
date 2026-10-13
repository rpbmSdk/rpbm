"""Régime du dossier et du modèle de devis, sans base."""
try:
    from odoo.tests.common import BaseCase as TestCase
    from odoo.addons.rpbm_pricing.lib import regime
except ImportError:
    from unittest import TestCase
    from lib import regime


class TestRegimePure(TestCase):
    def test_dossier_regime(self):
        self.assertIsNone(regime.dossier_regime(False, False))
        self.assertIsNone(regime.dossier_regime(False, True))
        self.assertEqual(regime.dossier_regime(True, True), regime.INSURANCE)
        self.assertEqual(regime.dossier_regime(True, False), regime.PRIVATE)

    def test_template_regime_on_real_names(self):
        # Noms de la préprod normalisés par rpbm_agent (lus le 2026-10-12).
        for name in ("pare brise v", "lunette arriere", "glace mobile", "glace fixe", "reglage adas (assurance)"):
            self.assertEqual(regime.template_regime(name), regime.INSURANCE, name)
        for name in ("pare-brise hors assurance", "lunette hors assurance", "glace hors assurance"):
            self.assertEqual(regime.template_regime(name), regime.PRIVATE, name)
        for name in ("pare brise avec bandeau", "lunette arriere chauffante", "film securitaire", "", None):
            self.assertIsNone(regime.template_regime(name), name)

    def test_divergence_only_when_both_known_and_different(self):
        self.assertEqual(regime.warnings(regime.PRIVATE, regime.INSURANCE, False),
                         ["Le modèle de devis est « Hors assurance », le dossier est « Assurance »."])
        self.assertEqual(regime.warnings(regime.INSURANCE, regime.INSURANCE, False), [])
        self.assertEqual(regime.warnings(None, regime.INSURANCE, False), [])
        self.assertEqual(regime.warnings(regime.INSURANCE, None, True), [])

    def test_xglass_labor_on_private_dossier(self):
        self.assertEqual(len(regime.warnings(None, regime.PRIVATE, True)), 1)
        self.assertIn("Main-d'œuvre X'Glass", regime.warnings(None, regime.PRIVATE, True)[0])
        self.assertEqual(regime.warnings(None, regime.PRIVATE, False), [])
        self.assertEqual(regime.warnings(regime.INSURANCE, regime.INSURANCE, True), [])
        self.assertEqual(len(regime.warnings(regime.INSURANCE, regime.PRIVATE, True)), 2)
