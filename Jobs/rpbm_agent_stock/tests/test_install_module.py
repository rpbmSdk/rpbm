"""Verification hors ligne de la logique de branchement d'install_module.py.

Aucun reseau, aucun Odoo reel : un faux client Odoo simule les etats possibles
(absent / uninstalled / installed) pour verifier que check_state()/run() prennent
la bonne branche. A lancer avant tout --commit reel, comme le selfcheck de
Jobs/Gestion Stock/import_odoo.py.

    pyenv exec python tests/test_install_module.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import install_module  # noqa: E402


class FakeOdoo:
    """Simule juste assez de common.Odoo pour tester le branchement, sans XML-RPC."""

    def __init__(self, states: list[dict], commit: bool = False):
        self._states = states
        self.commit = commit
        self.calls: list[tuple] = []

    def search_read(self, model, domain, fields):
        return self._states

    def call(self, model, method, ids, *args, label="", **kwargs):
        self.calls.append((model, method, ids))
        return True

    def field_names(self, model):
        return {"x_studio_eurocode"} if self.commit else set()

    def resolve_id(self, model, domain, label):
        return 42


def test_absent_triggers_update_list_dry_run() -> None:
    odoo = FakeOdoo(states=[])
    install_module.run(odoo)
    assert ("ir.module.module", "update_list", None) in odoo.calls, \
        "un module absent doit declencher update_list() meme en dry-run (log de l'intention)"


def test_installed_is_noop() -> None:
    odoo = FakeOdoo(states=[{"id": 1, "state": "installed", "latest_version": "17.0.1"}], commit=True)
    result = install_module.run(odoo)
    assert not any(call[1] == "button_immediate_install" for call in odoo.calls), \
        "un module deja installe ne doit jamais redeclencher button_immediate_install"
    assert result == 0


def test_uninstalled_triggers_install() -> None:
    odoo = FakeOdoo(states=[{"id": 1, "state": "uninstalled", "latest_version": "17.0.1"}], commit=True)
    install_module.run(odoo)
    assert any(call[1] == "button_immediate_install" for call in odoo.calls), \
        "un module uninstalled doit declencher button_immediate_install"


def main() -> None:
    test_absent_triggers_update_list_dry_run()
    test_installed_is_noop()
    test_uninstalled_triggers_install()
    print("test_install_module : OK (3 scenarios)")


if __name__ == "__main__":
    main()
