"""Expose les tests standalone de test_portal_auth.py au lanceur de tests Odoo.

Les tests eux-mêmes restent dans test_portal_auth.py pour rester exécutables
sans Odoo (`python test_portal_auth.py`, voir CLAUDE.md du module).
"""
from unittest import TestCase

from .. import test_portal_auth


class TestPortalParsing(TestCase):
    pass


for _name in dir(test_portal_auth):
    if _name.startswith("test_"):
        setattr(TestPortalParsing, _name, staticmethod(getattr(test_portal_auth, _name)))
