"""Aligne les vues Studio sur les champs natifs rpbm_* (bouton, champs natifs, libelles « (ancien) »).

    python studio_views.py apply [--commit] [--run <id>] [--profile ...] [--url ...] [--db ...] [--i-understand-this-is-production]
    python studio_views.py rollback --run <id> [--commit] [--profile ...] [--url ...] [--db ...] [--i-understand-this-is-production]

Une vue module ne doit pas viser un noeud cree par Studio (cible disparue = formulaire casse) : ce
script ajoute donc des blocs <xpath> en fin d'arch des vues Studio, que Studio conserve ensuite.
Chaque patch est un couple (controle, bloc) : le controle verifie l'effet A SA PLACE dans l'arch
combinee (get_views fr_FR), et seuls les blocs dont le controle echoue sont ajoutes. Idempotence
jugee patch par patch, cote client ; jamais de domaine ilike sur arch_db.

Apres ecriture : controles rejoues + get_views en mode Studio (strict : leve si une ancre est
introuvable, web_studio/models/ir_ui_view.py) ; en cas d'echec la sauvegarde est restauree.
Sauvegardes et manifeste dans runs/<run>-studio-views/ ; rollback ne restaure que si l'arch n'a
pas bouge depuis l'apply (sha256).

Fermer toute session Studio avant --commit : un editeur ouvert avant l'apply reecrit son
instantane au prochain enregistrement. Rejouer apply apres chaque reconstruction de l'instance,
et lancer rollback avant de desinstaller rpbm_agent ou de renommer un champ rpbm_*.

Connexion : profil paradigme-mcp-local ; URL du build (https://<base>.dev.odoo.com), jamais
l'alias de branche -- --url obligatoire hors Odoo.sh dev/staging (production).
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
import xmlrpc.client
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, NamedTuple
from xml.sax.saxutils import escape

from common import Odoo, load_profile
from recette_widget import Report, build_url

ROOT = Path(__file__).resolve().parents[2]
LEGACY_PATH = ROOT / "rpbm_agent" / "models" / "legacy_fields.py"
RUNS_DIR = Path(__file__).resolve().parent / "runs"
FR = {"lang": "fr_FR"}  # seule langue active : en_US est aligne par Odoo
MODULE_PAGE = "rpbm_agent_xglass"  # onglet du module : contient deja les champs natifs, ne compte pas
SUFFIX = " (ancien)"


def legacy_fields(model: str) -> list[str]:
    """Champs Studio de LEGACY_FIELDS (rpbm_agent/models/legacy_fields.py), lus sans importer odoo."""
    tree = ast.parse(LEGACY_PATH.read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", None) == "LEGACY_FIELDS")
    return [studio for studio, _ in ast.literal_eval(node.value)[model].values()]


class Arch:
    """Arch combinee parsee (xml.etree + table des parents). Les noeuds sous un <field> (sous-vues
    inline) ou dans l'onglet module sont ignores."""

    def __init__(self, xml: str, labels: dict[str, str]) -> None:
        self.root = ET.fromstring(xml)
        self.parent = {child: node for node in self.root.iter() for child in node}
        self.labels = labels  # fields_get fr_FR : libelles et champs existants du modele

    def find(self, tag: str, name: str):
        """Premier noeud visible, dans l'ordre du document : celui que vise l'xpath du bloc."""
        return next((node for node in self.root.iter(tag) if node.get("name") == name and not self._ignored(node)), None)

    def _ignored(self, node) -> bool:
        while (node := self.parent.get(node)) is not None:
            if node.tag == "field" or (node.tag == "page" and node.get("name") == MODULE_PAGE):
                return True
        return False


class Item(NamedTuple):
    label: str
    anchor: tuple[str, str]  # (balise, @name) vise par l'xpath
    position: str
    content: Callable[[Arch], str]
    check: Callable[[Arch], bool]
    nodes: tuple = ()  # noeuds rpbm_* de premier niveau ajoutes par le bloc
    fields: frozenset = frozenset()  # champs natifs que le bloc reference

    def block(self, arch: Arch) -> str:
        tag, name = self.anchor
        return f"<xpath expr=\"//{tag}[@name='{name}'][not(ancestor::field)]\" position=\"{self.position}\">{self.content(arch)}</xpath>"


class Spec(NamedTuple):
    xmlid: str  # vue de base (primaire) ; la vue Studio en est deduite
    view_type: str
    items: list[Item]
    natives: tuple = ()  # champs natifs deja attendus dans l'arch (colonnes/recherches du module)


def placed(position: str, anchor_tag: str, anchor: str, xml: str) -> Item:
    """Noeuds natifs `xml` places avant/apres/dans l'ancre, controles a leur place exacte."""
    top = ET.fromstring(f"<x>{xml}</x>")
    # ponytail: controle des noeuds de premier niveau seulement ; un champ retire ensuite d'un
    # groupe rpbm_* dans Studio n'est pas rajoute (il faudrait fusionner dans le groupe existant).
    nodes = tuple((node.tag, node.get("name")) for node in top)

    def check(arch: Arch) -> bool:
        target, found = arch.find(anchor_tag, anchor), [arch.find(*node) for node in nodes]
        if target is None or any(node is None for node in found):
            return False
        if position == "inside":
            return all(arch.parent.get(node) is target for node in found)
        siblings = list(arch.parent[target])
        i = siblings.index(target)
        around = siblings[max(0, i - len(found)):i] if position == "before" else siblings[i + 1:i + 1 + len(found)]
        return len(around) == len(found) and all(a is b for a, b in zip(around, found))

    return Item("+".join(name for _, name in nodes), (anchor_tag, anchor), position, lambda arch: xml, check,
                nodes, frozenset(node.get("name") for node in top.iter("field")))


def ancien(tag: str, name: str, optional: bool = False) -> Item:
    """Libelle du noeud (sinon fields_get) + « (ancien) », sans double suffixe ; listes : masque."""
    def text(arch: Arch) -> str:
        node = arch.find(tag, name)
        return (node.get("string") if node is not None else None) or arch.labels.get(name, name)

    def check(arch: Arch) -> bool:
        node = arch.find(tag, name)
        return node is not None and text(arch).endswith(SUFFIX) and (not optional or node.get("optional") == "hide")

    def content(arch: Arch) -> str:
        label = text(arch) if text(arch).endswith(SUFFIX) else text(arch) + SUFFIX
        return f'<attribute name="string">{escape(label)}</attribute>' + ('<attribute name="optional">hide</attribute>' if optional else "")

    return Item(f"{name}{SUFFIX}", (tag, name), "attributes", content, check)


def fields_xml(*fields: tuple[str, str]) -> str:
    return "".join(f'<field name="{name}" string="{label}"/>' for name, label in fields)


def before(anchor: str, *fields: tuple[str, str]) -> Item:
    return placed("before", "field", anchor, fields_xml(*fields))


# Libelles repris de Studio, pour que le natif se lise comme l'ancien champ qu'il double.
WIDGET = '<widget name="rpbm_agent_widget" colspan="2"/>'
VEHICLE_LEFT = [("rpbm_license_plate", "Immatriculation"), ("rpbm_vehicle_brand_id", "Marque"), ("rpbm_vehicle_model_id", "Modèle"),
                ("rpbm_vehicle_detail_model", "Détails Modèle"), ("rpbm_vehicle_id", "Véhicule (Flotte)")]
VEHICLE_RIGHT = [("rpbm_first_registration_date", "Date 1ère MEC"), ("rpbm_fuel_type", "Énergie Moteur"),
                 ("rpbm_eurocode_base", "Base Eurocode"), ("rpbm_vin", "VIN")]


def vehicle_group(attrs: str = "", left_head: str = "") -> str:
    return (f'<group name="rpbm_vehicle_native"{attrs}><group name="rpbm_vehicle_native_left">{left_head}{fields_xml(*VEHICLE_LEFT)}</group>'
            f'<group name="rpbm_vehicle_native_right">{fields_xml(*VEHICLE_RIGHT)}</group></group>')


VIEWS = [
    Spec("crm.crm_lead_view_form", "form", [
        placed("inside", "group", "studio_group_09urJ_left", WIDGET),
        placed("before", "group", "studio_group_GVpfN", vehicle_group()),
        before("x_studio_field_eENQz", ("rpbm_part_type", "Pièce concernée"), ("rpbm_xglass_category", "Catégorie X'Glass")),
        before("x_studio_field_NwRik", ("rpbm_eurocode", "Eurocode (Complet)")),
        before("x_studio_field_j8eh3", ("rpbm_vsf_designation", "VSF - Désignation")),
        before("x_studio_field_BKtpw", ("rpbm_vsf_stock", "VSF - Qté Dispo")),
        before("x_studio_field_MNzfJ", ("rpbm_constructor_reference", "Code Constructeur")),
        before("x_studio_lieu_intervention", ("rpbm_intervention_location", "Lieu Intervention")),
    ] + [ancien("field", name) for name in legacy_fields("crm.lead")]),
    Spec("sale.view_order_form", "form", [
        placed("after", "group", "sale_header", vehicle_group(
            ' string="Informations véhicule" invisible="not opportunity_id"',
            WIDGET + fields_xml(("rpbm_part_type", "Pièce concernée")))),
        before("x_studio_eurocode_complet", ("rpbm_eurocode", "Eurocode (Complet)")),
        before("x_studio_vsf_dsignation_1", ("rpbm_vsf_designation", "VSF - Désignation")),
        before("x_studio_vsf_qt_dispo", ("rpbm_vsf_stock", "VSF - Qté Dispo")),
    ] + [ancien("field", name) for name in (
        "x_studio_pice_concerne", "x_studio_immatriculation_", "x_studio_many2one_field_rP62C", "x_studio_many2one_field_DkgHx",
        "x_studio_dtails_modle", "x_studio_vin_", "x_studio_date_1re_mec", "x_studio_nergie_moteur", "x_studio_base_eurocode",
        "x_studio_eurocode_complet", "x_studio_vsf_dsignation_1", "x_studio_vsf_qt_dispo")]),
    Spec("account.view_move_form", "form", [  # pas de widget : account.move n'est pas gere
        placed("inside", "group", "studio_group_4fc_left", fields_xml(
            ("rpbm_license_plate", "Immatriculation"), ("rpbm_vehicle_brand_id", "Marque"),
            ("rpbm_vehicle_model_id", "Modèle"), ("rpbm_eurocode", "Eurocode"))),
        before("x_studio_pice_concerne_1", ("rpbm_part_type", "Pièce concernée")),
        ancien("field", "x_studio_pice_concerne_1"),
    ]),
    Spec("crm.crm_case_tree_view_oppor", "list", [ancien("field", "x_studio_field_NVioD", True), ancien("field", "x_studio_field_NwRik", True)],
         natives=("rpbm_license_plate", "rpbm_eurocode")),
    Spec("account.view_out_invoice_tree", "list", [ancien("field", "x_studio_related_field_JyuVb", True)], natives=("rpbm_license_plate",)),
    Spec("crm.view_crm_case_opportunities_filter", "search", [
        ancien("field", "x_studio_field_NVioD"), ancien("field", "x_studio_field_NwRik"),
        ancien("filter", "x_studio_field_KyCjB"), ancien("filter", "x_studio_field_eENQz"),
    ], natives=("rpbm_license_plate", "rpbm_vehicle_brand_id", "rpbm_eurocode")),
    Spec("account.view_account_invoice_filter", "search", [ancien("field", "x_studio_immatriculation")], natives=("rpbm_license_plate",)),
]


# --- acces Odoo ------------------------------------------------------------------------

def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolve(odoo: Odoo, xmlid: str) -> tuple[dict | None, int | None]:
    """Vue de base par xmlid, puis sa vue Studio par la regle de web_studio
    (controllers/main.py _get_studio_view) : jamais d'id code en dur."""
    module, name = xmlid.split(".")
    data = odoo.search_read("ir.model.data", [["module", "=", module], ["name", "=", name], ["model", "=", "ir.ui.view"]], ["res_id"], limit=1)
    if not data:
        return None, None
    base = odoo.execute("ir.ui.view", "read", [data[0]["res_id"]], ["name", "model", "mode"])[0]
    if base["mode"] != "primary":
        return base, None
    studio = odoo.execute("ir.ui.view", "search_read", [["inherit_id", "=", base["id"]], ["name", "=", f"Odoo Studio: {base['name']} customization"]],
                          fields=["id"], order="priority desc, name desc, id desc", limit=1)
    return base, (studio[0]["id"] if studio else None)


def combined(odoo: Odoo, model: str, base_id: int, view_type: str, studio: bool = False) -> str:
    views = odoo.execute(model, "get_views", [[base_id, view_type]], options={"studio": True} if studio else {}, context=FR)
    return views["views"][view_type]["arch"]


def studio_error(odoo: Odoo, model: str, base_id: int, view_type: str) -> str | None:
    """Mode strict de l'editeur Studio : une ancre introuvable y leve une erreur."""
    try:
        combined(odoo, model, base_id, view_type, studio=True)
    except xmlrpc.client.Fault as error:
        return fault(error)
    return None


def fault(error: xmlrpc.client.Fault) -> str:
    return (error.faultString.strip().splitlines() or [""])[-1][:300]


def read_arch(odoo: Odoo, view_id: int) -> str:
    return odoo.execute("ir.ui.view", "read", [view_id], ["arch_db"], context=FR)[0]["arch_db"]


def write_arch(odoo: Odoo, view_id: int, arch: str) -> None:
    # execute direct et non Odoo.call : en dry-run, call imprimerait toute l'arch (~70 000 caracteres).
    assert odoo.commit, "ecriture d'arch hors --commit"
    odoo.execute("ir.ui.view", "write", [view_id], {"arch_db": arch}, context=FR)


def run_dir(run_id: str) -> Path:
    return RUNS_DIR / f"{run_id}-studio-views"


def save_manifest(run_id: str, manifest: dict) -> None:
    (run_dir(run_id) / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


# --- apply -----------------------------------------------------------------------------

def apply(odoo: Odoo, run_id: str, views: list[Spec] = VIEWS) -> int:
    if odoo.commit and (run_dir(run_id) / "manifest.json").exists():
        raise SystemExit(f"Le run {run_id} a deja un manifeste : choisir un autre --run pour ne pas ecraser ses sauvegardes.")
    print("ATTENTION : fermez toute session Studio ouverte sur ces vues ; un editeur ouvert avant l'apply "
          "reecrit son instantane au prochain enregistrement.\n")
    report = Report(f"Vues Studio -- apply {run_id}")
    manifest = {"run": run_id, "url": odoo.url, "db": odoo.db, "views": []}
    labels: dict[str, dict[str, str]] = {}
    for spec in views:
        base, studio_id = resolve(odoo, spec.xmlid)
        if not studio_id:
            report.add("FAIL", spec.xmlid, "vue de base primaire ou vue Studio introuvable")
            continue
        model, title = base["model"], f"{spec.xmlid} (Studio {studio_id})"
        if model not in labels:
            labels[model] = {name: field["string"] for name, field in odoo.execute(model, "fields_get", [], attributes=["string"], context=FR).items()}
        arch = Arch(combined(odoo, model, base["id"], spec.view_type), labels[model])
        missing = sorted({f for item in spec.items for f in item.fields if f not in arch.labels}
                         | {f for f in spec.natives if arch.find("field", f) is None})
        if missing:
            report.add("WARN", title, f"ignoree : natifs absents du modele ou de la vue {missing} (module pas encore a jour ?)")
            continue

        expected, pending = [], []
        for item in spec.items:
            if item.check(arch):
                expected.append(item)
            elif any(arch.find(*node) is not None for node in item.nodes):
                report.add("WARN", title, f"{item.label} present ailleurs (deplace dans Studio ?) : non rajoute")
            elif arch.find(*item.anchor) is None:
                report.add("FAIL", title, f"ancre {item.anchor[1]} introuvable : {item.label} non ajoute")
            else:
                pending.append(item)
        if not pending:
            report.add("PASS", title, f"rien a faire ({len(expected)} controle(s) en place)")
            continue
        error = studio_error(odoo, model, base["id"], spec.view_type)
        if error:
            report.add("FAIL", title, f"editeur Studio deja en erreur sur cette vue, non modifiee : {error}")
            continue
        blocks = [item.block(arch) for item in pending]
        if not odoo.commit:
            report.add("TODO", title, f"{len(pending)} bloc(s) a ajouter, {len(expected)} en place")
            for block in blocks:
                print(f"      {block}")
            continue

        old = read_arch(odoo, studio_id)
        if not old.rstrip().endswith("</data>"):
            report.add("FAIL", title, "arch Studio sans racine <data> : non modifiee")
            continue
        folder = run_dir(run_id)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{studio_id}-avant.xml").write_text(old, encoding="utf-8")
        try:
            write_arch(odoo, studio_id, old.rstrip()[:-len("</data>")] + "  " + "\n  ".join(blocks) + "\n</data>")
        except xmlrpc.client.Fault as error:
            report.add("FAIL", title, f"ecriture refusee par Odoo (transaction annulee) : {fault(error)}")
            continue
        entry = {"xmlid": spec.xmlid, "studio_id": studio_id, "backup": f"{studio_id}-avant.xml",
                 "sha256_before": sha(old), "sha256_after": None, "restored": False}
        manifest["views"].append(entry)
        save_manifest(run_id, manifest)  # avant toute verification : une interruption laisse une trace
        try:
            entry["sha256_after"] = sha(read_arch(odoo, studio_id))
            after = Arch(combined(odoo, model, base["id"], spec.view_type), labels[model])
            failed = [item.label for item in expected + pending if not item.check(after)]
            error = studio_error(odoo, model, base["id"], spec.view_type)
        except BaseException:
            # Erreur reseau, Ctrl+C... : ne jamais laisser un patch non verifie en place.
            try:
                write_arch(odoo, studio_id, old)
                entry["restored"] = True
            finally:
                save_manifest(run_id, manifest)
            raise
        if failed or error:
            write_arch(odoo, studio_id, old)
            entry["restored"] = True
            same = sha(read_arch(odoo, studio_id)) == entry["sha256_before"]
            report.add("FAIL", title, f"verification KO ({failed or error}) : sauvegarde restauree" + ("" if same else " (sha256 different, a controler)"))
        else:
            report.add("PASS", title, f"{len(pending)} bloc(s) ajoute(s) ; controles et mode Studio OK")
        save_manifest(run_id, manifest)

    if manifest["views"]:
        (run_dir(run_id) / "rapport.md").write_text(report.markdown(f"\nManifeste : manifest.json (rollback : `studio_views.py rollback --run {run_id}`)"), encoding="utf-8")
        print(f"\nSauvegardes et rapport : {run_dir(run_id)}")
    if not odoo.commit:
        print("\nDry-run : relancer avec --commit pour ecrire.")
    return 1 if report.count("FAIL") else 0


# --- rollback --------------------------------------------------------------------------

def load_manifest(run_id: str) -> dict:
    path = run_dir(run_id) / "manifest.json"
    if not path.exists():
        raise SystemExit(f"Manifeste introuvable : {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def rollback(odoo: Odoo, run_id: str) -> int:
    # ponytail: restauration de la sauvegarde seulement, et seulement si l'arch n'a pas bouge depuis
    # l'apply. Pas de mode « strip » (retirer les noeuds rpbm_* et le suffixe « (ancien) » d'une arch
    # editee depuis) : a ecrire le jour ou une desinstallation de rpbm_agent est reellement prevue.
    manifest = load_manifest(run_id)
    report = Report(f"Vues Studio -- rollback {run_id}")
    for entry in manifest["views"]:
        title = f"{entry['xmlid']} (Studio {entry['studio_id']})"
        current = sha(read_arch(odoo, entry["studio_id"]))
        if current == entry["sha256_before"]:
            report.add("PASS", title, "deja dans l'etat d'avant l'apply")
        elif entry["restored"]:
            report.add("WARN", title, "restauree par l'apply mais modifiee depuis : rien a restaurer, a controler")
        elif current != entry["sha256_after"]:
            report.add("FAIL", title, "arch modifiee depuis l'apply (edition Studio ?) : restauration refusee, elle "
                                      "ecraserait cette edition ; retirer les ajouts rpbm_* et « (ancien) » dans Studio")
        elif not odoo.commit:
            report.add("TODO", title, "serait restauree (dry-run)")
        else:
            write_arch(odoo, entry["studio_id"], (run_dir(run_id) / entry["backup"]).read_text(encoding="utf-8"))
            same = sha(read_arch(odoo, entry["studio_id"])) == entry["sha256_before"]
            report.add("PASS" if same else "WARN", title, "sauvegarde restauree" + ("" if same else " (sha256 different de l'avant-apply, a controler)"))
    if odoo.commit:
        (run_dir(run_id) / "rollback.md").write_text(report.markdown(), encoding="utf-8")
    else:
        print("\nDry-run : relancer avec --commit pour restaurer.")
    return 1 if report.count("FAIL") else 0


def main(argv: Iterable[str] | None = None) -> int:
    connection = argparse.ArgumentParser(add_help=False)
    connection.add_argument("--commit", action="store_true", help="ecrire reellement dans Odoo")
    connection.add_argument("--i-understand-this-is-production", action="store_true",
                            help="requis en plus de --commit si la base cible ne semble pas etre une preprod/staging/test")
    connection.add_argument("--profile", default=None, help="profil paradigme-mcp (defaut : .paradigme.yaml)")
    connection.add_argument("--url", default=None, help="URL du build (defaut : https://<base>.dev.odoo.com ; jamais l'alias de branche)")
    connection.add_argument("--db", default=None, help="base du build si differente de celle du profil")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("apply", parents=[connection]).add_argument("--run", default=datetime.now().strftime("%Y%m%d-%H%M%S"))
    sub.add_parser("rollback", parents=[connection]).add_argument("--run", required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)

    previous = load_manifest(args.run) if args.command == "rollback" else {}  # rollback : meme instance que l'apply
    db = args.db or previous.get("db") or load_profile(args.profile)["database"]
    odoo = Odoo(args.profile, args.commit, build_url(args.url or previous.get("url"), db), db)
    db_normalized = odoo.db.lower().replace("-", "").replace("_", "")
    if args.commit and not any(word in db_normalized for word in ("preprod", "staging", "test")) and not args.i_understand_this_is_production:
        parser.error(f"La base {odoo.db!r} ne contient ni 'preprod' ni 'staging' ni 'test' dans son nom. "
                     "Repasser avec --i-understand-this-is-production si c'est bien voulu.")
    mode = "ECRITURE" if args.commit else "dry-run (aucune ecriture)"
    print(f"studio_views {args.command} run={args.run} sur {odoo.url} (profil {odoo.profile!r}, base {odoo.db}) -- {mode}\n")
    return (apply if args.command == "apply" else rollback)(odoo, args.run)


if __name__ == "__main__":
    sys.exit(main())
