"""Verification hors ligne de studio_views.py.

Aucun reseau, aucun Odoo reel : un faux client renvoie une arch combinee figee (brute ou deja
patchee) et enregistre les ecritures. A lancer avant tout --commit reel.

    python tests/test_studio_views.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import studio_views  # noqa: E402

LABELS = {"x_old": {"string": "Immatriculation"}, "rpbm_new": {"string": "Plaque"}}
# Le natif present dans l'onglet module ne compte pas : le bloc reste a ajouter.
RAW = ('<form><sheet><group name="g"><field name="x_old"/></group>'
       '<notebook><page name="rpbm_agent_xglass"><field name="rpbm_new"/></page></notebook></sheet></form>')
PATCHED = ('<form><sheet><group name="g"><field name="rpbm_new" string="Plaque"/><field name="x_old" string="Immatriculation (ancien)"/></group>'
           '<notebook><page name="rpbm_agent_xglass"><field name="rpbm_new"/></page></notebook></sheet></form>')
SPEC = studio_views.Spec("mod.view", "form", [
    studio_views.before("x_old", ("rpbm_new", "Plaque")),
    studio_views.ancien("field", "x_old"),
])


class FakeOdoo:
    """Juste assez de common.Odoo : une vue de base 10, sa vue Studio 20, une arch combinee figee."""

    url, db, profile = "http://fake", "fake-test", "fake"

    def __init__(self, combined: str = RAW, arch_db: str = "<data>\n</data>", commit: bool = False):
        self.combined, self.arch_db, self.commit = combined, arch_db, commit
        self.writes: list = []

    def search_read(self, model, domain, fields, limit=0):
        return [{"res_id": 10}]

    def execute(self, model, method, *args, **kwargs):
        if method == "read":
            if args[1] == ["arch_db"]:
                return [{"id": args[0][0], "arch_db": self.arch_db}]
            return [{"id": 10, "name": "base", "model": "crm.lead", "mode": "primary"}]
        if method == "search_read":
            return [{"id": 20}]
        if method == "fields_get":
            return LABELS
        if method == "get_views":
            return {"views": {args[0][0][1]: {"arch": self.combined}}}
        if method == "write":
            self.writes.append(args)
            self.arch_db = args[1]["arch_db"]
            return True
        raise AssertionError(f"appel inattendu {model}.{method}")


def test_module_page_and_subviews_do_not_count() -> None:
    labels = {name: value["string"] for name, value in LABELS.items()}
    assert studio_views.Arch(RAW, labels).find("field", "rpbm_new") is None, "l'onglet module ne compte pas"
    assert not SPEC.items[0].check(studio_views.Arch(RAW, labels))
    inline = '<form><field name="line_ids"><tree><field name="rpbm_new"/></tree></field></form>'
    assert studio_views.Arch(inline, labels).find("field", "rpbm_new") is None, "une sous-vue inline ne compte pas"


def test_dry_run_writes_nothing() -> None:
    odoo = FakeOdoo()
    studio_views.apply(odoo, "t1", [SPEC])
    assert not odoo.writes, "un dry-run ne doit rien ecrire"
    assert not studio_views.run_dir("t1").exists(), "un dry-run ne doit rien sauvegarder"


def test_second_apply_is_noop() -> None:
    odoo = FakeOdoo(combined=PATCHED, commit=True)
    assert studio_views.apply(odoo, "t2", [SPEC]) == 0
    assert not odoo.writes, "une arch deja patchee ne doit declencher aucune ecriture"


def test_label_from_fields_get_without_double_suffix() -> None:
    labels = {name: value["string"] for name, value in LABELS.items()}
    item = studio_views.ancien("field", "x_old", optional=True)
    block = item.block(studio_views.Arch('<tree><field name="x_old"/></tree>', labels))
    assert ">Immatriculation (ancien)<" in block and '<attribute name="optional">hide</attribute>' in block, block
    already = studio_views.Arch('<tree><field name="x_old" string="Immatriculation (ancien)"/></tree>', labels)
    assert not item.check(already), "optional=hide manquant : le controle doit echouer"
    assert "(ancien) (ancien)" not in item.block(already), "jamais de double suffixe"


TAB_SPEC = studio_views.Spec("mod.view", "form", [
    studio_views.before("x_old", ("rpbm_new", "Plaque")),
    studio_views.ancien("field", "x_old"),
] + studio_views.legacy_tab("p", ["x_old"], []))
TAB_RAW = '<form><sheet><group name="g"><field name="x_old"/></group><notebook><page name="p"/></notebook></sheet></form>'
# Natif reste a l'ancienne place, ancien champ deplace dans l'onglet « Anciens champs ».
TAB_DONE = ('<form><sheet><group name="g"><field name="rpbm_new" string="Plaque"/></group><notebook><page name="p"/>'
            '<page name="rpbm_legacy_fields"><group name="rpbm_legacy_fields_group">'
            '<group name="rpbm_legacy_left"><field name="x_old" string="Immatriculation (ancien)"/></group>'
            '<group name="rpbm_legacy_right"/></group></page></notebook></sheet></form>')


def test_legacy_tab_and_move() -> None:
    # L'onglet et le deplacement sont en attente dans le meme run : l'ancre creee par le bloc
    # precedent n'est pas un FAIL.
    odoo = FakeOdoo(combined=TAB_RAW)
    assert studio_views.apply(odoo, "t5", [TAB_SPEC]) == 0 and not odoo.writes
    labels = {name: value["string"] for name, value in LABELS.items()}
    assert all(item.check(studio_views.Arch(TAB_DONE, labels)) for item in TAB_SPEC.items), "natif, onglet, deplacement, suffixe"
    odoo = FakeOdoo(combined=TAB_DONE, commit=True)
    assert studio_views.apply(odoo, "t6", [TAB_SPEC]) == 0 and not odoo.writes, "deja deplace : rien a ecrire"


def test_rollback_refuses_when_arch_changed() -> None:
    folder = studio_views.run_dir("t4")
    folder.mkdir(parents=True)
    (folder / "20-avant.xml").write_text("<data>\n</data>", encoding="utf-8")
    (folder / "manifest.json").write_text(json.dumps({"views": [{
        "xmlid": "mod.view", "studio_id": 20, "backup": "20-avant.xml", "restored": False,
        "sha256_before": studio_views.sha("<data>\n</data>"), "sha256_after": studio_views.sha("<data>A</data>"),
    }]}), encoding="utf-8")
    odoo = FakeOdoo(arch_db="<data>B</data>", commit=True)
    assert studio_views.rollback(odoo, "t4") == 1
    assert not odoo.writes, "rollback doit refuser si l'arch a bouge depuis l'apply"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        studio_views.RUNS_DIR = Path(tmp)  # jamais dans runs/ versionne
        test_module_page_and_subviews_do_not_count()
        test_dry_run_writes_nothing()
        test_second_apply_is_noop()
        test_label_from_fields_get_without_double_suffix()
        test_legacy_tab_and_move()
        test_rollback_refuses_when_arch_changed()
    print("test_studio_views : OK (6 scenarios)")


if __name__ == "__main__":
    main()
