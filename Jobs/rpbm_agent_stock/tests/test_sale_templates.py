"""Verification hors ligne de sale_templates.py.

Aucun reseau, aucun Odoo reel : un faux client garde quelques tables en memoire (articles, modeles,
lignes, fournisseurs) et enregistre les ecritures. A lancer avant tout --commit reel.

    python tests/test_sale_templates.py
"""

from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sale_templates as st  # noqa: E402

M2O = {"product_tmpl_id", "sale_order_template_id", "product_id", "product_uom_id", "partner_id", "company_id",
       "categ_id", "uom_id", "uom_po_id", "product_variant_id"}
DECISIONS = set(st.DECISIONS)


def product(pid, code, kind="consu", **extra):
    return {"id": pid, "default_code": code, "name": code, "product_tmpl_id": pid, "detailed_type": kind, "active": True,
            "list_price": 9.0, "taxes_id": [3], "categ_id": 11, "invoice_policy": "order", "uom_id": 1, "uom_po_id": 1, **extra}


def line(lid, template, product_id, qty, display_type=False, name=""):
    return {"id": lid, "sale_order_template_id": template, "sequence": lid, "display_type": display_type,
            "name": name or f"article {product_id}", "product_id": product_id, "product_uom_qty": qty,
            "product_uom_id": product_id and 1}


class FakeOdoo:
    """Juste assez de common.Odoo pour sale_templates : read, search_read, search_count, create, write, unlink."""

    url, db, profile, uid = "http://fake", "fake-test", "fake", 2

    def __init__(self, commit: bool = False):
        self.commit, self.writes, self.next_id = commit, [], 1000
        self.fail = None  # (model, method, n-ieme appel, apres_ecriture) : coupure simulee
        services = {9, 46, 32}
        products = {pid: product(pid, code, "service" if pid in services else "consu") for pid, code in st.REFERENCES.items()}
        products[21] = product(21, "Kit Collage Sika 400 ml", "product")  # stockable avec fournisseur : ne bloque pas
        products[9] = product(9, "Nettoyage Bris de Glace", "service")
        self.tables = {
            "product.product": products,
            "product.template": {pid: {"id": pid, "active": True} for pid in products},
            "sale.order.template": {1: {"id": 1, "name": "Pare Brise V", "active": True},
                                    2: {"id": 2, "name": "Archive", "active": False}},
            "sale.order.template.line": {r["id"]: r for r in [
                line(1, 1, False, 0, "line_section", "Pièces"), line(2, 1, 13, 1), line(3, 1, 17, 0),
                line(4, 1, 20, 1, name="[Produits Connexes] Produits Connexes"), line(5, 1, 21, 1), line(6, 1, 19, 0),
                line(7, 1, 43, 1), line(8, 1, 9, 1), line(9, 1, False, 0, "line_section", "Pose à domicile"), line(10, 1, 46, 0),
                line(11, 2, 13, 1),  # modele archive : jamais touche
            ]},
            "product.supplierinfo": {1: {"id": 1, "partner_id": 7, "company_id": 1, "product_id": False, "product_tmpl_id": 21}},
            "res.partner": {7: {"id": 7, "active": True}},
            "res.users": {2: {"id": 2, "company_id": 1}},
        }

    def _out(self, record, fields):
        return {"id": record["id"], **{f: ([record.get(f), str(record.get(f))] if record.get(f) else False) if f in M2O
                                        else record.get(f) for f in fields}}

    def _match(self, record, domain, context):
        if "active" in record and (context or {}).get("active_test", True) and not any(c[0] == "active" for c in domain):
            if not record["active"]:
                return False
        for field, op, value in domain:
            if field == "product_tmpl_id" and "product_tmpl_id" not in record:
                return False
            if field == "sale_order_template_id.active":
                current = self.tables["sale.order.template"][record["sale_order_template_id"]]["active"]
            else:
                current = record.get(field)
            if not (current == value if op == "=" else current in value):
                return False
        return True

    def execute(self, model, method, *args, fields=None, context=None, order=None, **kwargs):
        table = self.tables.get(model, {})
        if method == "read":
            ids, names = args
            if model == "product.template" and names == ["product_variant_id"]:
                return [{"id": i, "product_variant_id": [i, "variante"]} for i in ids]
            return [self._out(table[i], names) for i in ids if i in table]
        if method == "search_read":
            return [self._out(r, fields) for r in table.values() if self._match(r, args[0], context)]
        if method == "search_count":
            return sum(1 for r in table.values() if self._match(r, args[0], context))
        self.writes.append((model, method, args))
        assert self.commit, "ecriture en dry-run"
        calls = sum(1 for w in self.writes if w[:2] == (model, method))
        if self.fail and self.fail[:3] == (model, method, calls):
            if not self.fail[3]:
                raise ConnectionError("coupure avant l'ecriture")
            self.fail = None
            result = self.execute(model, method, *args, fields=fields, context=context, order=order, **kwargs)
            raise ConnectionError(f"reponse perdue apres l'ecriture ({result})")
        if method == "create":
            vals, new = dict(args[0]), self.next_id
            self.next_id += 1
            if model == "product.template":
                table[new] = {"id": new, "active": True}
                self.tables["product.product"][new] = product(new, vals["default_code"], vals["detailed_type"])
            else:
                table[new] = {"id": new, **vals}
            return new
        if method == "write":
            for i in args[0]:
                table[i].update(args[1])
                if model == "product.template" and args[1].get("active") is False:
                    self.tables["product.product"][i]["active"] = False  # comme Odoo : l'archivage descend aux variantes
            return True
        if method == "unlink":
            for i in args[0]:
                del table[i]
            return True
        raise AssertionError(f"appel inattendu {model}.{method}")

    def lines(self, template):
        return st.read_lines(self, [template])


def test_dry_run_writes_nothing_and_fails_without_decisions() -> None:
    odoo = FakeOdoo()
    assert st.apply(odoo, "t1", set()) == 1, "Produits Connexes et le film restent bloquants sans decision"
    assert not odoo.writes and not st.run_dir("t1").exists()


def test_apply_then_second_apply_is_noop() -> None:
    odoo = FakeOdoo(commit=True)
    assert st.apply(odoo, "t2", DECISIONS) == 0
    products = {l["product"]: l for l in odoo.lines(1)}
    assert not {13, 17, 19, 46} & set(products), "generiques, gel et pose a domicile retires"
    assert not any(l["name"] == "Pose à domicile" for l in odoo.lines(1)), "section Pose a domicile retiree"
    service = next(pid for pid, p in odoo.tables["product.product"].items() if p["default_code"] == st.SERVICE_CODE)
    assert products[service]["name"] == "[Produits Connexes] Produits Connexes", "libelle client inchange"
    assert products[43]["qty"] == 0 and {21, 9} <= set(products)
    assert [l["product"] for l in odoo.lines(2)] == [13], "modele archive intact"
    assert not odoo.tables["product.template"][13]["active"] and not odoo.tables["product.template"][20]["active"]
    assert odoo.tables["product.template"][9]["active"], "l'article 9 n'est jamais archive"
    done = len(odoo.writes)
    assert st.apply(odoo, "t3", DECISIONS) == 0
    assert len(odoo.writes) == done, "un second apply ne doit rien ecrire"


def test_rollback_restores_snapshot() -> None:
    odoo = FakeOdoo(commit=True)
    before = st.signature(odoo.lines(1))
    st.apply(odoo, "t4", DECISIONS)
    assert st.rollback(odoo, "t4") == 0
    assert st.signature(odoo.lines(1)) == before
    assert odoo.tables["product.template"][13]["active"] and odoo.tables["product.product"][13]["active"]
    service = next(p for p in odoo.tables["product.product"].values() if p["default_code"] == st.SERVICE_CODE)
    assert not odoo.tables["product.template"][service["id"]]["active"], "service cree archive"
    done = len(odoo.writes)
    assert st.rollback(odoo, "t4") == 0 and len(odoo.writes) == done, "second rollback : deja annule"


def test_rollback_refused_after_template_edit() -> None:
    odoo = FakeOdoo(commit=True)
    st.apply(odoo, "t5", DECISIONS)
    odoo.tables["sale.order.template.line"][5]["product_uom_qty"] = 2  # edition apres l'apply
    done = len(odoo.writes)
    assert st.rollback(odoo, "t5") == 1 and len(odoo.writes) == done


def test_stops_before_any_write() -> None:
    odoo = FakeOdoo(commit=True)
    for pid in (900, 901):
        odoo.tables["product.product"][pid] = product(pid, st.SERVICE_CODE, "service")
    try:
        st.apply(odoo, "t6", DECISIONS)
        raise AssertionError("cle PC-FORFAIT ambigue non detectee")
    except SystemExit:
        pass
    assert not odoo.writes and not st.run_dir("t6").exists()
    odoo = FakeOdoo(commit=True)
    odoo.tables["product.product"][13]["default_code"] = "AUTRE"
    try:
        st.apply(odoo, "t7", set())
        raise AssertionError("article de reference inattendu non detecte")
    except SystemExit:
        pass
    assert not odoo.writes and not st.run_dir("t7").exists()


def test_existing_service_reused_and_reapply_after_rollback() -> None:
    odoo = FakeOdoo(commit=True)
    odoo.tables["product.product"][900] = product(900, st.SERVICE_CODE, "service")
    odoo.tables["product.template"][900] = {"id": 900, "active": True}
    assert st.apply(odoo, "t8", {"produits-connexes", "films-qte-zero"}) == 0
    assert not any(w[:2] == ("product.template", "create") for w in odoo.writes), "PC-FORFAIT existant reutilise"
    assert 900 in {l["product"] for l in odoo.lines(1)}
    assert st.rollback(odoo, "t8") == 0 and odoo.tables["product.template"][900]["active"], "service non cree par le run : laisse actif"

    odoo = FakeOdoo(commit=True)
    st.apply(odoo, "t9", {"produits-connexes", "films-qte-zero"})
    st.rollback(odoo, "t9")  # archive le service cree
    assert st.apply(odoo, "t10", {"produits-connexes", "films-qte-zero"}) == 0, "un nouvel apply desarchive le service"
    services = [p for p in odoo.tables["product.product"].values() if p["default_code"] == st.SERVICE_CODE]
    assert len(services) == 1 and services[0]["active"]
    assert st.rollback(odoo, "t10") == 0 and not services[0]["active"]


def test_interrupted_apply_is_rolled_back() -> None:
    for after_write in (False, True):  # coupure avant l'ecriture, ou reponse perdue apres une ecriture validee
        odoo = FakeOdoo(commit=True)
        before = st.signature(odoo.lines(1))
        odoo.fail = ("sale.order.template.line", "unlink", 2, after_write)
        try:
            st.apply(odoo, f"t11-{after_write}", DECISIONS)
            raise AssertionError("coupure non propagee")
        except ConnectionError:
            pass
        assert st.rollback(odoo, f"t11-{after_write}") == 0
        assert st.signature(odoo.lines(1)) == before, f"instantane non restaure (apres ecriture : {after_write})"
        service = next(p for p in odoo.tables["product.product"].values() if p["default_code"] == st.SERVICE_CODE)
        assert not service["active"]


def test_interrupted_rollback_resumes() -> None:
    for after_write in (False, True):
        odoo = FakeOdoo(commit=True)
        before = st.signature(odoo.lines(1))
        st.apply(odoo, f"t12-{after_write}", DECISIONS)
        odoo.fail = ("sale.order.template.line", "create", 2, after_write)
        try:
            st.rollback(odoo, f"t12-{after_write}")
            raise AssertionError("coupure non propagee")
        except ConnectionError:
            pass
        assert st.rollback(odoo, f"t12-{after_write}") == 0, "la reprise ne doit pas prendre ses propres recreations pour une edition"
        assert st.signature(odoo.lines(1)) == before, f"ligne manquante ou en double (apres ecriture : {after_write})"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        st.RUNS_DIR = Path(tmp)  # jamais dans runs/ versionne
        tests = [test_dry_run_writes_nothing_and_fails_without_decisions, test_apply_then_second_apply_is_noop,
                 test_rollback_restores_snapshot, test_rollback_refused_after_template_edit, test_stops_before_any_write,
                 test_existing_service_reused_and_reapply_after_rollback, test_interrupted_apply_is_rolled_back,
                 test_interrupted_rollback_resumes]
        for test in tests:
            test()
    print(f"test_sale_templates : OK ({len(tests)} scenarios)")


if __name__ == "__main__":
    main()
