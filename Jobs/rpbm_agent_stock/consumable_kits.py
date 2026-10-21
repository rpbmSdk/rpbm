"""Pose un kit vide (nomenclature « Kit » sans composant) sur chaque consommable vendable sans fournisseur.

    python consumable_kits.py apply [--perimetre modeles|utilises|vendables] [--commit] [--run <id>] [--profile ...] [--url ...] [--db ...]
                                    [--i-understand-this-is-production]
    python consumable_kits.py check --perimetre modeles|utilises|vendables [--profile ...] [--url ...] [--db ...]
    python consumable_kits.py archive [--commit] [--avec-utilises] [--run <id>] [--profile ...] [--url ...] [--db ...]
    python consumable_kits.py rollback --run <id> [--commit] [--profile ...] [--url ...] [--db ...] [--i-understand-this-is-production]

Pourquoi : avec un transporteur a route (« stock, sinon regle suivante »), un consommable n'a jamais de stock libre et
remonte jusqu'a la regle Acheter ; sans fournisseur, _run_buy annule toute la confirmation (« pas de prix
fournisseur »), et sans route Acheter c'est « No rule has been found » (plan-modeles-devis.md §1).

Ce que fait apply : une nomenclature mrp.bom de type « Kit » (phantom), sans ligne, reference RPBM-SANS-APPRO, sur
chaque consommable vendable et actif sans fournisseur valide du perimetre choisi : « modeles », ceux qui figurent sur une
ligne d'un modele de devis actif ; « utilises », ceux-la plus ceux qui ont servi depuis 12 mois (vente ou facture) ou
sont sur un devis ouvert ; « vendables », tous. --perimetre est obligatoire avec --commit ; sans lui, la
simulation montre les deux perimetres et leur difference. A la confirmation, Odoo remplace le besoin d'un kit par
ceux de ses composants (mrp/models/stock_rule.py:254-284) : aucun, donc ni regle, ni achat, ni erreur. Donnee
standard, aucun code ; l'article garde son type consommable (la regle 8 le majore toujours), reste dans les modeles,
et les devis ouverts se confirment sans retouche (le kit est lu a la confirmation). Decision du 2026-10-21.

Effets connus : ces lignes n'apparaissent plus sur les bons de livraison et leur quantite livree reste a 0 (facturation
sur quantites commandees, non touchee) ; tout mouvement ulterieur de l'article est explose en rien (reception d'achat
comprise) : si un fournisseur lui est ajoute un jour, supprimer son kit en meme temps. Sur une commande confirmee avant le
kit, baisser la quantite d'une ligne ne reduit plus sa livraison : corriger le bon a la main.

Hors cible : les stockables sans fournisseur (un kit casse leur suivi de stock, mrp/models/product.py:220-310 : leur
donner un fournisseur) ; un article a regle de reapprovisionnement (refuse par mrp_bom.check_kit_has_not_orderpoint) ou
a plusieurs variantes : FAIL, a traiter a la main.

archive (decision du 2026-10-21 : kits pour les 25 consommables des modeles, archivage des autres) : archive les
consommables vendables sans fournisseur ni kit absents des modeles de devis actifs. La simulation donne, pour chacun,
ses lignes de vente et de facture sur 12 mois, sa derniere utilisation et ses lignes de devis ouverts ; ceux qui servent
encore sont en tete (WARN) et --commit ne les archive qu'avec --avec-utilises. Un article archive reste sur les devis
qui le portent : avec un transporteur a route, leur confirmation bloquerait encore (pas de kit).

check : aucun consommable du perimetre sans fournisseur ni kit ; code retour 1 sinon. A rejouer apres chaque ajout
d'article. rollback : supprime les nomenclatures creees par ce run, sauf celles modifiees depuis (lignes ajoutees,
reference changee), et desarchive les articles archives par ce run. Sauvegarde dans runs/<run>-consommables/ ; chaque operation journalisee AVANT d'etre jouee.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import xmlrpc.client
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

from common import Odoo, load_profile
from recette_widget import Report, build_url

RUNS_DIR = Path(__file__).resolve().parent / "runs"
ALL = {"active_test": False}
CODE = "RPBM-SANS-APPRO"
SCOPES = ("modeles", "utilises", "vendables")


def m2o(value):
    return value[0] if value else False


# --- lecture -----------------------------------------------------------------------------

def read_state(odoo: Odoo) -> dict:
    """Consommables et stockables vendables actifs, leurs fournisseurs valides et leurs kits."""
    products = odoo.execute("product.product", "search_read", [["detailed_type", "in", ["consu", "product"]], ["sale_ok", "=", True]],
                            fields=["default_code", "name", "detailed_type", "product_tmpl_id", "uom_id", "nbr_reordering_rules"])
    tmpl_ids = sorted({m2o(p["product_tmpl_id"]) for p in products})
    templates = {t["id"]: t for t in odoo.execute("product.template", "read", tmpl_ids, ["product_variant_count"])} if tmpl_ids else {}
    rows = odoo.execute("product.supplierinfo", "search_read", [["product_tmpl_id", "in", tmpl_ids]],
                        fields=["partner_id", "company_id", "product_id", "product_tmpl_id"]) if tmpl_ids else []
    partners = {p["id"]: p["active"] for p in odoo.execute("res.partner", "read", sorted({m2o(r["partner_id"]) for r in rows}),
                                                           ["active"], context=ALL)} if rows else {}
    company = m2o(odoo.execute("res.users", "read", [odoo.uid], ["company_id"])[0]["company_id"])
    boms = odoo.execute("mrp.bom", "search_read", [["type", "=", "phantom"], ["product_tmpl_id", "in", tmpl_ids]],
                        fields=["code", "product_tmpl_id", "product_id", "bom_line_ids"]) if tmpl_ids else []
    in_templates = {m2o(l["product_id"]) for l in odoo.execute(
        "sale.order.template.line", "search_read", [["sale_order_template_id.active", "=", True], ["product_id", "!=", False]],
        fields=["product_id"])}
    for p in products:
        tmpl = m2o(p["product_tmpl_id"])
        # Fournisseur valide comme le repli de _run_buy (purchase_stock/models/stock_rule.py:69-71) : partenaire
        # actif, societe vide ou la notre, variante ; ni dates ni quantite minimale.
        p["has_seller"] = any(partners.get(m2o(r["partner_id"])) and m2o(r["company_id"]) in (False, company)
                              and m2o(r["product_id"]) in (False, p["id"]) for r in rows if m2o(r["product_tmpl_id"]) == tmpl)
        p["kits"] = [b for b in boms if m2o(b["product_tmpl_id"]) == tmpl and m2o(b["product_id"]) in (False, p["id"])]
        p["variants"] = templates.get(tmpl, {}).get("product_variant_count", 1)
        p["in_templates"] = p["id"] in in_templates
    return {"products": products}


def label(product: dict) -> str:
    code = (product["default_code"] or "").strip()
    return f"{code} · {product['name']}" if code and code != product["name"] else product["name"]


def targets(state: dict, scope: str | None) -> list[dict]:
    """Consommables sans fournisseur ni kit du perimetre (« vendables » sans perimetre choisi). « utilises » suppose
    mark_used() passe sur l'etat."""
    return [p for p in state["products"] if p["detailed_type"] == "consu" and not p["has_seller"] and not p["kits"]
            and (scope in (None, "vendables") or p["in_templates"] or (scope == "utilises" and p["used"]))]


def mark_used(odoo: Odoo, state: dict) -> dict[int, dict]:
    """Usage sur 12 mois des consommables hors modeles (p["used"]) ; renvoie l'historique par article."""
    outside = [p for p in targets(state, None) if not p["in_templates"]]
    hist = history(odoo, [p["id"] for p in outside], (date.today() - timedelta(days=365)).isoformat())
    for p in state["products"]:
        p["used"] = bool(p["id"] in hist and any(hist[p["id"]][k] for k in ("sales", "invoices", "open")))
    return hist


def plan(state: dict, scope: str | None) -> tuple[list[dict], dict[int, str]]:
    """Une creation de kit par consommable du perimetre, et les cas a traiter a la main."""
    ops, manual = [], {}
    for p in sorted(targets(state, scope), key=lambda p: label(p)):
        if p["nbr_reordering_rules"]:
            manual[p["id"]] = "regle de reapprovisionnement : Odoo refuse le kit, a supprimer d'abord"
        elif p["variants"] > 1:
            manual[p["id"]] = f"{p['variants']} variantes : kit par variante a decider a la main"
        else:
            ops.append({"op": "create_kit", "product": p["id"], "tmpl": m2o(p["product_tmpl_id"]), "uom": m2o(p["uom_id"]),
                        "label": label(p)})
    return ops, manual


def remaining(state: dict, ops: list[dict], scope: str | None) -> list[dict]:
    """Consommables du perimetre sans fournisseur ni kit apres ces operations (le controle de check)."""
    done = {op["product"] for op in ops}
    return [p for p in targets(state, scope) if p["id"] not in done]


def usage(odoo: Odoo, product_ids: list[int]) -> tuple[dict, dict]:
    """Lignes de devis ouverts (qte > 0) et lignes de modeles actifs, par article : ce que chaque kit debloque."""
    def counts(model, domain):
        groups = odoo.execute(model, "read_group", domain, ["product_id"], ["product_id"], lazy=False) if product_ids else []
        return {m2o(g["product_id"]): g["__count"] for g in groups}
    quotes = counts("sale.order.line", [["order_id.state", "in", ["draft", "sent"]], ["product_id", "in", product_ids],
                                        ["product_uom_qty", ">", 0]])
    templates = counts("sale.order.template.line", [["sale_order_template_id.active", "=", True], ["product_id", "in", product_ids]])
    return quotes, templates


# --- apply -------------------------------------------------------------------------------

def run_dir(run_id: str) -> Path:
    return RUNS_DIR / f"{run_id}-consommables"


def save_manifest(run_id: str, manifest: dict) -> None:
    path = run_dir(run_id) / "manifest.json"
    path.with_suffix(".tmp").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(path.with_suffix(".tmp"), path)  # atomique : un arret brutal ne laisse jamais un manifeste tronque


def write(odoo: Odoo, model: str, method: str, *args, **kwargs):
    assert odoo.commit, "ecriture hors --commit"
    return odoo.execute(model, method, *args, **kwargs)


def find_kit(odoo: Odoo, tmpl: int) -> list[dict]:
    return odoo.execute("mrp.bom", "search_read", [["type", "=", "phantom"], ["product_tmpl_id", "=", tmpl], ["code", "=", CODE]],
                        fields=["code", "bom_line_ids"], context=ALL)


def apply(odoo: Odoo, run_id: str, scope: str | None = None) -> int:
    if odoo.commit and scope not in SCOPES:
        raise SystemExit("--perimetre modeles ou vendables est obligatoire avec --commit.")
    if odoo.commit and (run_dir(run_id) / "manifest.json").exists():
        raise SystemExit(f"Le run {run_id} a deja un manifeste : choisir un autre --run pour ne pas ecraser ses sauvegardes.")
    report = Report(f"Kits vides -- apply {run_id}")
    state = read_state(odoo)
    mark_used(odoo, state)
    consu = [p for p in state["products"] if p["detailed_type"] == "consu"]
    report.add("INFO", "etat initial", f"{len(consu)} consommables vendables, dont {sum(1 for p in consu if not p['has_seller'])} "
                                       f"sans fournisseur et {sum(1 for p in consu if p['kits'])} deja en kit")
    ops, manual = plan(state, scope)
    if not scope:
        in_t = [p for p in targets(state, None) if p["in_templates"]]
        used = [p for p in targets(state, None) if not p["in_templates"] and p["used"]]
        idle = [p for p in targets(state, None) if not p["in_templates"] and not p["used"]]
        report.add("INFO", "perimetre modeles", f"{len(in_t)} kit(s) : consommables sans fournisseur presents dans un modele actif")
        report.add("INFO", "perimetre utilises", f"{len(in_t) + len(used)} kit(s) : + ceux qui servent encore (12 mois ou devis ouvert) : "
                                                 + ", ".join(label(p) for p in sorted(used, key=label)))
        report.add("INFO", "perimetre vendables", f"{len(in_t) + len(used) + len(idle)} kit(s) : + ceux sans usage : "
                                                  + ", ".join(label(p) for p in sorted(idle, key=label)))
    quotes, templates = usage(odoo, [op["product"] for op in ops])
    for op in ops:
        where = [] if scope else ["[modeles]" if templates.get(op["product"]) else "[hors modeles]"]
        if templates.get(op["product"]):
            where.append(f"{templates[op['product']]} ligne(s) de modeles actifs")
        if quotes.get(op["product"]):
            where.append(f"{quotes[op['product']]} ligne(s) de devis ouverts")
        report.add("TODO" if not odoo.commit else "INFO", op["label"], "kit vide a creer" + (" " + " ; ".join(where) if where else ""))
    stockables = [p for p in state["products"] if p["detailed_type"] == "product" and not p["has_seller"]]
    if stockables:
        report.add("WARN", "stockables sans fournisseur", f"{len(stockables)} articles, non traites (un kit casserait leur stock) : "
                                                          "leur donner un fournisseur")
    if not ops:
        report.add("PASS", "kits", "rien a faire")

    if ops and odoo.commit:
        run_dir(run_id).mkdir(parents=True, exist_ok=True)
        manifest = {"run": run_id, "url": odoo.url, "db": odoo.db, "code": CODE, "scope": scope, "ops": [], "rolled_back": False}
        save_manifest(run_id, manifest)
        try:
            for op in ops:
                op["pending"] = True  # journalisee AVANT d'etre jouee : une reponse perdue reste annulable
                manifest["ops"].append(op)
                save_manifest(run_id, manifest)
                op["bom"] = write(odoo, "mrp.bom", "create", {
                    "product_tmpl_id": op["tmpl"], "type": "phantom", "product_qty": 1.0, "product_uom_id": op["uom"],
                    "code": CODE, "company_id": False})
                del op["pending"]
                save_manifest(run_id, manifest)
        except BaseException:
            save_manifest(run_id, manifest)
            print(f"\nApply interrompu apres {len(manifest['ops'])} operation(s) engagee(s) : "
                  f"`consumable_kits.py rollback --run {run_id} --commit` les annule.")
            raise
        report.add("PASS", "ecritures", f"{len(ops)} kit(s) cree(s)")
        state, ops = read_state(odoo), []  # relecture reelle
        mark_used(odoo, state)
    left = remaining(state, ops, scope)
    for p in left:
        report.add("FAIL", label(p), manual.get(p["id"], "consommable vendable sans fournisseur ni kit : bloquera la confirmation "
                                                         "avec un transporteur a route"))
    if odoo.commit and (run_dir(run_id) / "manifest.json").exists():
        (run_dir(run_id) / "rapport.md").write_text(report.markdown(f"\nRollback : `consumable_kits.py rollback --run {run_id}`"), encoding="utf-8")
        print(f"\nSauvegarde et rapport : {run_dir(run_id)}")
    elif not odoo.commit:
        print("\nDry-run : relancer avec --commit pour ecrire.")
    return 1 if report.count("FAIL") else 0


def history(odoo: Odoo, product_ids: list[int], since: str) -> dict[int, dict]:
    """Usage de chaque article : lignes de vente et de facture depuis `since`, derniere date, lignes de devis ouverts."""
    def grouped(model, domain, agg=None):
        rows = odoo.execute(model, "read_group", domain + [["product_id", "in", product_ids]], ["product_id"] + ([agg] if agg else []),
                            ["product_id"], lazy=False) if product_ids else []
        return {m2o(r["product_id"]): r for r in rows}
    sales = grouped("sale.order.line", [["state", "!=", "cancel"], ["create_date", ">=", since]])
    last_sale = grouped("sale.order.line", [["state", "!=", "cancel"]], "create_date:max")
    posted = [["parent_state", "=", "posted"], ["move_id.move_type", "in", ["out_invoice", "out_refund"]]]
    invoices = grouped("account.move.line", posted + [["date", ">=", since]])
    last_invoice = grouped("account.move.line", posted, "date:max")
    quotes = grouped("sale.order.line", [["order_id.state", "in", ["draft", "sent"]], ["product_uom_qty", ">", 0]])
    out = {}
    for pid in product_ids:
        dates = [d for d in ((last_sale.get(pid) or {}).get("create_date"), (last_invoice.get(pid) or {}).get("date")) if d]
        out[pid] = {"sales": (sales.get(pid) or {}).get("__count", 0), "invoices": (invoices.get(pid) or {}).get("__count", 0),
                    "open": (quotes.get(pid) or {}).get("__count", 0), "last": max(str(d)[:10] for d in dates) if dates else "jamais"}
    return out


def archive(odoo: Odoo, run_id: str, with_used: bool = False) -> int:
    if odoo.commit and (run_dir(run_id) / "manifest.json").exists():
        raise SystemExit(f"Le run {run_id} a deja un manifeste : choisir un autre --run pour ne pas ecraser ses sauvegardes.")
    report = Report(f"Archivage des consommables hors modeles -- {run_id}")
    state = read_state(odoo)
    hist = mark_used(odoo, state)
    candidates = sorted((p for p in targets(state, None) if not p["in_templates"]), key=label)
    used = [p for p in candidates if p["used"]]
    used.sort(key=lambda p: (-hist[p["id"]]["open"], -hist[p["id"]]["invoices"], -hist[p["id"]]["sales"]))
    idle = [p for p in candidates if p not in used]
    report.add("INFO", "perimetre", f"{len(candidates)} consommables vendables sans fournisseur ni kit, hors modeles actifs : "
                                    f"{len(used)} encore utilises (12 mois ou devis ouvert), {len(idle)} sans usage")
    rows = ["", "| Article | Ventes 12 m | Factures 12 m | Devis ouverts | Derniere utilisation | Archive |", "|---|---:|---:|---:|---|---|"]
    for p in used + idle:
        h = hist[p["id"]]
        keep = p in used and not with_used
        detail = f"ventes 12 m {h['sales']}, factures 12 m {h['invoices']}, devis ouverts {h['open']}, derniere utilisation {h['last']}"
        if p in used:
            report.add("WARN", label(p), detail + (" : encore utilise, archive avec --avec-utilises" if keep else " : encore utilise, archive"))
        else:
            report.add("TODO" if not odoo.commit else "INFO", label(p), detail + " : a archiver")
        rows.append(f"| {label(p)} | {h['sales']} | {h['invoices']} | {h['open']} | {h['last']} | {'non (utilise)' if keep else 'oui'} |")
    print("\n".join(rows))
    ops = [{"op": "archive", "product": p["id"], "tmpl": m2o(p["product_tmpl_id"]), "label": label(p)}
           for p in candidates if p in idle or with_used]
    if not odoo.commit:
        print("\nDry-run : relancer avec --commit pour archiver.")
        return 0
    if not ops:
        report.add("PASS", "archivage", "rien a faire")
        return 0
    run_dir(run_id).mkdir(parents=True, exist_ok=True)
    manifest = {"run": run_id, "url": odoo.url, "db": odoo.db, "ops": [], "rolled_back": False}
    save_manifest(run_id, manifest)
    try:
        for op in ops:
            op["pending"] = True
            manifest["ops"].append(op)
            save_manifest(run_id, manifest)
            write(odoo, "product.template", "write", [op["tmpl"]], {"active": False})  # descend aux variantes
            del op["pending"]
            save_manifest(run_id, manifest)
    except BaseException:
        save_manifest(run_id, manifest)
        print(f"\nArchivage interrompu : `consumable_kits.py rollback --run {run_id} --commit` desarchive.")
        raise
    report.add("PASS", "archivage", f"{len(ops)} article(s) archive(s)")
    (run_dir(run_id) / "rapport.md").write_text(report.markdown("\n".join(rows)), encoding="utf-8")
    return 0


def check(odoo: Odoo, scope: str) -> int:
    report = Report(f"Kits vides -- controle ({scope})")
    state = read_state(odoo)
    if scope == "utilises":
        mark_used(odoo, state)
    left = remaining(state, [], scope)
    for p in left:
        report.add("FAIL", label(p), "consommable vendable sans fournisseur ni kit")
    if not left:
        report.add("PASS", f"consommables ({scope})", "tous ont un fournisseur ou un kit")
    return 1 if left else 0


# --- rollback ----------------------------------------------------------------------------

def load_manifest(run_id: str) -> dict:
    path = run_dir(run_id) / "manifest.json"
    if not path.exists():
        raise SystemExit(f"Manifeste introuvable : {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def rollback(odoo: Odoo, run_id: str) -> int:
    manifest = load_manifest(run_id)
    report = Report(f"Kits vides -- rollback {run_id}")
    if manifest["rolled_back"]:
        report.add("PASS", "run", "deja annule")
        return 0
    for op in reversed(manifest["ops"]):
        if op.get("undone"):
            continue
        if op["op"] == "archive":
            if not odoo.commit:
                report.add("TODO", op["label"], "a desarchiver")
                continue
            write(odoo, "product.template", "write", [op["tmpl"]], {"active": True}, context=ALL)
            write(odoo, "product.product", "write", [op["product"]], {"active": True}, context=ALL)  # le desarchivage ne descend pas
            report.add("PASS", op["label"], "desarchive")
            op["undone"] = True
            save_manifest(run_id, manifest)
            continue
        # Par reference et modele d'article : retrouve aussi un kit cree dont la reponse s'est perdue (pending).
        kits = find_kit(odoo, op["tmpl"])
        if not kits:
            report.add("PASS", op["label"], "kit deja absent")
        elif len(kits) > 1 or kits[0]["bom_line_ids"]:
            report.add("FAIL", op["label"], f"kit {[k['id'] for k in kits]} modifie ou en double depuis l'apply : non supprime, a voir a la main")
            continue
        elif not odoo.commit:
            report.add("TODO", op["label"], f"kit {kits[0]['id']} a supprimer")
            continue
        else:
            try:
                write(odoo, "mrp.bom", "unlink", [kits[0]["id"]])
            except xmlrpc.client.Fault as error:
                report.add("FAIL", op["label"], f"suppression refusee par Odoo : {error.faultString.strip().splitlines()[-1][:200]}")
                continue
            report.add("PASS", op["label"], f"kit {kits[0]['id']} supprime")
        if odoo.commit:
            op["undone"] = True
            save_manifest(run_id, manifest)  # reprise possible apres une coupure
    if not odoo.commit:
        print("\nDry-run : relancer avec --commit pour annuler.")
        return 1 if report.count("FAIL") else 0
    manifest["rolled_back"] = not report.count("FAIL")
    save_manifest(run_id, manifest)
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
    apply_parser.add_argument("--perimetre", choices=SCOPES, help="obligatoire avec --commit ; sans lui, la simulation montre les deux")
    sub.add_parser("check", parents=[connection]).add_argument("--perimetre", choices=SCOPES, required=True)
    archive_parser = sub.add_parser("archive", parents=[connection])
    archive_parser.add_argument("--run", default=datetime.now().strftime("%Y%m%d-%H%M%S"))
    archive_parser.add_argument("--avec-utilises", action="store_true", help="archiver aussi les articles encore utilises")
    sub.add_parser("rollback", parents=[connection]).add_argument("--run", required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)

    previous = load_manifest(args.run) if args.command == "rollback" else {}  # rollback : meme instance que l'apply
    db = args.db or previous.get("db") or load_profile(args.profile)["database"]
    odoo = Odoo(args.profile, args.commit and args.command != "check", build_url(args.url or previous.get("url"), db), db)
    db_normalized = odoo.db.lower().replace("-", "").replace("_", "")
    if odoo.commit and not any(word in db_normalized for word in ("preprod", "staging", "test")) and not args.i_understand_this_is_production:
        parser.error(f"La base {odoo.db!r} ne contient ni 'preprod' ni 'staging' ni 'test' dans son nom. "
                     "Repasser avec --i-understand-this-is-production si c'est bien voulu.")
    mode = "ECRITURE" if odoo.commit else "lecture seule"
    print(f"consumable_kits {args.command} sur {odoo.url} (profil {odoo.profile!r}, base {odoo.db}) -- {mode}\n")
    if args.command == "apply":
        return apply(odoo, args.run, args.perimetre)
    if args.command == "archive":
        return archive(odoo, args.run, args.avec_utilises)
    return check(odoo, args.perimetre) if args.command == "check" else rollback(odoo, args.run)


if __name__ == "__main__":
    sys.exit(main())
