"""Nettoie les modeles de devis actifs pour que leur confirmation ne bloque plus (etape 3 bis).

    python sale_templates.py apply [--commit] [--run <id>] [--decision <nom> ...] [--profile ...] [--url ...] [--db ...] [--i-understand-this-is-production]
    python sale_templates.py rollback --run <id> [--commit] [--profile ...] [--url ...] [--db ...] [--i-understand-this-is-production]

Pourquoi (plan-modeles-devis.md §1) : avec un transporteur a route, une ligne consommable ou stockable
en qte > 0 sans fournisseur valide remonte jusqu'a la regle Acheter, et _run_buy annule toute la
confirmation (« pas de prix fournisseur »). Une telle ligne est dite *bloquante* ; elle est un *piege*
si elle remplit tout sauf la qte (elle bloque des qu'un vendeur la passe a 1).

Regles, appliquees aux lignes de TOUS les modeles actifs (jamais une liste de noms) :
- toujours : supprimer les lignes des articles generiques (§2 ; Q-03 tranchee le 2026-10-12, une fiche
  article par piece), puis archiver ces articles ;
- seulement avec --decision, une fois le choix du client connu (§8) :
    produits-connexes  Produits Connexes (20) remplace par un service PC-FORFAIT au meme prix, 20 archive
    gel-capteur        lignes Gel Capteur (19) supprimees, 19 archive (le gel VSF reel le remplace)
    films-qte-zero     films solaires en qte > 0 passes a qte 0, en attendant le regime des films
    pose-domicile      lignes Pose a domicile (46) et leur section supprimees, 46 et 32 archives
Un article n'est archive que si plus aucune ligne de modele actif ne le reference (§2 : appliquer un
modele recopie un article archive) ; l'article 9 ne l'est jamais.

Rapport : lignes bloquantes restantes (FAIL, code retour 1), pieges (WARN), devis ouverts concernes.
Un second apply repond « rien a faire ». Sauvegarde dans runs/<run>-modeles-devis/ : instantane des
lignes des modeles actifs avant la premiere ecriture, puis chaque operation journalisee AVANT d'etre
jouee. rollback refuse d'agir si un modele touche a change depuis l'apply ; sinon il recree les lignes
supprimees, remet les valeurs ecrites, desarchive les articles et archive le service cree (sauf s'il sert
encore). Apply ou rollback coupe en route : relancer rollback, il reprend ou il s'etait arrete.

Hors perimetre (plan §5) : les 92 pieces du catalogue sans fournisseur (sync_vsf_information), les
consommables libres hors modeles, le transporteur « Free delivery charges ».

Connexion : profil paradigme-mcp-local ; URL du build (https://<base>.dev.odoo.com), jamais l'alias de
branche -- --url obligatoire hors Odoo.sh dev/staging (production).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from common import Odoo, load_profile, normalize_key
from recette_widget import Report, build_url

RUNS_DIR = Path(__file__).resolve().parent / "runs"
ALL = {"active_test": False}

# Ids identiques en production (la preprod en est une copie du 2026-09-11) ; chaque id est controle
# par son default_code (son nom s'il n'a pas de code) avant toute ecriture.
GENERIQUES = {
    13: "VITRAGE1", 47: "VITRAGE2", 31: "LUNETTE V", 30: "LUNETTE V CHAUFFANTE", 50: "GLACE V",
    49: "PARE-BRISE V", 14: "PARE-BRISE V CAPTEUR PLUIE", 15: "PARE-BRISE V CAPTEUR PLUIE (YC CAMERA)",
    35: "GLACE FIXE PORTE AVD", 36: "GLACE FIXE PORTE AVG", 37: "GLACE FIXE PORTE ARD", 38: "GLACE FIXE PORTE ARG",
    39: "GLACE MOBILE PORTE AVD", 40: "GLACE MOBILE PORTE AVG", 41: "GLACE MOBILE PORTE ARD", 42: "GLACE MOBILE PORTE ARG",
    17: "JOINT1", 27: "JOINT2", 28: "JOINT3", 26: "JOINT4", 25: "JOINT SUP PARE-BRISE", 16: "CALE PARE-BRISE",
    48: "AGRPAHES",  # code reel de « AGRAPHES KIT »
}
PRODUITS_CONNEXES = {20: "Produits Connexes"}
GEL_CAPTEUR = {19: "Gel Capteur"}
FILMS = {43: "Film solaire bandeau pour pare-brise", 136: "Film solaire pour vitre avant et arrière mobile",
         137: "Film solaire pour custode et déflecteur", 139: "Film solaire pour lunette arrière",
         140: "Film solaire pour lunette arrière gauche ou droite"}
POSE_DOMICILE = {46: "Pose Domicile", 32: "FRAIS DE DEPLACEMENT"}
POSE_SECTION = "Pose à domicile"
REFERENCES = {**GENERIQUES, **PRODUITS_CONNEXES, **GEL_CAPTEUR, **FILMS, **POSE_DOMICILE}
NEVER_ARCHIVE = {9}  # Nettoyage Bris de Glace : sale_timesheet.time_product
SERVICE_CODE = "PC-FORFAIT"
NEW_SERVICE = -1  # id provisoire du service PC-FORFAIT tant qu'il n'est pas cree
KNOWN_TEMPLATES = {1, 5, 7, 8, *range(10, 26)}  # modeles actifs de la preprod au 2026-10-16
DECISIONS = ("produits-connexes", "gel-capteur", "films-qte-zero", "pose-domicile")
HINTS = {**{pid: "--decision produits-connexes" for pid in PRODUITS_CONNEXES},
         **{pid: "--decision gel-capteur" for pid in GEL_CAPTEUR},
         **{pid: "--decision films-qte-zero" for pid in FILMS}}
LINE_FIELDS = ["sale_order_template_id", "sequence", "display_type", "name", "product_id", "product_uom_qty", "product_uom_id"]


def m2o(value):
    return value[0] if value else False


# --- lecture -----------------------------------------------------------------------------

def read_lines(odoo: Odoo, template_ids: Iterable[int]) -> list[dict]:
    rows = odoo.execute("sale.order.template.line", "search_read", [["sale_order_template_id", "in", sorted(template_ids)]],
                        fields=LINE_FIELDS, order="sale_order_template_id, sequence, id")
    return [{"id": r["id"], "template": m2o(r["sale_order_template_id"]), "sequence": r["sequence"],
             "display_type": r["display_type"] or False, "name": r["name"] or "", "product": m2o(r["product_id"]),
             "qty": r["product_uom_qty"], "uom": m2o(r["product_uom_id"])} for r in rows]


def read_products(odoo: Odoo, ids: Iterable[int]) -> dict[int, dict]:
    ids = sorted(set(ids))
    rows = odoo.execute("product.product", "read", ids, ["default_code", "name", "product_tmpl_id", "detailed_type", "active"],
                        context=ALL) if ids else []
    return {r["id"]: {"code": r["default_code"] or "", "name": r["name"], "tmpl": m2o(r["product_tmpl_id"]),
                      "type": r["detailed_type"], "active": r["active"]} for r in rows}


def read_sellers(odoo: Odoo, tmpl_ids: Iterable[int]) -> dict[int, list[dict]]:
    rows = odoo.execute("product.supplierinfo", "search_read", [["product_tmpl_id", "in", sorted(set(tmpl_ids))]],
                        fields=["partner_id", "company_id", "product_id", "product_tmpl_id"])
    partner_ids = sorted({m2o(r["partner_id"]) for r in rows})
    active = {p["id"]: p["active"] for p in odoo.execute("res.partner", "read", partner_ids, ["active"], context=ALL)} if rows else {}
    sellers: dict[int, list[dict]] = {}
    for r in rows:
        sellers.setdefault(m2o(r["product_tmpl_id"]), []).append({
            "active": active.get(m2o(r["partner_id"]), False), "company": m2o(r["company_id"]), "product": m2o(r["product_id"])})
    return sellers


def check_references(products: dict[int, dict]) -> None:
    """Arret avant toute ecriture si un id de reference manque ou ne porte pas le code attendu."""
    errors = [f"{pid} absent" if pid not in products else
              f"{pid} porte {products[pid]['code'] or products[pid]['name']!r}, {expected!r} attendu"
              for pid, expected in REFERENCES.items()
              if pid not in products or expected != (products[pid]["code"] or products[pid]["name"])]
    if errors:
        raise SystemExit("Articles de reference inattendus, rien n'est ecrit : " + " ; ".join(errors))


def find_service(odoo: Odoo) -> int | None:
    """Service PC-FORFAIT deja cree (rejeu, ou archive par un rollback), None s'il reste a creer ; arret si
    ambigu ou si ce n'est pas un service."""
    found = odoo.execute("product.product", "search_read", [["default_code", "=", SERVICE_CODE]],
                         fields=["detailed_type"], context=ALL)
    if len(found) > 1:
        raise SystemExit(f"{len(found)} articles {SERVICE_CODE} ({[f['id'] for f in found]}) : cle ambigue, rien n'est ecrit.")
    if found and found[0]["detailed_type"] != "service":
        raise SystemExit(f"Article {SERVICE_CODE} {found[0]['id']} n'est pas un service : a regler a la main, rien n'est ecrit.")
    return found[0]["id"] if found else None


# --- regles ------------------------------------------------------------------------------

class State:
    """Articles, fournisseurs et societe : de quoi dire si une ligne bloque."""

    def __init__(self, products: dict[int, dict], sellers: dict[int, list[dict]], company: int) -> None:
        self.products = {**products, NEW_SERVICE: {"code": SERVICE_CODE, "name": SERVICE_CODE, "tmpl": NEW_SERVICE,
                                                    "type": "service", "active": True}}
        self.sellers, self.company = sellers, company

    def status(self, line: dict) -> str | None:
        """FAIL (bloquante), WARN (piege a qte 0) ou None. Fournisseur valide comme le repli de _run_buy
        (purchase_stock/models/stock_rule.py:69-71) : partenaire actif, societe vide ou la notre, variante ;
        ni dates ni qte minimale. shortcut: le free_qty des regles mts_else_mto n'est pas lu (un stockable
        sans fournisseur mais en stock passerait) ; compte bloquant par prudence."""
        product = self.products.get(line["product"]) if not line["display_type"] else None
        if not product or product["type"] not in ("consu", "product"):
            return None
        if any(s["active"] and s["company"] in (False, self.company) and s["product"] in (False, line["product"])
               for s in self.sellers.get(product["tmpl"], [])):
            return None
        return "FAIL" if line["qty"] > 0 else "WARN"


def is_pose_section(line: dict) -> bool:
    return line["display_type"] == "line_section" and normalize_key(line["name"]).lower() == normalize_key(POSE_SECTION).lower()


def plan(lines: list[dict], state: State, decisions: set[str], service: int | None) -> list[dict]:
    """Operations, dans l'ordre d'execution : service, ecritures, suppressions, archivages."""
    removed = set(GENERIQUES) | (set(GEL_CAPTEUR) if "gel-capteur" in decisions else set()) \
        | (set(POSE_DOMICILE) if "pose-domicile" in decisions else set())
    ops: list[dict] = []
    if "produits-connexes" in decisions and service is None:
        ops.append({"op": "create_service"})
    elif "produits-connexes" in decisions and not state.products[service]["active"]:
        ops.append({"op": "unarchive_service", "tmpl": state.products[service]["tmpl"], "products": [service]})
    target = service or NEW_SERVICE
    for line in lines:
        if line["product"] in removed or ("pose-domicile" in decisions and is_pose_section(line)):
            ops.append({"op": "unlink", "line": line})
        elif line["product"] in PRODUITS_CONNEXES and "produits-connexes" in decisions:
            ops.append({"op": "write", "line": line, "values": {"product_id": target, "name": line["name"]}})
        elif line["product"] in FILMS and "films-qte-zero" in decisions and line["qty"] > 0:
            ops.append({"op": "write", "line": line, "values": {"product_uom_qty": 0}})
    ops.sort(key=lambda op: ("create_service", "unarchive_service", "write", "unlink").index(op["op"]))

    archivable = removed | (set(PRODUITS_CONNEXES) if "produits-connexes" in decisions else set())
    referenced = {state.products[line["product"]]["tmpl"] for line in simulate(lines, ops) if line["product"]}
    for tmpl in sorted({state.products[pid]["tmpl"] for pid in archivable}):
        variants = sorted(pid for pid, p in state.products.items() if p["tmpl"] == tmpl and pid != NEW_SERVICE)
        if tmpl not in referenced and not NEVER_ARCHIVE & set(variants) and any(state.products[pid]["active"] for pid in variants):
            ops.append({"op": "archive", "tmpl": tmpl, "products": variants})
    return ops


def simulate(lines: list[dict], ops: list[dict]) -> list[dict]:
    gone = {op["line"]["id"] for op in ops if op["op"] == "unlink"}
    changes = {op["line"]["id"]: op["values"] for op in ops if op["op"] == "write"}
    after = []
    for line in lines:
        if line["id"] in gone:
            continue
        values = changes.get(line["id"], {})
        after.append({**line, "product": values.get("product_id", line["product"]), "qty": values.get("product_uom_qty", line["qty"]),
                      "name": values.get("name", line["name"])})
    return after


def signature(lines: list[dict]) -> list:
    """Contenu d'un modele sans les ids de ligne (une ligne recreee par rollback en change)."""
    return sorted([line["sequence"], line["display_type"] or "", line["name"], line["product"] or 0, line["qty"], line["uom"] or 0]
                  for line in lines)


def describe(line: dict, state: State, templates: dict[int, str]) -> str:
    product = state.products.get(line["product"])
    what = product and (product["code"] or product["name"]) or f"section « {line['name']} »"
    return f"ligne {line['id']} du modele {line['template']} « {templates.get(line['template'], '?')} » : {what}, qte {line['qty']:g}"


# --- apply -------------------------------------------------------------------------------

def run_dir(run_id: str) -> Path:
    return RUNS_DIR / f"{run_id}-modeles-devis"


def save_manifest(run_id: str, manifest: dict) -> None:
    (run_dir(run_id) / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")


def write(odoo: Odoo, model: str, method: str, *args, **kwargs):
    assert odoo.commit, "ecriture hors --commit"
    return odoo.execute(model, method, *args, **kwargs)


def load_state(odoo: Odoo, report: Report) -> tuple[dict[int, str], list[dict], State]:
    products = read_products(odoo, REFERENCES)
    check_references(products)
    templates = {t["id"]: t["name"] for t in odoo.execute("sale.order.template", "search_read", [["active", "=", True]], fields=["name"])}
    for tid in sorted(set(templates) - KNOWN_TEMPLATES):
        report.add("WARN", f"modele {tid} « {templates[tid]} »", "actif mais absent de l'inventaire du 2026-10-16 : relire ses lignes")
    # Aucune option sur la preprod (2026-10-16) : signalees seulement, si la production en a.
    options = odoo.execute("sale.order.template.option", "search_count",
                           [["sale_order_template_id", "in", sorted(templates)], ["product_id", "in", sorted(REFERENCES)]])
    if options:
        report.add("WARN", "options de modeles", f"{options} produit(s) optionnel(s) portent un article de reference : non traites, a retirer a la main")
    lines = read_lines(odoo, templates)
    products.update(read_products(odoo, {line["product"] for line in lines if line["product"]} - set(products)))
    company = m2o(odoo.execute("res.users", "read", [odoo.uid], ["company_id"])[0]["company_id"])
    return templates, lines, State(products, read_sellers(odoo, {p["tmpl"] for p in products.values()}), company)


def report_lines(report: Report, lines: list[dict], state: State, templates: dict[int, str]) -> list[dict]:
    """FAIL par ligne bloquante, WARN par article piege ; renvoie les bloquantes."""
    failing = [line for line in lines if state.status(line) == "FAIL"]
    for line in failing:
        report.add("FAIL", describe(line, state, templates),
                   "bloquante : " + HINTS.get(line["product"], "ajouter un fournisseur a l'article ou retirer la ligne"))
    traps: dict[int, list[int]] = {}
    for line in lines:
        if state.status(line) == "WARN":
            traps.setdefault(line["product"], []).append(line["template"])
    for pid, tids in sorted(traps.items()):
        product = state.products[pid]
        report.add("WARN", f"{product['code'] or product['name']} ({pid})",
                   f"piege : {len(tids)} ligne(s) a qte 0, modeles {sorted(set(tids))} ; bloque si un vendeur passe la qte a 1")
    return failing


def report_quotes(odoo: Odoo, report: Report, products: list[int], state: State) -> str:
    """Devis ouverts ou ces articles sont en qte > 0 (plan §6) : total, et tableau de ceux de moins de 90 jours."""
    rows = odoo.execute("sale.order.line", "search_read", [["order_id.state", "in", ["draft", "sent"]], ["product_id", "in", products],
                                                           ["product_uom_qty", ">", 0]], fields=["order_id", "product_id"]) if products else []
    faulty: dict[int, set[int]] = {}
    for row in rows:
        faulty.setdefault(m2o(row["order_id"]), set()).add(m2o(row["product_id"]))
    if not faulty:
        return ""
    today = date.today()
    orders = [(order, (today - date.fromisoformat(order["date_order"][:10])).days)
              for order in odoo.execute("sale.order", "read", sorted(faulty), ["name", "date_order"])]
    recent = sorted((item for item in orders if item[1] < 90), key=lambda item: item[1])
    report.add("WARN", "devis ouverts", f"{len(orders)} devis brouillon ou envoye portent un article bloquant ou archive, dont "
                                        f"{len(recent)} de moins de 90 jours (tableau) : le vendeur les reprend sans reappliquer le modele (plan §6)")
    table = "\n".join(["", "## Devis ouverts de moins de 90 jours", "", "| Devis | Date | Age (j) | Articles fautifs |", "|---|---|---:|---|"]
                      + [f"| {order['name']} | {order['date_order'][:10]} | {age} | "
                         + ", ".join(state.products[pid]["code"] or state.products[pid]["name"] if pid in state.products else str(pid)
                                     for pid in sorted(faulty[order["id"]])) + " |" for order, age in recent])
    print(table)
    return table


def apply(odoo: Odoo, run_id: str, decisions: set[str]) -> int:
    if odoo.commit and (run_dir(run_id) / "manifest.json").exists():
        raise SystemExit(f"Le run {run_id} a deja un manifeste : choisir un autre --run pour ne pas ecraser ses sauvegardes.")
    report = Report(f"Modeles de devis -- apply {run_id}")
    templates, lines, state = load_state(odoo, report)
    service = find_service(odoo) if "produits-connexes" in decisions else None
    if service:
        state.products.update(read_products(odoo, [service]))  # un service ne bloque jamais : pas de fournisseur a lire
    before = [line for line in lines if state.status(line) == "FAIL"]
    report.add("INFO", "etat initial", f"{len(before)} ligne(s) bloquante(s) dans {len(templates)} modele(s) actif(s) : "
                                       f"{[line['id'] for line in before]} ; decisions : {sorted(decisions) or 'aucune'}")
    ops = plan(lines, state, decisions, service)
    after = simulate(lines, ops)
    if not ops:
        report.add("PASS", "modeles", "rien a faire")
    elif not odoo.commit:
        for op in ops:
            report.add("TODO", *todo(op, state, templates))

    if ops and odoo.commit:
        folder = run_dir(run_id)
        folder.mkdir(parents=True, exist_ok=True)
        manifest = {"run": run_id, "url": odoo.url, "db": odoo.db, "decisions": sorted(decisions), "snapshot": lines,
                    "ops": [], "rolled_back": False}
        save_manifest(run_id, manifest)  # instantane complet avant la premiere ecriture
        try:
            for op in ops:
                # Journalisee AVANT d'etre jouee : une reponse perdue apres une ecriture validee reste annulable.
                op["pending"] = True
                manifest["ops"].append(op)
                save_manifest(run_id, manifest)
                execute(odoo, op, manifest)
                del op["pending"]
                save_manifest(run_id, manifest)
        except BaseException:
            save_manifest(run_id, manifest)
            print(f"\nApply interrompu apres {len(manifest['ops'])} operation(s) engagee(s) : "
                  f"`sale_templates.py rollback --run {run_id} --commit` les annule.")
            raise
        report.add("PASS", "ecritures", f"{len(ops)} operation(s) faites")
        templates, after, state = load_state(odoo, Report("relecture"))  # relecture reelle
        for tid in touched(manifest):
            if signature([line for line in after if line["template"] == tid]) != expected(manifest, tid, manifest["ops"]):
                report.add("WARN", f"modele {tid}", "etat relu different de la simulation : le rollback le prendra pour une edition, a controler")
    failing = report_lines(report, after, state, templates)
    archived = [pid for op in ops if op["op"] == "archive" for pid in op["products"]]
    table = report_quotes(odoo, report, sorted({line["product"] for line in failing} | set(archived)), state)
    if ops and odoo.commit:
        (run_dir(run_id) / "rapport.md").write_text(report.markdown(f"\nRollback : `sale_templates.py rollback --run {run_id}`\n{table}"),
                                                     encoding="utf-8")
        print(f"\nSauvegarde et rapport : {run_dir(run_id)}")
    elif not odoo.commit:
        print("\nDry-run : relancer avec --commit pour ecrire.")
    return 1 if report.count("FAIL") else 0


def todo(op: dict, state: State, templates: dict[int, str]) -> tuple[str, str]:
    if op["op"] == "create_service":
        return f"creer le service {SERVICE_CODE}", "copie de Produits Connexes (20) : nom, prix, taxes, categorie ; type service, non achetable"
    if op["op"] == "unarchive_service":
        return f"desarchiver le service {SERVICE_CODE}", f"article {op['tmpl']}, archive par un rollback precedent"
    if op["op"] == "archive":
        return f"archiver l'article {op['tmpl']}", ", ".join(state.products[pid]["code"] or state.products[pid]["name"] for pid in op["products"])
    detail = "supprimer" if op["op"] == "unlink" else f"ecrire {op['values']}"
    return describe(op["line"], state, templates), detail


def set_active(odoo: Odoo, tmpl: int, products: list[int], active: bool) -> None:
    write(odoo, "product.template", "write", [tmpl], {"active": active}, context=ALL)
    if active:  # l'archivage descend seul aux variantes (product_template.py:506-507), pas le desarchivage
        write(odoo, "product.product", "write", products, {"active": True}, context=ALL)


def execute(odoo: Odoo, op: dict, manifest: dict) -> None:
    """Joue une operation ; y note ce qu'il faut pour la defaire (ids crees)."""
    if op["op"] == "create_service":
        src = odoo.execute("product.product", "read", list(PRODUITS_CONNEXES),
                           ["name", "list_price", "taxes_id", "categ_id", "invoice_policy", "uom_id", "uom_po_id"], context=ALL)[0]
        tmpl = write(odoo, "product.template", "create", {
            "name": src["name"], "default_code": SERVICE_CODE, "detailed_type": "service", "list_price": src["list_price"],
            "taxes_id": [(6, 0, src["taxes_id"])], "categ_id": m2o(src["categ_id"]), "invoice_policy": src["invoice_policy"],
            "uom_id": m2o(src["uom_id"]), "uom_po_id": m2o(src["uom_po_id"]), "sale_ok": True, "purchase_ok": False})
        op.update(tmpl=tmpl, products=[m2o(odoo.execute("product.template", "read", [tmpl], ["product_variant_id"])[0]["product_variant_id"])])
        manifest["service"] = op["products"][0]
    elif op["op"] == "unarchive_service":
        set_active(odoo, op["tmpl"], op["products"], True)
    elif op["op"] == "write":
        values = {**op["values"]}
        if values.get("product_id") == NEW_SERVICE:
            values["product_id"] = op["values"]["product_id"] = manifest["service"]
        write(odoo, "sale.order.template.line", "write", [op["line"]["id"]], values)
    elif op["op"] == "unlink":
        write(odoo, "sale.order.template.line", "unlink", [op["line"]["id"]])
    elif op["op"] == "archive":
        set_active(odoo, op["tmpl"], op["products"], False)


# --- rollback ----------------------------------------------------------------------------

def load_manifest(run_id: str) -> dict:
    path = run_dir(run_id) / "manifest.json"
    if not path.exists():
        raise SystemExit(f"Manifeste introuvable : {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def touched(manifest: dict) -> list[int]:
    return sorted({op["line"]["template"] for op in manifest["ops"] if "line" in op})


def expected(manifest: dict, tid: int, ops: list[dict]) -> list:
    """Signature attendue d'un modele : l'instantane apres ces operations."""
    return signature(simulate([line for line in manifest["snapshot"] if line["template"] == tid], ops))


def undo(odoo: Odoo, op: dict, manifest: dict) -> tuple[str, str]:
    """Defait une operation. Une ligne n'est recreee que si rollback a constate son absence ; les autres
    branches sont rejouables sans effet de bord."""
    line = op.get("line")
    if op["op"] == "archive":
        set_active(odoo, op["tmpl"], op["products"], True)
        return "PASS", f"article {op['tmpl']} desarchive"
    if op["op"] == "unlink":
        new = write(odoo, "sale.order.template.line", "create", {
            "sale_order_template_id": line["template"], "sequence": line["sequence"], "display_type": line["display_type"],
            "name": line["name"], "product_id": line["product"], "product_uom_qty": line["qty"], "product_uom_id": line["uom"]})
        return "PASS", f"ligne {line['id']} recreee (nouvel id {new})"
    if op["op"] == "write":
        keys = {"product_id": "product", "name": "name", "product_uom_qty": "qty"}
        values = {key: line[keys[key]] for key in op["values"]}
        if "product_id" in values:
            values["product_uom_id"] = line["uom"]
        write(odoo, "sale.order.template.line", "write", [line["id"]], values)
        return "PASS", f"ligne {line['id']} remise a {values}"
    # create_service / unarchive_service : le service repart aux archives, sauf s'il sert encore
    service = op["products"][0] if "products" in op else find_service(odoo)
    if not service:
        return "PASS", f"service {SERVICE_CODE} jamais cree"
    uses = odoo.execute("sale.order.template.line", "search_count", [["product_id", "=", service], ["sale_order_template_id.active", "=", True]])
    if uses:
        return "WARN", f"service {SERVICE_CODE} ({service}) encore sur {uses} ligne(s) de modele actif : laisse actif"
    tmpl = op.get("tmpl") or m2o(odoo.execute("product.product", "read", [service], ["product_tmpl_id"], context=ALL)[0]["product_tmpl_id"])
    set_active(odoo, tmpl, [service], False)
    return "PASS", f"service {SERVICE_CODE} (article {tmpl}) archive"


def rollback(odoo: Odoo, run_id: str) -> int:
    manifest = load_manifest(run_id)
    report = Report(f"Modeles de devis -- rollback {run_id}")
    if manifest["rolled_back"]:
        report.add("PASS", "run", "deja annule")
        return 0
    # Operations restantes : un prefixe (l'undo part de la fin). La derniere est incertaine si une coupure l'a
    # surprise, en apply (pending) ou en rollback (undoing) : les deux etats attendus sont alors admis.
    remaining = [op for op in manifest["ops"] if not op.get("undone")]
    uncertain = remaining[-1] if remaining and (remaining[-1].get("pending") or remaining[-1].get("undoing")) else None
    settled = remaining[:-1] if uncertain else remaining
    current = {tid: signature(read_lines(odoo, [tid])) for tid in touched(manifest)}
    changed = [tid for tid, sig in current.items() if sig not in (expected(manifest, tid, remaining), expected(manifest, tid, settled))]
    for tid in changed:
        report.add("FAIL", f"modele {tid}", "modifie depuis l'apply : rollback refuse, il ecraserait cette modification")
    if changed:
        return 1
    if uncertain and "line" in uncertain:
        tid = uncertain["line"]["template"]
        if expected(manifest, tid, remaining) != current[tid]:  # effet absent : jamais joue, ou deja defait
            uncertain["undone"] = odoo.commit
            remaining = settled
            report.add("PASS", f"defaire {uncertain['op']}", f"ligne {uncertain['line']['id']} : effet deja absent")
    for op in reversed(remaining):
        if not odoo.commit:
            report.add("TODO", f"defaire {op['op']}", str(op.get("line", {}).get("id") or op.get("tmpl", "")))
            continue
        op["undoing"] = True
        save_manifest(run_id, manifest)  # reprise possible apres une coupure
        status, detail = undo(odoo, op, manifest)
        op["undone"] = True
        del op["undoing"]
        save_manifest(run_id, manifest)
        report.add(status, f"defaire {op['op']}", detail)
    if not odoo.commit:
        print("\nDry-run : relancer avec --commit pour annuler.")
        return 0
    manifest["rolled_back"] = True
    save_manifest(run_id, manifest)
    for tid in touched(manifest):
        same = signature(read_lines(odoo, [tid])) == expected(manifest, tid, [])
        report.add("PASS" if same else "WARN", f"modele {tid}", "identique a l'instantane" if same else "different de l'instantane, a controler")
    (run_dir(run_id) / "rollback.md").write_text(report.markdown(), encoding="utf-8")
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
    apply_parser = sub.add_parser("apply", parents=[connection])
    apply_parser.add_argument("--run", default=datetime.now().strftime("%Y%m%d-%H%M%S"))
    apply_parser.add_argument("--decision", action="append", choices=DECISIONS, default=[],
                              help="choix du client a appliquer (plan §8), repetable ; aucun par defaut")
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
    print(f"sale_templates {args.command} run={args.run} sur {odoo.url} (profil {odoo.profile!r}, base {odoo.db}) -- {mode}\n")
    if args.command == "apply":
        return apply(odoo, args.run, set(args.decision))
    return rollback(odoo, args.run)


if __name__ == "__main__":
    sys.exit(main())
