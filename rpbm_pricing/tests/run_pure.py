"""Tests purs sans Odoo : ``python3 -I rpbm_pricing/tests/run_pure.py``.

Charge chaque ``tests/test_*_pure.py`` présent par son chemin (le paquet ``tests`` importe Odoo),
avec ``rpbm_pricing/`` dans ``sys.path`` pour ``from lib import ...``.
"""
import importlib.util
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR.parent))

suite = unittest.TestSuite()
for path in sorted(TESTS_DIR.glob("test_*_pure.py")):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))

result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() and result.testsRun else 1)
