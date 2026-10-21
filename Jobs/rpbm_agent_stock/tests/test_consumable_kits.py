"""Verification hors ligne de consumable_kits.py.

Aucun reseau, aucun Odoo reel : un faux client garde articles, fournisseurs et nomenclatures en memoire, sait simuler
une coupure, et enregistre les ecritures. A lancer avant tout --commit reel.

    python tests/test_consumable_kits.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import consumable_kits as ck  # noqa: E402

M2O = {"product_tmpl_id", "product_id", "uom_id", "partner_id", "company_id"}


def product(pid, name, kind="consu", **extra):
    return {"id": pid, "default_code": "", "name": name, "detailed_type": kind, "product_tmpl_id": pid, "uom_id": 1,
            "nbr_reordering_rules": 0, "sale_ok": True, "active": True, **extra}


class FakeOdoo:
    """Juste assez de common.Odoo pour consumable_kits : search_read, read, read_group, create, unlink."""

    url, db, profile, uid = "http://fake", "fake-test", "fake", 2

    def __init__(self, commit: bool = False):
        self.commit, self.writes, self.next_id, self.fail = commit, [], 1000, None
        products = [product(13, "VITRAGE 1"), product(20, "Produits Connexes"), product(183, "FRANCHISE"),
                    product(174, "FILM Sécuritaire"),          # consommable avec fournisseur : pas de kit
                    product(60, "PIECE STOCK", "product"),     # stockable sans fournisseur : signale, pas de kit
                    product(9, "Nettoyage", "service"),
                    product(70, "NON VENDABLE", sale_ok=False),
                    product(72, "DEJA KIT")]
        self.tables = {
            "product.product": {p["id"]: p for p in products},
            "product.template": {p["id"]: {"id": p["id"], "product_variant_count": 1} for p in products},
            "product.supplierinfo": {1: {"id": 1, "partner_id": 7, "company_id": 1, "product_id": False, "product_tmpl_id": 174}},
            "res.partner": {7: {"id": 7, "active": True}},
            "res.users": {2: {"id": 2, "company_id": 1}},
            # 13 et 20 dans un modele actif, 183 seulement dans un modele archive
            "sale.order.template.line": {1: {"id": 1, "product_id": 13, "sale_order_template_id.active": True},
                                         2: {"id": 2, "product_id": 20, "sale_order_template_id.active": True},
                                         3: {"id": 3, "product_id": 183, "sale_order_template_id.active": False}},
            "mrp.bom": {500: {"id": 500, "type": "phantom", "product_tmpl_id": 72, "product_id": False, "code": "AUTRE",
                              "bom_line_ids": []}},
        }

    def _out(self, record, fields):
        return {"id": record["id"], **{f: ([record.get(f), str(record.get(f))] if record.get(f) else False) if f in M2O
                                        else record.get(f) for f in fields}}

    def _match(self, record, domain):
        for field, op, value in domain:
            current = record.get(field)
            if not {"=": current == value, "!=": current != value}.get(op, current in value if op == "in" else False):
                return False
        return True

    def execute(self, model, method, *args, fields=None, context=None, **kwargs):
        table = self.tables.get(model, {})
        if method == "search_read":
            return [self._out(r, fields) for r in table.values() if self._match(r, args[0])]
        if method == "read":
            return [self._out(table[i], args[1]) for i in args[0] if i in table]
        if method == "read_group":
            return []  # devis ouverts et modeles : hors du faux
        self.writes.append((model, method, args))
        assert self.commit, "ecriture en dry-run"
        calls = sum(1 for w in self.writes if w[:2] == (model, method))
        if self.fail and self.fail[:3] == (model, method, calls):
            if not self.fail[3]:
                raise ConnectionError("coupure avant l'ecriture")
            self.fail = None
            result = self.execute(model, method, *args, fields=fields, context=context, **kwargs)
            raise ConnectionError(f"reponse perdue apres l'ecriture ({result})")
        if method == "create":
            new = self.next_id
            self.next_id += 1
            table[new] = {"id": new, "product_id": False, "bom_line_ids": [], **args[0]}
            return new
        if method == "unlink":
            for i in args[0]:
                del table[i]
            return True
        if method == "write":
            for i in args[0]:
                table[i].update(args[1])
                if model == "product.template" and args[1].get("active") is False:
                    self.tables["product.product"][i]["active"] = False
            return True
        raise AssertionError(f"appel inattendu {model}.{method}")

    def kits(self):
        return {b["product_tmpl_id"]: b for b in self.tables["mrp.bom"].values() if b["code"] == ck.CODE}


def test_dry_run_writes_nothing() -> None:
    odoo = FakeOdoo()
    assert ck.apply(odoo, "t1") == 0
    assert not odoo.writes and not ck.run_dir("t1").exists()
    assert ck.check(odoo, "vendables") == 1, "avant l'apply, 3 consommables sans fournisseur ni kit"
    try:
        ck.apply(FakeOdoo(commit=True), "t1b")
        raise AssertionError("--commit sans perimetre accepte")
    except SystemExit:
        pass


def test_scope_templates() -> None:
    odoo = FakeOdoo(commit=True)
    assert ck.apply(odoo, "t8", "modeles") == 0
    assert set(odoo.kits()) == {13, 20}, "FRANCHISE (hors modele actif) non traite"
    assert ck.check(odoo, "modeles") == 0 and ck.check(odoo, "vendables") == 1


def test_apply_targets_only_consumables_without_supplier() -> None:
    odoo = FakeOdoo(commit=True)
    assert ck.apply(odoo, "t2", "vendables") == 0
    kits = odoo.kits()
    assert set(kits) == {13, 20, 183}, "ni le consommable avec fournisseur, ni le stockable, ni le service, ni le non vendable, ni le kit existant"
    bom = kits[13]
    assert bom["type"] == "phantom" and bom["product_qty"] == 1.0 and bom["product_uom_id"] == 1 and bom["company_id"] is False
    assert ck.check(odoo, "vendables") == 0
    done = len(odoo.writes)
    assert ck.apply(odoo, "t3", "vendables") == 0 and len(odoo.writes) == done, "un second apply ne doit rien ecrire"


def test_manual_cases_fail_before_writing() -> None:
    odoo = FakeOdoo(commit=True)
    odoo.tables["product.product"][183]["nbr_reordering_rules"] = 1
    odoo.tables["product.template"][20]["product_variant_count"] = 2
    assert ck.apply(odoo, "t4", "vendables") == 1, "regle de reapprovisionnement et variantes : FAIL"
    assert set(odoo.kits()) == {13}, "les autres sont traites, ces deux-la non"


def test_rollback_removes_only_created_kits() -> None:
    odoo = FakeOdoo(commit=True)
    ck.apply(odoo, "t5", "vendables")
    assert ck.rollback(odoo, "t5") == 0
    assert not odoo.kits() and 500 in odoo.tables["mrp.bom"], "le kit d'un autre (AUTRE) reste"
    done = len(odoo.writes)
    assert ck.rollback(odoo, "t5") == 0 and len(odoo.writes) == done, "second rollback : deja annule"


def test_rollback_keeps_modified_kit() -> None:
    odoo = FakeOdoo(commit=True)
    ck.apply(odoo, "t6", "vendables")
    odoo.kits()[20]["bom_line_ids"] = [99]  # composant ajoute a la main depuis
    assert ck.rollback(odoo, "t6") == 1
    assert set(odoo.kits()) == {20}, "seul le kit modifie reste"


def test_interrupted_apply_then_rollback() -> None:
    for after_write in (False, True):  # coupure avant la creation, ou reponse perdue apres une creation validee
        odoo = FakeOdoo(commit=True)
        odoo.fail = ("mrp.bom", "create", 2, after_write)
        try:
            ck.apply(odoo, f"t7-{after_write}", "vendables")
            raise AssertionError("coupure non propagee")
        except ConnectionError:
            pass
        assert ck.rollback(odoo, f"t7-{after_write}") == 0
        assert not odoo.kits(), f"kit orphelin (apres ecriture : {after_write})"


def test_scope_used() -> None:
    real_history = ck.history
    ck.history = lambda o, ids, since: {pid: {"sales": 0, "invoices": 2 if pid == 183 else 0, "open": 0, "last": "2026-07-15"}
                                        for pid in ids}
    try:
        odoo = FakeOdoo(commit=True)
        odoo.tables["product.product"][184] = product(184, "LOYER")
        odoo.tables["product.template"][184] = {"id": 184, "product_variant_count": 1}
        assert ck.apply(odoo, "t12", "utilises") == 0
        assert set(odoo.kits()) == {13, 20, 183}, "modeles + FRANCHISE (factures) ; LOYER inutilise, sans kit"
        assert ck.check(odoo, "utilises") == 0 and ck.check(odoo, "vendables") == 1
        assert ck.archive(odoo, "t13") == 0
        archived = {w[2][0][0] for w in odoo.writes if w[:2] == ("product.template", "write")}
        assert archived == {184}, "apres les kits, seul LOYER reste a archiver"
    finally:
        ck.history = real_history


def test_archive_outside_templates() -> None:
    odoo = FakeOdoo()
    assert ck.archive(odoo, "t9") == 0 and not odoo.writes, "simulation : aucune ecriture"
    real_history = ck.history
    ck.history = lambda o, ids, since: {pid: {"sales": 0, "invoices": 3 if pid == 183 else 0, "open": 0, "last": "2026-10-01"}
                                        for pid in ids}
    try:
        odoo = FakeOdoo(commit=True)
        odoo.tables["product.product"][184] = product(184, "LOYER")
        odoo.tables["product.template"][184] = {"id": 184, "product_variant_count": 1}
        assert ck.archive(odoo, "t10") == 0
        archived = {w[2][0][0] for w in odoo.writes if w[:2] == ("product.template", "write")}
        assert archived == {184}, "seul l'article inutilise est archive ; FRANCHISE (factures) garde sans --avec-utilises"
        assert ck.rollback(odoo, "t10") == 0
        assert odoo.tables["product.product"][184]["active"], "rollback : desarchive"
        assert ck.archive(FakeOdoo(commit=True), "t11", with_used=True) == 0
    finally:
        ck.history = real_history


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ck.RUNS_DIR = Path(tmp)  # jamais dans runs/ versionne
        tests = [test_dry_run_writes_nothing, test_scope_templates, test_apply_targets_only_consumables_without_supplier,
                 test_manual_cases_fail_before_writing, test_rollback_removes_only_created_kits,
                 test_rollback_keeps_modified_kit, test_interrupted_apply_then_rollback, test_archive_outside_templates, test_scope_used]
        for test in tests:
            test()
    print(f"test_consumable_kits : OK ({len(tests)} scenarios)")


if __name__ == "__main__":
    main()
