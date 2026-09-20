"""Recette hybride du widget rpbm_agent : de l'opportunite a la vente.

    python recette_widget.py wait-build [--timeout 1800]           attend que la version du manifest soit deployee
    python recette_widget.py migration                             controle de la migration champs natifs (lecture seule)
    python recette_widget.py prepare --run 20260921 [--commit]     preflight + donnees de recette + session web
    python recette_widget.py verify --run 20260921                 verification en base apres le parcours navigateur

Les phases navigateur (dialog du widget sur l'opportunite puis sur le devis) sont jouees par un
agent avec le MCP chrome-devtools et le helper recette_widget.js ; ce script prepare et verifie.
Aucun nettoyage : les enregistrements restent, tagues RECETTE-<run> (decision pilote).

Connexion : profil paradigme-mcp-local (rpbm-preprod) pour les secrets et la base ; l'URL est celle du
build (https://<base>.dev.odoo.com), jamais l'alias de branche. La session web utilise les memes
identifiants via /web/session/authenticate. Aucun secret n'est affiche ; le jeton de session
n'est ecrit que dans .paradigme/tmp/ (ignore par Git).
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from common import Odoo, load_profile

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "rpbm_agent"
TMP_DIR = ROOT / ".paradigme" / "tmp"
RUNS_DIR = Path(__file__).resolve().parent / "runs"

LABOR_PRODUCTS = {"T1": 24, "T2": 23, "T3": 113}
VSF_PARTNER_ID = 5708
CARRIERS = {"galleria": "Retrait / pose Galleria", "genipa": "Retrait / pose Genipa", "domicile": "Pose sur site (Camion)"}
FUEL_TYPES = {"diesel", "gasoline", "full_hybrid", "plug_in_hybrid_diesel", "plug_in_hybrid_gasoline", "cng", "lpg", "hydrogen", "electric"}
LEGACY_PAIRS = {  # natif -> Studio historique (crm.lead), pour comparer les taux de remplissage
    "rpbm_license_plate": "x_studio_field_NVioD", "rpbm_vehicle_brand_id": "x_studio_field_KyCjB",
    "rpbm_vehicle_model_id": "x_studio_field_ZhaeY", "rpbm_vin": "x_studio_field_PfJlB",
    "rpbm_fuel_type": "x_studio_field_TAhpP", "rpbm_vehicle_detail_model": "x_studio_field_i8fWl",
    "rpbm_first_registration_date": "x_studio_field_Eh6Wd", "rpbm_part_type": "x_studio_field_eENQz",
    "rpbm_eurocode_base": "x_studio_field_ORIyy", "rpbm_eurocode": "x_studio_field_NwRik",
    "rpbm_vsf_designation": "x_studio_field_j8eh3", "rpbm_vsf_stock": "x_studio_field_BKtpw",
    "rpbm_constructor_reference": "x_studio_field_MNzfJ", "rpbm_intervention_location": "x_studio_lieu_intervention",
}
REMOVED_FIELDS = (
    [("sale.order", f"x_rpbm_vehicle_{s}") for s in ("brand_id", "model_id", "brand_name", "model_name", "vin", "detail_model", "fuel_type", "date_mec")]
    + [("crm.lead", f"x_rpbm_vehicle_{s}") for s in ("brand_id", "model_id", "brand_name", "model_name", "vin", "detail_model", "fuel_type", "date_mec")]
    + [("sale.order", "x_studio_vehicle_id"), ("sale.order", "x_studio_categorie_xglass"), ("sale.order", "x_rpbm_vsf_constructor_reference"),
       ("crm.lead", "x_studio_vehicle_id"), ("crm.lead", "x_studio_categorie_xglass"),
       ("fleet.vehicle", "x_studio_detail_model"), ("fleet.vehicle", "x_studio_date_mec"),
       ("product.template", "x_studio_eurocode"), ("product.template", "x_studio_largeur_mm"), ("product.template", "x_studio_longueur_mm"),
       ("product.product", "x_studio_reference_constructeur")]
)
NATIVE_FIELDS = {
    "crm.lead": list(LEGACY_PAIRS) + ["rpbm_vehicle_id", "rpbm_xglass_category", "rpbm_xglass_piece_id", "rpbm_piece_oe_id", "rpbm_piece_am_id"],
    "sale.order": ["rpbm_vehicle_id", "rpbm_vehicle_brand_id", "rpbm_vehicle_model_id", "rpbm_license_plate", "rpbm_eurocode", "rpbm_part_type", "rpbm_intervention_location"],
    "sale.order.line": ["rpbm_xglass_price", "rpbm_labor_operation_key"],
    "fleet.vehicle": ["rpbm_detail_model", "rpbm_first_registration_date"],
    "product.template": ["rpbm_eurocode", "rpbm_width_mm", "rpbm_length_mm"],
    "product.product": ["rpbm_constructor_reference"],
    "account.move": ["rpbm_vehicle_id", "rpbm_license_plate"],
    "stock.picking": ["rpbm_vehicle_id"],
}


class Report:
    def __init__(self, title: str) -> None:
        self.title = title
        self.rows: list[tuple[str, str, str]] = []
        self.started = datetime.now()

    def add(self, status: str, check: str, detail: str = "") -> None:
        self.rows.append((status, check, detail))
        print(f"  [{status}] {check}" + (f" -- {detail}" if detail else ""))

    def count(self, status: str) -> int:
        return sum(1 for row in self.rows if row[0] == status)

    def markdown(self, extra: str = "") -> str:
        lines = [f"# {self.title}", "", f"Date : {self.started:%Y-%m-%d %H:%M}",
                 f"Verdict : **{'FAIL' if self.count('FAIL') else 'PASS'}** ({self.count('PASS')} PASS, {self.count('WARN')} WARN, {self.count('FAIL')} FAIL, {self.count('NOT_RUN')} NOT_RUN)",
                 "", "| Statut | Contrôle | Détail |", "|---|---|---|"]
        lines += [f"| `{status}` | {check} | {detail} |" for status, check, detail in self.rows]
        return "\n".join(lines + ["", extra]).rstrip() + "\n"

    def save(self, name: str, extra: str = "") -> Path:
        RUNS_DIR.mkdir(exist_ok=True)
        path = RUNS_DIR / name
        path.write_text(self.markdown(extra), encoding="utf-8")
        print(f"\nRapport : {path}")
        return path


def manifest_version() -> str:
    manifest = ast.literal_eval((MODULE / "__manifest__.py").read_text(encoding="utf-8"))
    return manifest["version"]


def build_url(explicit: str | None, db: str | None = None) -> str:
    """URL du build Odoo.sh de la base du profil (https://<base>.dev.odoo.com).

    L'alias de branche (*.odoo.com) n'est jamais utilise : il pointe vers le build courant de la
    branche, pas necessairement celui du commit a verifier.
    """
    if explicit:
        return explicit.rstrip("/")
    return f"https://{db or load_profile()['database']}.dev.odoo.com"


def installed_version(odoo: Odoo) -> str | None:
    found = odoo.search_read("ir.module.module", [["name", "=", "rpbm_agent"]], ["state", "installed_version"], limit=1)
    return found[0]["installed_version"] if found and found[0]["state"] == "installed" else None


def manifest_path(run_id: str) -> Path:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    return TMP_DIR / f"recette-{run_id}.json"


def load_manifest(run_id: str) -> dict:
    path = manifest_path(run_id)
    if not path.exists():
        raise SystemExit(f"Manifeste introuvable : {path} (lancer `prepare --run {run_id} --commit` d'abord).")
    return json.loads(path.read_text(encoding="utf-8"))


# --- wait-build ---------------------------------------------------------------------

def cmd_wait_build(args) -> int:
    expected = manifest_version()
    deadline = time.monotonic() + args.timeout
    print(f"Attente de rpbm_agent {expected} sur le profil (toutes les {args.interval}s, max {args.timeout}s)...")
    while True:
        try:
            odoo = Odoo(args.profile, False, build_url(args.url, args.db), args.db)
            version = installed_version(odoo)
        except Exception as error:  # noqa: BLE001 - instance en cours de rebuild
            version = f"indisponible ({type(error).__name__})"
        print(f"  {datetime.now():%H:%M:%S} version installée : {version}")
        if version == expected:
            print("Build déployé.")
            return 0
        if time.monotonic() > deadline:
            print("Délai dépassé : le build n'a pas livré la version attendue.")
            return 2
        time.sleep(args.interval)


# --- migration -----------------------------------------------------------------------

def cmd_migration(args) -> int:
    odoo = Odoo(args.profile, False, build_url(args.url, args.db), args.db)
    report = Report(f"Recette migration champs natifs — {odoo.url}")
    expected = manifest_version()
    version = installed_version(odoo)
    report.add("PASS" if version == expected else "FAIL", "version du module", f"{version} (attendu {expected})")

    for model, names in NATIVE_FIELDS.items():
        present = odoo.field_names(model)
        missing = [name for name in names if name not in present]
        report.add("FAIL" if missing else "PASS", f"champs natifs {model}", f"manquants : {missing}" if missing else f"{len(names)} présents")

    lead_fields = odoo.field_names("crm.lead")
    for native, studio in LEGACY_PAIRS.items():
        if studio not in lead_fields:
            report.add("WARN", f"crm.lead {native}", f"champ Studio {studio} absent : pas de comparaison")
            continue
        n_native = odoo.search_count("crm.lead", [[native, "!=", False]])
        n_studio = odoo.search_count("crm.lead", [[studio, "!=", False]])
        ratio = n_native / n_studio if n_studio else 1.0
        status = "PASS" if ratio >= 0.95 else ("WARN" if ratio >= 0.8 else "FAIL")
        report.add(status, f"crm.lead {native} vs {studio}", f"{n_native} / {n_studio} remplis ({ratio:.0%})")

    so_fields = odoo.field_names("sale.order")
    if "x_studio_immatriculation_" in so_fields:
        n_native = odoo.search_count("sale.order", [["rpbm_license_plate", "!=", False]])
        n_studio = odoo.search_count("sale.order", [["x_studio_immatriculation_", "!=", False]])
        report.add("PASS" if n_native >= 0.95 * n_studio else "FAIL", "sale.order miroir immatriculation", f"{n_native} / {n_studio}")
    sol_fields = odoo.field_names("sale.order.line")
    if "x_studio_prix_x_glass" in sol_fields:
        n_native = odoo.search_count("sale.order.line", [["rpbm_xglass_price", "!=", 0]])
        n_studio = odoo.search_count("sale.order.line", [["x_studio_prix_x_glass", "!=", 0]])
        report.add("PASS" if n_native >= 0.95 * n_studio else "FAIL", "sale.order.line prix X'Glass natif", f"{n_native} / {n_studio}")
    n_eurocode = odoo.search_count("product.template", [["rpbm_eurocode", "!=", False]])
    report.add("PASS" if n_eurocode >= 3000 else "FAIL", "product.template.rpbm_eurocode", f"{n_eurocode} produits")
    for vehicle in odoo.search_read("fleet.vehicle", [], ["license_plate", "rpbm_detail_model", "rpbm_first_registration_date", "vin_sn", "fuel_type"], limit=10):
        report.add("PASS" if vehicle["rpbm_detail_model"] else "WARN", f"fleet.vehicle {vehicle['license_plate']}",
                   f"détail={vehicle['rpbm_detail_model']!r} MEC={vehicle['rpbm_first_registration_date']} énergie={vehicle['fuel_type']}")

    leftovers = []
    for model, name in REMOVED_FIELDS:
        if odoo.search_count("ir.model.fields", [["model", "=", model], ["name", "=", name]]):
            leftovers.append(f"{model}.{name}")
    report.add("PASS" if not leftovers else "WARN", "champs créés par l'ancien module supprimés",
               "aucun résidu" if not leftovers else f"conservés (référencés ou erreur, voir journal Odoo.sh) : {leftovers}")

    # Cohérence marque/modèle sur un échantillon : natif Fleet vs référentiel Studio.
    if "x_studio_field_KyCjB" in lead_fields:
        sample = odoo.search_read("crm.lead", [["rpbm_vehicle_brand_id", "!=", False], ["x_studio_field_KyCjB", "!=", False]],
                                  ["rpbm_vehicle_brand_id", "x_studio_field_KyCjB", "rpbm_vehicle_model_id", "x_studio_field_ZhaeY"], limit=25)
        mismatches = [lead["id"] for lead in sample
                      if _norm(lead["rpbm_vehicle_brand_id"][1]) != _norm(lead["x_studio_field_KyCjB"][1])]
        report.add("PASS" if not mismatches else "WARN", "marque native = marque Studio (échantillon 25)",
                   "identiques" if not mismatches else f"écarts sur {mismatches}")

    lock = odoo.search_read("ir.config_parameter", [["key", "=", "rpbm_agent.session_lock"]], ["value"], limit=1)
    report.add("PASS" if not (lock and lock[0]["value"]) else "WARN", "verrou portail libre", (lock[0]["value"] if lock else "absent")[:60])
    report.save(f"{date.today():%Y%m%d}-recette-migration.md")
    return 1 if report.count("FAIL") else 0


def _norm(value) -> str:
    import unicodedata
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(c for c in text if not unicodedata.combining(c)).strip().casefold()


# --- prepare -------------------------------------------------------------------------

def _reference_lead(odoo: Odoo, plate: str) -> dict:
    found = odoo.search_read(
        "crm.lead", [["rpbm_license_plate", "=", plate], ["rpbm_eurocode", "!=", False]],
        ["id", "rpbm_eurocode_base", "rpbm_eurocode", "rpbm_vehicle_brand_id", "rpbm_vehicle_model_id", "rpbm_part_type"], limit=1,
    )
    return found[0] if found else {}


def web_session(url: str, db: str | None = None) -> tuple[str | None, str]:
    """Ouvre une session web avec les identifiants du profil. Retourne (session_id, message)."""
    profile = load_profile()
    payload = {"jsonrpc": "2.0", "method": "call", "id": 1,
               "params": {"db": db or profile["database"], "login": profile["username"], "password": profile["password"]}}
    request = urllib.request.Request(f"{url}/web/session/authenticate", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode())
            cookies = response.headers.get_all("Set-Cookie") or []
    except (urllib.error.URLError, OSError) as error:
        return None, f"réseau : {type(error).__name__}"
    if body.get("error"):
        name = body["error"].get("data", {}).get("name") or body["error"].get("message")
        return None, f"refusée ({name}) : le mot de passe du profil n'ouvre pas de session interactive (clé API ?)"
    session_id = next((c.split("session_id=", 1)[1].split(";", 1)[0] for c in cookies if "session_id=" in c), None)
    return session_id, f"ouverte (uid {body.get('result', {}).get('uid')})"


def cmd_prepare(args) -> int:
    odoo = Odoo(args.profile, args.commit, build_url(args.url, args.db), args.db)
    report = Report(f"Recette widget — préparation run {args.run} — {odoo.url}")
    expected = manifest_version()
    version = installed_version(odoo)
    report.add("PASS" if version == expected else "FAIL", "version du module", f"{version} (attendu {expected})")
    if version != expected:
        report.save(f"{args.run}-recette-prepare.md")
        return 1

    keys = {row["key"] for row in odoo.search_read("ir.config_parameter", [["key", "in", ["XGLASS_USER", "XGLASS_PASS", "VSF_LOGIN", "VSF_PASSWORD"]]], ["key"])}
    report.add("PASS" if len(keys) == 4 else "FAIL", "identifiants portails configurés", f"{len(keys)}/4 clés")
    products = {p["id"]: p for p in odoo.search_read("product.product", [["id", "in", list(LABOR_PRODUCTS.values())]], ["id", "name", "detailed_type", "list_price", "active"])}
    ok = all(pid in products and products[pid]["detailed_type"] == "service" and products[pid]["active"] for pid in LABOR_PRODUCTS.values())
    report.add("PASS" if ok else "FAIL", "produits main-d'œuvre T1/T2/T3", ", ".join(f"{p['id']}={p['list_price']}" for p in products.values()))
    report.add("PASS" if odoo.search_count("res.partner", [["id", "=", VSF_PARTNER_ID]]) else "FAIL", "fournisseur VSF 5708")
    carriers = {c["name"]: c["id"] for c in odoo.search_read("delivery.carrier", [["name", "in", list(CARRIERS.values())], ["active", "=", True]], ["id", "name"])}
    report.add("PASS" if len(carriers) == 3 else "FAIL", "transporteurs", str(carriers))
    for model, names in NATIVE_FIELDS.items():
        missing = [n for n in names if n not in odoo.field_names(model)]
        if missing:
            report.add("FAIL", f"champs natifs {model}", f"manquants : {missing}")
    for plate, expect_vehicle in ((args.plate_new, False), (args.plate_existing, True)):
        vehicles = odoo.search_read("fleet.vehicle", [["license_plate", "=", plate]], ["id", "driver_id"])
        status = "PASS" if bool(vehicles) == expect_vehicle else "WARN"
        report.add(status, f"plaque {plate} {'avec' if expect_vehicle else 'sans'} véhicule Fleet", str(vehicles))
    lock = odoo.search_read("ir.config_parameter", [["key", "=", "rpbm_agent.session_lock"]], ["value"], limit=1)
    report.add("PASS" if not (lock and lock[0]["value"]) else "WARN", "verrou portail libre", (lock[0]["value"] if lock else "absent")[:60])

    expectations = {plate: _reference_lead(odoo, plate) for plate in (args.plate_new, args.plate_existing)}
    for plate, ref in expectations.items():
        report.add("PASS" if ref else "WARN", f"attendus de référence {plate}",
                   f"lead {ref.get('id')} base={ref.get('rpbm_eurocode_base')} eurocode={ref.get('rpbm_eurocode')} marque={ref.get('rpbm_vehicle_brand_id')}" if ref else "aucun dossier de référence")

    manifest = {"run": args.run, "url": odoo.url, "created": datetime.now().isoformat(timespec="seconds"),
                "plate_new": args.plate_new, "plate_existing": args.plate_existing,
                "expectations": expectations, "carriers": carriers, "labor_products": LABOR_PRODUCTS}
    if report.count("FAIL"):
        report.save(f"{args.run}-recette-prepare.md")
        return 1
    if not args.commit:
        report.add("NOT_RUN", "création des données de recette", "dry-run : relancer avec --commit")
        report.save(f"{args.run}-recette-prepare.md")
        return 0

    partner_id = odoo.execute("res.partner", "create", {"name": f"RECETTE-{args.run} Client", "customer_rank": 1})
    stage = odoo.search_read("crm.stage", [], ["id"], limit=1)
    leads = {}
    for tag, plate, location in (("W1", args.plate_new, "galleria"), ("W3", args.plate_existing, "galleria")):
        vals = {"name": f"RECETTE-{args.run}-{tag} {plate}", "type": "opportunity", "partner_id": partner_id,
                "rpbm_license_plate": plate, "rpbm_intervention_location": location}
        # Champs Studio obligatoires dans la vue formulaire (sinon « Confirmer et enregistrer » echoue) : valeurs arbitraires.
        lead_fields = odoo.field_names("crm.lead")
        if "x_studio_moyen_1er_contact" in lead_fields:
            vals["x_studio_moyen_1er_contact"] = "Téléphone"
        if "x_studio_field_VGmbJ" in lead_fields:
            choice = odoo.search_read("x_choix_comment_connu", [], ["id"], limit=1)
            if choice:
                vals["x_studio_field_VGmbJ"] = choice[0]["id"]
        if stage:
            vals["stage_id"] = stage[0]["id"]
        leads[tag] = odoo.execute("crm.lead", "create", vals)
        report.add("PASS", f"opportunité {tag} créée", f"id {leads[tag]} ({plate})")
    manifest.update({"partner_id": partner_id, "leads": leads, "url": odoo.url, "db": odoo.db,
                     "urls": {tag: f"{odoo.url}/web#model=crm.lead&view_type=form&id={lead_id}" for tag, lead_id in leads.items()}})
    if "x_studio_field_NVioD" in odoo.field_names("crm.lead"):
        lead = odoo.search_read("crm.lead", [["id", "=", leads["W1"]]], ["x_studio_field_NVioD", "x_studio_lieu_intervention"])[0]
        report.add("PASS" if lead["x_studio_field_NVioD"] == args.plate_new and lead["x_studio_lieu_intervention"] == "GALLERIA" else "FAIL",
                   "double alimentation Studio à la création", str(lead))

    session_id, message = web_session(odoo.url, odoo.db)
    manifest["session_id"] = session_id
    report.add("PASS" if session_id else "WARN", "session web (profil)", message + ("" if session_id else " — connexion manuelle requise dans le navigateur"))
    manifest_path(args.run).write_text(json.dumps(manifest, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Manifeste : {manifest_path(args.run)}")
    for tag, url in manifest["urls"].items():
        print(f"  {tag} : {url}")
    report.save(f"{args.run}-recette-prepare.md", "\nIdentifiants créés : " + json.dumps({"partner": partner_id, **leads}))
    return 0


# --- verify --------------------------------------------------------------------------

def cmd_verify(args) -> int:
    manifest = load_manifest(args.run)
    odoo = Odoo(args.profile, False, build_url(args.url or manifest.get("url"), args.db or manifest.get("db")), args.db or manifest.get("db"))
    report = Report(f"Recette widget — vérification run {args.run} — {odoo.url}")
    lead_fields = odoo.field_names("crm.lead")
    w1 = odoo.search_read("crm.lead", [["id", "=", manifest["leads"]["W1"]]], ["id"] + NATIVE_FIELDS["crm.lead"] + [
        f for f in LEGACY_PAIRS.values() if f in lead_fields])[0]

    # Opportunité W1
    vehicle_id = w1["rpbm_vehicle_id"] and w1["rpbm_vehicle_id"][0]
    report.add("PASS" if vehicle_id else "FAIL", "W1 véhicule lié", str(w1["rpbm_vehicle_id"]))
    report.add("PASS" if w1["rpbm_xglass_category"] == "PARE-BRISE" else "FAIL", "W1 catégorie X'Glass", str(w1["rpbm_xglass_category"]))
    report.add("PASS" if w1["rpbm_part_type"] == "windshield" else "FAIL", "W1 pièce concernée", str(w1["rpbm_part_type"]))
    report.add("PASS" if w1["rpbm_eurocode_base"] else "FAIL", "W1 base eurocode", str(w1["rpbm_eurocode_base"]))
    for name in ("rpbm_eurocode", "rpbm_vsf_designation"):
        report.add("PASS" if w1[name] else "FAIL", f"W1 {name} (article principal)", str(w1[name])[:60])
    report.add("PASS" if w1["rpbm_xglass_piece_id"] and w1["rpbm_piece_oe_id"] else "FAIL", "W1 identifiants de pièce", f"{w1['rpbm_xglass_piece_id']} / {w1['rpbm_piece_oe_id']} / {w1['rpbm_piece_am_id']}")
    for name in ("rpbm_vehicle_brand_id", "rpbm_vehicle_model_id", "rpbm_vin", "rpbm_fuel_type"):
        report.add("PASS" if w1[name] else "WARN", f"W1 {name} dérivé du véhicule", str(w1[name]))
    expectation = manifest["expectations"].get(manifest["plate_new"]) or {}
    if expectation.get("rpbm_eurocode_base"):
        report.add("PASS" if w1["rpbm_eurocode_base"] == expectation["rpbm_eurocode_base"] else "WARN", "W1 base eurocode = référence",
                   f"{w1['rpbm_eurocode_base']} vs {expectation['rpbm_eurocode_base']}")
    studio_checks = {"x_studio_field_NVioD": w1["rpbm_license_plate"], "x_studio_field_NwRik": w1["rpbm_eurocode"],
                     "x_studio_field_eENQz": {"windshield": "Pare-Brise", "rear_window": "Lunette arrière", "side_window": "Glace Latérale", "other": "Autre..."}.get(w1["rpbm_part_type"]),
                     "x_studio_field_ORIyy": w1["rpbm_eurocode_base"], "x_studio_field_j8eh3": w1["rpbm_vsf_designation"]}
    for studio, expected in studio_checks.items():
        if studio in w1:
            report.add("PASS" if (w1[studio] or False) == (expected or False) else "FAIL", f"W1 Studio {studio} synchronisé", f"{w1[studio]!r} vs natif {expected!r}")
    if "x_studio_field_KyCjB" in w1 and w1["rpbm_vehicle_brand_id"]:
        report.add("PASS" if w1["x_studio_field_KyCjB"] and _norm(w1["x_studio_field_KyCjB"][1]) == _norm(w1["rpbm_vehicle_brand_id"][1]) else "FAIL",
                   "W1 Studio marque synchronisée", f"{w1['x_studio_field_KyCjB']} vs {w1['rpbm_vehicle_brand_id']}")

    # Fleet
    if vehicle_id:
        vehicle = odoo.search_read("fleet.vehicle", [["id", "=", vehicle_id]], ["license_plate", "driver_id", "fuel_type", "vin_sn", "rpbm_first_registration_date", "rpbm_detail_model", "model_id"])[0]
        report.add("PASS" if vehicle["license_plate"] == manifest["plate_new"] else "FAIL", "Fleet plaque", vehicle["license_plate"])
        report.add("PASS" if vehicle["driver_id"] and vehicle["driver_id"][0] == manifest["partner_id"] else "WARN", "Fleet conducteur = client", str(vehicle["driver_id"]))
        report.add("PASS" if (not vehicle["fuel_type"] or vehicle["fuel_type"] in FUEL_TYPES) else "FAIL", "Fleet énergie native", str(vehicle["fuel_type"]))
        report.add("PASS" if vehicle["vin_sn"] and not vehicle["vin_sn"].startswith("var") else "WARN", "Fleet VIN", str(vehicle["vin_sn"]))
        report.add("PASS" if vehicle["rpbm_detail_model"] else "WARN", "Fleet détail modèle", str(vehicle["rpbm_detail_model"]))

    # Produit
    product = odoo.search_read("product.product", [["product_tmpl_id.rpbm_eurocode", "=", w1["rpbm_eurocode"]]], ["id", "name", "default_code", "list_price", "image_1920"], limit=2) if w1["rpbm_eurocode"] else []
    report.add("PASS" if len(product) == 1 else ("WARN" if len(product) > 1 else "FAIL"), "produit VSF (par eurocode)", f"{[p['id'] for p in product]} {product[0]['default_code'] if product else ''}")
    if product:
        sellers = odoo.search_read("product.supplierinfo", [["product_tmpl_id.rpbm_eurocode", "=", w1["rpbm_eurocode"]], ["partner_id", "=", VSF_PARTNER_ID]], ["price", "date_start"])
        report.add("PASS" if len(sellers) >= 1 else "FAIL", "prix fournisseur VSF", str([(s["price"], s["date_start"]) for s in sellers]))

    # Devis W2
    orders = odoo.search_read("sale.order", [["opportunity_id", "=", w1["id"]]], ["id", "name", "state", "carrier_id", "picking_ids", "rpbm_license_plate", "rpbm_vehicle_id", "rpbm_eurocode", "order_line"])
    report.add("PASS" if orders else "FAIL", "devis lié à W1", str([(o["id"], o["name"], o["state"]) for o in orders]))
    for order in orders:
        report.add("PASS" if order["carrier_id"] and order["carrier_id"][1] == CARRIERS["galleria"] else "FAIL", f"{order['name']} transporteur prérempli", str(order["carrier_id"]))
        report.add("PASS" if order["rpbm_license_plate"] == w1["rpbm_license_plate"] and order["rpbm_vehicle_id"] == w1["rpbm_vehicle_id"] else "FAIL", f"{order['name']} miroirs natifs", f"{order['rpbm_license_plate']} / {order['rpbm_vehicle_id']}")
        lines = odoo.search_read("sale.order.line", [["order_id", "=", order["id"]]], ["product_id", "product_uom_qty", "price_unit", "rpbm_xglass_price", "rpbm_labor_operation_key"])
        article_lines = [l for l in lines if l["rpbm_xglass_price"]]
        labor_lines = [l for l in lines if l["rpbm_labor_operation_key"]]
        report.add("PASS" if article_lines else "FAIL", f"{order['name']} ligne article VSF", str([(l["product_id"][1][:30], l["price_unit"], l["rpbm_xglass_price"]) for l in article_lines]))
        for line in article_lines:
            expected_price = round(line["rpbm_xglass_price"] * 1.5, 3)
            report.add("PASS" if abs(line["price_unit"] - expected_price) < 0.01 else "FAIL", f"{order['name']} prix ligne = prix X'Glass × 1,5", f"{line['price_unit']} vs {expected_price}")
        report.add("PASS" if labor_lines else "WARN", f"{order['name']} lignes main-d'œuvre", str([(l["product_id"][0], l["product_uom_qty"], l["price_unit"]) for l in labor_lines]))
        for line in labor_lines:
            pid = line["product_id"][0]
            product_price = odoo.search_read("product.product", [["id", "=", pid]], ["list_price"])[0]["list_price"]
            ok = pid in LABOR_PRODUCTS.values() and line["product_uom_qty"] > 0 and abs(line["price_unit"] - product_price) < 0.01
            report.add("PASS" if ok else "FAIL", f"{order['name']} MO {line['rpbm_labor_operation_key']}", f"produit {pid} qté {line['product_uom_qty']} prix {line['price_unit']} (tarif {product_price})")
        report.add("PASS" if order["state"] == "sale" else "FAIL", f"{order['name']} confirmé", order["state"])
        report.add("PASS" if order["picking_ids"] else "WARN", f"{order['name']} livraison générée", str(order["picking_ids"]))
        if order["picking_ids"]:
            picking = odoo.search_read("stock.picking", [["id", "in", order["picking_ids"]]], ["picking_type_id", "rpbm_vehicle_id"], limit=1)[0]
            report.add("PASS" if picking["rpbm_vehicle_id"] == w1["rpbm_vehicle_id"] else "WARN", "livraison : véhicule reporté", str(picking["rpbm_vehicle_id"]))

    # W3 : véhicule existant inchangé
    w3 = odoo.search_read("crm.lead", [["id", "=", manifest["leads"]["W3"]]], ["rpbm_vehicle_id", "rpbm_license_plate"])[0]
    existing = odoo.search_read("fleet.vehicle", [["license_plate", "=", manifest["plate_existing"]]], ["id", "vin_sn", "driver_id"], limit=1)
    report.add("PASS" if w3["rpbm_vehicle_id"] and existing and w3["rpbm_vehicle_id"][0] == existing[0]["id"] else "WARN", "W3 véhicule existant réutilisé", f"{w3['rpbm_vehicle_id']} / Fleet {existing}")

    lock = odoo.search_read("ir.config_parameter", [["key", "=", "rpbm_agent.session_lock"]], ["value"], limit=1)
    report.add("PASS" if not (lock and lock[0]["value"]) else "WARN", "verrou portail libéré", (lock[0]["value"] if lock else "absent")[:60])
    if manifest.get("session_id"):
        try:
            urllib.request.urlopen(urllib.request.Request(f"{odoo.url}/web/session/logout", headers={"Cookie": f"session_id={manifest['session_id']}"}), timeout=30)
            report.add("PASS", "session web invalidée")
        except Exception as error:  # noqa: BLE001
            report.add("WARN", "session web invalidée", type(error).__name__)
    report.save(f"{args.run}-recette-widget.md", "\nManifeste : " + str(manifest_path(args.run)))
    return 1 if report.count("FAIL") else 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", default=None, help="profil paradigme-mcp (défaut : .paradigme.yaml)")
    parser.add_argument("--url", default=None, help="URL du build (défaut : https://<base>.dev.odoo.com ; jamais l'alias de branche)")
    parser.add_argument("--db", default=None, help="base du build (rpbm-pre-prod-<id>) si differente de celle du profil")
    sub = parser.add_subparsers(dest="command", required=True)
    wait = sub.add_parser("wait-build")
    wait.add_argument("--timeout", type=int, default=1800)
    wait.add_argument("--interval", type=int, default=60)
    sub.add_parser("migration")
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--run", default=date.today().strftime("%Y%m%d"))
    prepare.add_argument("--plate-new", default="BF857CZ")
    prepare.add_argument("--plate-existing", default="FQ581EN")
    prepare.add_argument("--commit", action="store_true")
    verify = sub.add_parser("verify")
    verify.add_argument("--run", required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)
    return {"wait-build": cmd_wait_build, "migration": cmd_migration, "prepare": cmd_prepare, "verify": cmd_verify}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
