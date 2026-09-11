"""Import du catalogue articles et des emplacements RPBM vers Odoo, phase par phase.

Lit les fichiers produits par prepare_migration_files.py et les pousse dans Odoo par XML-RPC.
Chaque phase est independante, rejouable et sans effet tant que --commit n'est pas passe.

    pyenv exec python import_odoo.py <phase> [--commit] [--limit N]

Phases, dans l'ordre des dependances :

    categories    product.category      8 racines + 7 sous-categories, valorisation D8
    warehouses    stock.warehouse       5 entrepots
    locations     stock.location        emplacements source (racks rattaches a leur depot)
    suppliers     res.partner           fournisseurs FRS hors VSF
    products      product.template      catalogue dedoublonne par EUROCODE
    supplierinfo  product.supplierinfo  prix fournisseurs (PRIX ACHAT)
    costs         product.product       cout standard_price (PRIX RV)
    check         lecture seule         controles post-import
    selfcheck     hors ligne            verification de la logique du script

rpbm_agent doit etre installe AVANT la phase products (D5) : son pre_init_hook cree
x_studio_eurocode, sans lequel les fiches migrees restent invisibles au widget (qui en
creerait des doublons) et hors de portee de la synchronisation VSF.

Aucune donnee d'historique du fichier Excel n'est reprise (D4) : le CSV sert uniquement a
creer les articles, les tarifs, les emplacements et les categories.

Toutes les lignes portent un identifiant externe derive de leur cle metier, ce qui rend
l'import idempotent : Odoo fait un write si l'identifiant existe deja, un create sinon.
C'est le seul mecanisme d'unicite disponible sur product.supplierinfo, qui n'a aucune
contrainte SQL ni Python contre les doublons.

Secrets lus depuis ~/.paradigme/.env (RPBM_PREPROD_DB, RPBM_USERNAME, RPBM_PASSWORD),
jamais affiches. Voir plan-import-articles.md pour le deroule complet et les conditions
d'entree de chaque phase.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import xmlrpc.client
from datetime import date
from pathlib import Path
from typing import Iterable, Iterator, Sequence


FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(FOLDER))

from prepare_migration_files import NON_SUPPLIER_KEYS, normalize_key  # noqa: E402

DEFAULT_URL = "https://rpbm-pre-prod.odoo.com/"
ENV_PATH = Path.home() / ".paradigme" / ".env"

# Prefixe des identifiants externes. __import__ est le module reserve d'Odoo aux donnees
# importees : ne jamais utiliser le nom d'un module reel, ses enregistrements seraient
# supprimes a la mise a jour de ce module.
XMLID_MODULE = "__import__"
XMLID_PREFIX = "rpbm"

# load() est tout-ou-rien par appel : une seule ligne en erreur annule tout le lot et
# renvoie ids=False. Des lots courts limitent la perte et permettent de continuer.
CHUNK_SIZE = 200

# Partenaire VSF existant en preproduction, referencé par rpbm_agent.vsf_partner_id.
# Ne jamais creer un second partenaire VSF : la synchronisation VSF du module leve une
# UserError des que deux prix fournisseurs sont actifs pour ce partenaire sur un produit.
VSF_PARTNER_ID = 5708

# Entrepots cibles (decision RPBM du 2026-07-23, forme a confirmer par Q1). Le code Odoo est
# limite a 5 caracteres.
WAREHOUSES = [
    ("Galleria", "GALL"),
    ("Genipa", "GENI"),
    ("Depot 1", "DEP1"),
    ("Depot 2", "DEP2"),
    ("Camion", "CAM"),
]

# Valorisation des stocks (D8). Ce sont les valeurs par defaut d'Odoo 17
# (stock_account/data/stock_account_data.xml) : aucun compte comptable a parametrer. Elles sont
# posees explicitement pour que le PRIX RV charge en phase costs reste stable - en AVCO,
# stock_account/models/stock_move.py reecrit standard_price a chaque reception entrante et le
# cout importe serait ecrase. La preproduction contient deja des categories en average/real_time.
COST_METHOD = "standard"
VALUATION = "manual_periodic"

# Emplacement tampon des PLACE laissees non rattachees (D13). Rien n'est devine : la reprise se
# fait par un simple reimport une fois l'arbitrage rendu, les identifiants externes garantissant
# un deplacement plutot qu'un doublon.
UNRESOLVED_LOCATION = "A controler"


# --- Helpers ---------------------------------------------------------------------------


def slugify(value: str) -> str:
    return normalize_key(value).lower().replace(" ", "_")


def xmlid(kind: str, key: str) -> str:
    # Une cle qui ne laisse aucun caractere exploitable produirait un identifiant partage
    # par toutes les valeurs de ce genre, donc un seul enregistrement Odoo pour plusieurs
    # lignes source. Echouer bruyamment plutot que fusionner en silence.
    slug = slugify(key)
    if not slug:
        raise ValueError(f"Identifiant externe vide pour {kind} : {key!r}")
    return f"{XMLID_PREFIX}_{kind}_{slug}"


def category_path(category: str, subcategory: str) -> str:
    return f"{category} / {subcategory}" if subcategory else category


def to_number(value: str) -> str:
    """Decimale FR (63,27) vers le format attendu par le convertisseur Odoo (63.27)."""
    return str(value).strip().replace(",", ".")


def read_csv(filename: str) -> list[dict[str, str]]:
    path = FOLDER / filename
    if not path.exists():
        raise FileNotFoundError(
            f"{filename} introuvable. Lancer d'abord : pyenv exec python prepare_migration_files.py"
        )
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def read_catalog() -> list[dict[str, str]]:
    """Catalogue importable : produits, tarifs et couts partent tous de la meme liste.

    Les references dont l'EUROCODE n'a pas un format exploitable sont exclues (D3) : sans
    x_studio_eurocode valide, elles seraient invisibles au widget rpbm_agent - qui en creerait
    des doublons - et non synchronisables a vie, tout en occupant une fiche Odoo.
    eurocode_format_valide est la seule source de verite sur ce point.
    """
    return [
        row for row in read_csv("products_to_import.csv")
        if row["eurocode_format_valide"] == "true"
    ]


def excluded_references() -> list[str]:
    """Les references ecartees par read_catalog(), pour les signaler a l'execution."""
    return [
        row["product_reference"] for row in read_csv("products_to_import.csv")
        if row["eurocode_format_valide"] != "true"
    ]


def chunked(rows: Sequence[list[str]], size: int = CHUNK_SIZE) -> Iterator[list[list[str]]]:
    for start in range(0, len(rows), size):
        yield list(rows[start:start + size])


def load_env(path: Path = ENV_PATH) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"Fichier de secrets introuvable : {path}")
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("'\"")
    return values


# --- Client Odoo -----------------------------------------------------------------------


class Odoo:
    """Client XML-RPC minimal. Les lectures sont toujours autorisees, les ecritures
    seulement si commit est vrai."""

    def __init__(self, url: str, commit: bool) -> None:
        env = load_env()
        missing = [
            key for key in ("RPBM_PREPROD_DB", "RPBM_USERNAME", "RPBM_PASSWORD")
            if not env.get(key)
        ]
        if missing:
            raise RuntimeError(f"Variables absentes de {ENV_PATH} : {', '.join(missing)}")

        self.url = url.rstrip("/")
        self.db = env["RPBM_PREPROD_DB"]
        self.password = env["RPBM_PASSWORD"]
        self.commit = commit

        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.uid = common.authenticate(self.db, env["RPBM_USERNAME"], self.password, {})
        if not self.uid:
            raise RuntimeError(f"Echec d'authentification Odoo sur {self.url}.")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    def execute(self, model: str, method: str, *args, **kwargs):
        return self.models.execute_kw(self.db, self.uid, self.password, model, method, list(args), kwargs)

    def search_read(self, model: str, domain: list, fields: list[str], limit: int = 0) -> list[dict]:
        return self.execute(model, "search_read", domain, fields=fields, limit=limit)

    def search_count(self, model: str, domain: list) -> int:
        return self.execute(model, "search_count", domain)

    def field_names(self, model: str) -> set[str]:
        return set(self.execute(model, "fields_get", [], attributes=["type"]))

    def resolve_id(self, model: str, domain: list, label: str) -> int:
        found = self.search_read(model, domain, ["id"], limit=1)
        if not found:
            raise RuntimeError(f"{label} introuvable dans Odoo ({model} {domain}).")
        return found[0]["id"]

    def company_id(self) -> int:
        return self.search_read("res.users", [["id", "=", self.uid]], ["company_id"])[0]["company_id"][0]

    def load(self, model: str, fields: list[str], rows: list[list[str]], label: str) -> dict:
        """Charge par lots. Retourne un compte rendu agrege."""
        report = {"sent": len(rows), "loaded": 0, "failed": 0, "messages": []}
        if not rows:
            print(f"  {label} : rien a charger.")
            return report

        if not self.commit:
            print(f"  {label} : {len(rows)} ligne(s) pretes (dry-run, aucune ecriture).")
            for row in rows[:3]:
                print(f"    {dict(zip(fields, row))}")
            if len(rows) > 3:
                print(f"    ... et {len(rows) - 3} autre(s)")
            return report

        for index, chunk in enumerate(chunked(rows), start=1):
            result = self.execute(
                model, "load", fields, chunk,
                context={"tracking_disable": True, "mail_create_nolog": True},
            )
            ids = result.get("ids")
            if ids:
                report["loaded"] += len(ids)
            else:
                report["failed"] += len(chunk)
                report["messages"].extend(result.get("messages", []))
                print(f"  {label} : lot {index} REJETE ({len(chunk)} lignes).")
        print(f"  {label} : {report['loaded']} charge(s), {report['failed']} en echec.")
        return report


# --- Construction des lignes (pur, testable hors ligne) --------------------------------


def build_categories() -> tuple[list[list[str]], list[list[str]]]:
    """Retourne (racines, sous-categories). Les deux lots sont charges separement : les
    racines se rattachent a une categorie Odoo existante par identifiant base, les
    sous-categories a leur parent par identifiant externe."""
    roots, children = [], []
    for row in read_csv("categories_odoo_proposition.csv"):
        if row["odoo_action"] != "create":
            continue
        path = row["category_name"]
        name = path.split(" / ")[-1].strip()
        entry_id = xmlid("categ", path)
        if row["parent_category"] == "Autres":
            children.append([entry_id, name, xmlid("categ", "Autres")])
        else:
            roots.append([entry_id, name])
    return roots, children


def build_warehouses() -> list[list[str]]:
    return [[xmlid("wh", name), name, code] for name, code in WAREHOUSES]


def build_locations() -> tuple[list[list[str]], list[list[str]], list[dict], list[dict]]:
    """Retourne (emplacements internes, casse, deja resolus, anomalies).

    Les PLACE deja resolues (entrepots source, racine D2 existante) ne sont pas recreees.
    Les racks couverts par la repartition RPBM du 2026-08-05 (colonne warehouse du mapping)
    vont sous le stock de leur depot. Tout le reste reste cree sous "A controler" : aucune
    donnee perdue, aucun rattachement devine, reprise par reimport une fois arbitre.

    Regroupement sur la valeur normalisee, pour la meme raison que le catalogue produits :
    CASSE et Casse designent le meme endroit. Les valeurs sans aucun caractere exploitable
    (!!!, -, ?) ne sont pas des emplacements et sortent en anomalie.
    """
    grouped: dict[str, list[dict[str, str]]] = {}
    skipped, anomalies = [], []
    for row in read_csv("locations_mapping.csv"):
        if row["mapping_status"] in {"source_warehouse", "existing_root"}:
            skipped.append(row)
            continue
        key = normalize_key(row["source_place"])
        if not key:
            anomalies.append(row)
            continue
        grouped.setdefault(key, []).append(row)

    internal, scrap = [], []
    for key, entries in sorted(grouped.items()):
        best = max(entries, key=lambda entry: int(entry["source_row_count"]))
        place = best["source_place"]
        if key == "CASSE":
            scrap.append([xmlid("loc", key), place])
        else:
            # Le nom retenu est la cle normalisee des qu'un depot est tranche : deux graphies
            # d'un meme rack (J11A / J11a) doivent donner un seul emplacement Odoo.
            warehouse = best["warehouse"] if best["mapping_status"] == "mapped" else ""
            internal.append([
                xmlid("loc", key), key if warehouse else place, warehouse,
            ])
    return internal, scrap, skipped, anomalies


def build_suppliers() -> tuple[list[list[str]], list[dict[str, str]]]:
    """Un partenaire par fournisseur reel, doublons de casse fusionnes.

    VSF est exclu sans exception : le partenaire existe deja (VSF - VITRO SERVICE FRANCE)
    et rpbm_agent s'y refere par son identifiant. En creer un second casserait
    definitivement l'historisation des prix du module.
    """
    grouped: dict[str, list[dict[str, str]]] = {}
    excluded = []
    for row in read_csv("suppliers_mapping.csv"):
        key = normalize_key(row["source_frs"])
        if key.startswith("VSF") or key in NON_SUPPLIER_KEYS:
            excluded.append(row)
            continue
        grouped.setdefault(key, []).append(row)

    rows = []
    for key, entries in sorted(grouped.items()):
        # Orthographe retenue : celle de la variante la plus frequente dans la source.
        best = max(entries, key=lambda entry: int(entry["row_count"]))
        rows.append([xmlid("partner", key), best["source_frs"].strip(), "1", "company"])
    return rows, excluded


def build_products() -> tuple[list[str], list[list[str]]]:
    """Tous les articles sont stockables (D2) et portent un eurocode valide (D3).

    x_studio_eurocode est renseigne sans condition : rpbm_agent est un prerequis de la phase
    (D5) et le catalogue est deja filtre par read_catalog().
    """
    fields = [
        "id", "name", "default_code", "categ_id/id", "detailed_type", "list_price",
        "x_studio_eurocode",
    ]
    rows = []
    for row in read_catalog():
        reference = row["product_reference"]
        rows.append([
            xmlid("prod", reference),
            row["product_name"] or reference,
            reference,
            xmlid("categ", category_path(row["target_category"], row["target_subcategory"])),
            "product",
            to_number(row["public_price"]),
            reference,
        ])
    return fields, rows


def build_supplierinfo(today: str) -> tuple[list[list[str]], list[list[str]]]:
    """Retourne (lignes VSF, lignes autres fournisseurs).

    date_start est systematiquement renseignee : sans elle la ligne est active pour
    toujours et l'historisation J-1/J de rpbm_agent ne peut plus fonctionner.
    """
    vsf, others = [], []
    for row in read_catalog():
        price = to_number(row["purchase_price"])
        if not price:
            continue
        reference = row["product_reference"]
        supplier = row["supplier"]
        key = normalize_key(supplier)
        if key.startswith("VSF"):
            vsf.append([
                xmlid("seller", f"{reference} vsf"), xmlid("prod", reference),
                str(VSF_PARTNER_ID), price, today, reference,
            ])
        elif key and key not in NON_SUPPLIER_KEYS:
            others.append([
                xmlid("seller", f"{reference} {key}"), xmlid("prod", reference),
                xmlid("partner", key), price, today, reference,
            ])
    return vsf, others


def build_costs() -> list[tuple[str, float]]:
    """Cout Odoo = PRIX RV (D6), fret inclus (D7). Les references sans PRIX RV exploitable
    sont exclues plutot que forcees a zero."""
    costs = []
    for row in read_catalog():
        value = to_number(row["cost_price"])
        if value:
            costs.append((row["product_reference"], float(value)))
    return costs


# --- Phases ----------------------------------------------------------------------------


def phase_categories(odoo: Odoo, limit: int | None) -> None:
    roots, children = build_categories()
    parent_id = odoo.resolve_id(
        "product.category", [["complete_name", "=", "All / Saleable"]], "Categorie All / Saleable"
    )
    print(f"Categories : {len(roots)} racine(s), {len(children)} sous-categorie(s).")
    print(f"  Valorisation : cout {COST_METHOD}, inventaire {VALUATION} (D8).")
    valuation = [COST_METHOD, VALUATION]
    odoo.load(
        "product.category",
        ["id", "name", "parent_id/.id", "property_cost_method", "property_valuation"],
        [row + [str(parent_id)] + valuation for row in roots[:limit]], "racines",
    )
    odoo.load(
        "product.category",
        ["id", "name", "parent_id/id", "property_cost_method", "property_valuation"],
        [row + valuation for row in children[:limit]], "sous-categories",
    )


def phase_warehouses(odoo: Odoo, limit: int | None) -> None:
    rows = build_warehouses()[:limit]
    existing = odoo.search_read("stock.warehouse", [], ["name", "code"])
    print(f"Entrepots : {len(rows)} cible(s). Existants : {[w['name'] for w in existing]}")
    print(
        "  Q1 encore ouverte : 5 entrepots distincts ou 1 entrepot a 5 zones. Si la reponse est\n"
        "  « 1 entrepot », cette phase n'a pas lieu d'etre et P3 rattache les emplacements a\n"
        "  l'arborescence existante.\n"
        "  Rappel : les 434 emplacements sous RPBM/Stock D1 et D2 ne sont pas migres par cette\n"
        "  phase. Leur promotion en entrepots autonomes est une restructuration, pas une creation."
    )
    odoo.load("stock.warehouse", ["id", "name", "code"], rows, "entrepots")


def phase_locations(odoo: Odoo, limit: int | None) -> None:
    internal, scrap, skipped, anomalies = build_locations()
    physical = odoo.resolve_id(
        "stock.location", [["complete_name", "=", "Physical Locations"]], "Physical Locations"
    )
    virtual = odoo.resolve_id(
        "stock.location", [["complete_name", "=", "Virtual Locations"]], "Virtual Locations"
    )
    by_warehouse: dict[str, list[list[str]]] = {}
    for entry_id, name, warehouse in internal:
        by_warehouse.setdefault(warehouse, []).append([entry_id, name])
    unresolved = by_warehouse.pop("", [])
    print(
        f"Emplacements : {len(internal)} a creer ({len(unresolved)} sous "
        f"« {UNRESOLVED_LOCATION} », {len(internal) - len(unresolved)} rattaches a un depot), "
        f"{len(scrap)} en casse, {len(skipped)} deja resolus (ignores)."
    )
    for warehouse, rows in sorted(by_warehouse.items()):
        print(f"  {warehouse} : {len(rows)} emplacement(s).")
    if unresolved:
        print(f"  Non rattaches, a arbitrer manuellement : {len(unresolved)}")
        for entry_id, name in unresolved:
            print(f"    {name!r}")
    if anomalies:
        print(f"  {len(anomalies)} valeur(s) PLACE non exploitables, non importees :")
        for row in anomalies:
            print(f"    {row['source_place']!r} ({row['source_row_count']} ligne(s) source)")

    odoo.load(
        "stock.location", ["id", "name", "location_id/.id", "usage"],
        [[xmlid("loc", UNRESOLVED_LOCATION), UNRESOLVED_LOCATION, str(physical), "internal"]],
        "emplacement tampon",
    )
    odoo.load(
        "stock.location", ["id", "name", "location_id/id", "usage"],
        [row + [xmlid("loc", UNRESOLVED_LOCATION), "internal"] for row in unresolved[:limit]],
        f"emplacements sous {UNRESOLVED_LOCATION}",
    )
    # Chaque depot recoit ses racks sous son propre emplacement de stock : c'est lui qui porte
    # la disponibilite, pas la racine de l'entrepot.
    for warehouse, rows in sorted(by_warehouse.items()):
        found = odoo.search_read(
            "stock.warehouse", [["name", "=", warehouse]], ["lot_stock_id"], limit=1
        )
        if not found:
            # En dry-run la phase warehouses n'a pas encore ete validee : signaler sans
            # interrompre, pour que le blanc complet reste jouable d'un bout a l'autre.
            message = f"Entrepot {warehouse} introuvable : lancer la phase warehouses d'abord."
            if odoo.commit:
                raise RuntimeError(message)
            print(f"  {message} ({len(rows)} emplacement(s) non simules)")
            continue
        odoo.load(
            "stock.location", ["id", "name", "location_id/.id", "usage"],
            [row + [str(found[0]["lot_stock_id"][0]), "internal"] for row in rows[:limit]],
            f"emplacements {warehouse}",
        )
    # La casse ne doit jamais alimenter le stock vendable.
    odoo.load(
        "stock.location", ["id", "name", "location_id/.id", "usage", "scrap_location"],
        [row + [str(virtual), "inventory", "1"] for row in scrap[:limit]], "casse",
    )


def phase_suppliers(odoo: Odoo, limit: int | None) -> None:
    rows, excluded = build_suppliers()
    print(f"Fournisseurs : {len(rows)} partenaire(s) apres fusion des doublons de casse.")
    print(f"  Exclus (VSF ou valeur non-fournisseur) : {len(excluded)}")
    for row in excluded:
        print(f"    {row['source_frs']} ({row['row_count']} lignes)")
    odoo.load(
        "res.partner", ["id", "name", "supplier_rank", "company_type"], rows[:limit], "fournisseurs",
    )


def phase_products(odoo: Odoo, limit: int | None) -> None:
    if "x_studio_eurocode" not in odoo.field_names("product.template"):
        # Sans cette cle, le widget de rpbm_agent ne retrouve pas le produit migre : il en
        # cree un doublon et la fiche importee reste non synchronisable (reconciliation §2.1).
        raise SystemExit(
            "Phase interrompue : x_studio_eurocode absent de product.template.\n"
            "Installer rpbm_agent (pre_init_hook) AVANT l'import (D5), puis rejouer."
        )
    fields, rows = build_products()
    ecartes = excluded_references()
    print(f"Produits : {len(rows)} reference(s) stockable(s), colonnes : {', '.join(fields)}")
    if ecartes:
        # Non importees (D3) : leur eurocode n'en est pas un, la synchro VSF ne saurait pas
        # les retrouver. Elles restent dans le fichier Excel, a reprendre a la main si besoin.
        print(f"  {len(ecartes)} reference(s) exclue(s) pour format d'eurocode non exploitable :")
        for reference in ecartes:
            print(f"    {reference}")
    odoo.load("product.template", fields, rows[:limit], "produits")


def phase_supplierinfo(odoo: Odoo, limit: int | None) -> None:
    today = date.today().isoformat()
    vsf, others = build_supplierinfo(today)
    fields = ["id", "product_tmpl_id/id", "partner_id/{}", "price", "date_start", "product_code"]

    # Garde-fou P0-B (reconciliation §2.15) : _active_vsf_supplierinfo() leve une UserError
    # des que deux tarifs VSF sont actifs le meme jour, ce qui bloque definitivement la
    # synchronisation du produit. Decision RPBM du 2026-08-05 : dater les lignes preexistantes
    # au jour de l'import et ne pas leur en ajouter une seconde. La ligne conservee est reprise
    # par la premiere synchronisation, qui l'historise elle-meme si le prix a change.
    existing = odoo.search_read(
        "product.supplierinfo", [["partner_id", "=", VSF_PARTNER_ID]],
        ["product_tmpl_id", "date_start", "date_end"],
    )
    actives = [
        line for line in existing
        if line["product_tmpl_id"] and not line["date_end"]
    ]
    sans_date = [line["id"] for line in actives if not line["date_start"]]
    if sans_date:
        print(f"  {len(sans_date)} tarif(s) VSF actifs sans date_start : datation au {today}.")
        if odoo.commit:
            odoo.execute("product.supplierinfo", "write", sans_date, {"date_start": today})

    if actives:
        # Seuls les produits deja porteurs d'un identifiant externe de cet import peuvent
        # entrer en collision : un produit inconnu de l'import recevra sa propre fiche, donc
        # sa propre ligne de tarif, sans jamais en cumuler deux sur le meme enregistrement.
        deja = odoo.search_read(
            "ir.model.data",
            [["module", "=", XMLID_MODULE], ["model", "=", "product.template"],
             ["res_id", "in", [line["product_tmpl_id"][0] for line in actives]]],
            ["name"],
        )
        proteges = {row["name"] for row in deja}
        avant = len(vsf)
        vsf = [row for row in vsf if row[1] not in proteges]
        print(
            f"  {len(actives)} produit(s) portent deja un tarif VSF actif "
            f"({len(proteges)} issus de cet import) ; "
            f"{avant - len(vsf)} ligne(s) ecartee(s) pour ne pas les doubler."
        )

    print(f"Prix fournisseurs : {len(vsf)} ligne(s) VSF, {len(others)} ligne(s) autres.")
    odoo.load(
        "product.supplierinfo", [f.format(".id") for f in fields], vsf[:limit], "tarifs VSF",
    )
    odoo.load(
        "product.supplierinfo", [f.format("id") for f in fields], others[:limit], "tarifs autres",
    )


def phase_costs(odoo: Odoo, limit: int | None) -> None:
    costs = build_costs()[:limit]
    company = odoo.company_id()
    print(f"Couts : {len(costs)} reference(s) avec un PRIX RV exploitable (fret inclus, D7).")
    print(
        f"  Aucun impact comptable (D8) : categories en cout {COST_METHOD} / valorisation\n"
        f"  {VALUATION}, et _change_standard_price sort sur quantity_svl <= 0 - or les produits\n"
        "  crees en phase products n'ont pas de stock, celui-ci etant hors perimetre. Ni couche\n"
        "  de valorisation, ni ecriture comptable."
    )
    if not odoo.commit:
        for reference, value in costs[:3]:
            print(f"    {reference} -> {value}")
        return

    # standard_price est company_dependent : sans allowed_company_ids, la valeur atterrit
    # dans la societe de l'utilisateur d'integration. Ecriture sur le variant, car l'inverse
    # du template est ignore silencieusement quand il porte plusieurs variantes.
    context = {"allowed_company_ids": [company]}
    written = 0
    for reference, value in costs:
        found = odoo.execute(
            "product.product", "search", [["default_code", "=", reference]], limit=1
        )
        if not found:
            print(f"  Introuvable, ignore : {reference}")
            continue
        odoo.execute("product.product", "write", found, {"standard_price": value}, context=context)
        written += 1
    print(f"  {written} cout(s) ecrit(s) pour la societe {company}.")


def phase_check(odoo: Odoo, limit: int | None) -> None:
    imported = [["module", "=", XMLID_MODULE], ["name", "like", f"{XMLID_PREFIX}_%"]]
    print("Controles post-import :\n")
    for label, model, domain in [
        ("Categories importees", "ir.model.data", imported + [["model", "=", "product.category"]]),
        ("Entrepots importes", "ir.model.data", imported + [["model", "=", "stock.warehouse"]]),
        ("Emplacements importes", "ir.model.data", imported + [["model", "=", "stock.location"]]),
        ("Fournisseurs importes", "ir.model.data", imported + [["model", "=", "res.partner"]]),
        ("Produits importes", "ir.model.data", imported + [["model", "=", "product.template"]]),
        ("Tarifs importes", "ir.model.data", imported + [["model", "=", "product.supplierinfo"]]),
        ("Produits sans eurocode Studio", "product.template", [["x_studio_eurocode", "=", False]]),
        ("Produits a cout nul", "product.product", [["standard_price", "=", 0]]),
    ]:
        try:
            print(f"  {label:38} {odoo.search_count(model, domain)}")
        except xmlrpc.client.Fault as error:
            print(f"  {label:38} non evaluable ({error.faultString.splitlines()[-1]})")

    # Le controle qui compte : plus d'un tarif actif par produit bloque la synchro VSF.
    lignes = odoo.search_read(
        "product.supplierinfo", [["date_end", "=", False]], ["product_tmpl_id", "partner_id"]
    )
    doublons: dict[tuple, int] = {}
    for ligne in lignes:
        if ligne["product_tmpl_id"] and ligne["partner_id"]:
            cle = (ligne["product_tmpl_id"][0], ligne["partner_id"][0])
            doublons[cle] = doublons.get(cle, 0) + 1
    conflits = [cle for cle, count in doublons.items() if count > 1]
    bloquants = [cle for cle in conflits if cle[1] == VSF_PARTNER_ID]
    print(f"\n  Produits avec plusieurs tarifs actifs pour un meme fournisseur : {len(conflits)}")
    print(f"  dont sur le partenaire VSF (bloquant) : {len(bloquants)}")
    if bloquants:
        print(
            "  Doit etre a zero : sync_vsf_information() leve une UserError sur ces produits.\n"
            f"  Templates concernes : {[cle[0] for cle in bloquants]}"
        )
    elif conflits:
        print(
            "  Non bloquant pour la synchronisation VSF, mais Odoo choisit alors le tarif par\n"
            "  ordre (sequence, min_qty, prix) : a arbitrer avec le metier."
        )


# --- Verification hors ligne -----------------------------------------------------------


def phase_selfcheck() -> None:
    """Verifie la logique non triviale sans reseau ni Odoo."""
    assert slugify("Glace latérale") == slugify("Glace laterale") == "glace_laterale"
    assert slugify("Autres / Lève-vitre") == "autres_leve_vitre"
    assert category_path("Autres", "Optique") == "Autres / Optique"
    assert category_path("Joint", "") == "Joint"
    assert slugify(category_path("Autres", "Cache retro")) == slugify("Autres / Cache rétro")

    assert to_number("63,27") == "63.27"
    assert to_number("1116") == "1116"
    assert to_number("") == ""

    assert normalize_key("Vsf Centre") == normalize_key("VSF CENTRE") == "VSF CENTRE"
    assert normalize_key("VSF Ouest").startswith("VSF")
    assert normalize_key("A+ Glass") == normalize_key("A+ GLASS")

    lots = list(chunked([[str(i)] for i in range(450)]))
    assert [len(lot) for lot in lots] == [200, 200, 50], "dernier lot partiel"

    roots, children = build_categories()
    assert len(children) == 7, f"7 sous-categories attendues, {len(children)} trouvees"
    assert all(child[2] == xmlid("categ", "Autres") for child in children)
    ids = [row[0] for row in roots + children]
    assert len(ids) == len(set(ids)), "identifiants externes de categorie en doublon"

    fields, rows = build_products()
    assert fields[-1] == "x_studio_eurocode"
    assert len(fields) == len(rows[0]), "colonnes et valeurs desalignees"
    # D3 : les references au format d'eurocode douteux ne sont pas importees du tout. Le garde-fou
    # porte donc sur leur absence, et non plus sur un x_studio_eurocode laisse vide.
    ecartes = excluded_references()
    assert ecartes, "aucune reference exclue : le filtre de format est-il encore actif ?"
    references = {row[2] for row in rows}
    assert not (references & set(ecartes)), \
        "une reference au format d'eurocode suspect s'est glissee dans le lot produits"
    assert len(rows) + len(ecartes) == len(read_csv("products_to_import.csv")), \
        "des lignes du catalogue ne sont ni importees ni exclues"

    vsf, others = build_supplierinfo("2026-07-30")
    assert all(row[4] == "2026-07-30" for row in vsf + others), "date_start obligatoire"
    assert all(row[2] == str(VSF_PARTNER_ID) for row in vsf), "VSF doit pointer le partenaire 5708"
    seller_ids = [row[0] for row in vsf + others]
    assert len(seller_ids) == len(set(seller_ids)), "identifiants externes de tarif en doublon"

    partners, excluded = build_suppliers()
    noms = [row[1] for row in partners]
    assert not any(normalize_key(nom).startswith("VSF") for nom in noms), "VSF ne doit pas etre cree"
    assert len({row[0] for row in partners}) == len(partners), "doublons de casse non fusionnes"
    assert any(normalize_key(row["source_frs"]).startswith("VSF") for row in excluded)

    internal, scrap, skipped, anomalies = build_locations()
    assert len(scrap) == 1, "les variantes de casse de CASSE doivent etre fusionnees"
    depots = {row[2] for row in internal if row[2]}
    assert depots == {"Depot 1", "Depot 2"}, f"depots inattendus : {depots}"
    assert {name for name, code in WAREHOUSES} >= depots, "depot cible absent de WAREHOUSES"
    # Un rack rattache doit porter la cle normalisee, sinon deux graphies creeraient deux
    # emplacements sous le meme depot.
    assert all(row[1] == normalize_key(row[1]) for row in internal if row[2])
    loc_ids = [row[0] for row in internal + scrap]
    assert len(loc_ids) == len(set(loc_ids)), "identifiants externes d'emplacement en doublon"

    # Un identifiant externe partage ferait fusionner plusieurs lignes source dans un seul
    # enregistrement Odoo, sans erreur ni trace. C'est le mode de defaillance le plus couteux
    # de cet import : verifier l'unicite sur tous les genres d'identifiants.
    for genre, valeurs in [
        ("categorie", ids), ("produit", [row[0] for row in rows]),
        ("tarif", seller_ids), ("fournisseur", [row[0] for row in partners]),
        ("emplacement", loc_ids), ("entrepot", [row[0] for row in build_warehouses()]),
    ]:
        assert len(valeurs) == len(set(valeurs)), f"identifiants externes {genre} en doublon"

    # Tout produit cree porte la cle de re-synchronisation VSF, egale a sa reference : c'est ce
    # que garantit l'exclusion en amont (reconciliation §2.1 et §2.13).
    eurocode_index = fields.index("x_studio_eurocode")
    reference_index = fields.index("default_code")
    assert all(row[eurocode_index] == row[reference_index] for row in rows), \
        "x_studio_eurocode doit valoir la reference sur chaque produit"

    # Le filtre doit s'appliquer aux trois constructeurs : un tarif ou un cout qui porterait sur
    # une reference non importee serait rejete par Odoo au chargement, lot entier compris.
    couts = build_costs()
    assert {reference for reference, _ in couts} <= references, \
        "un cout porte sur une reference absente du lot produits"
    tarif_refs = {row[5] for row in vsf + others}
    assert tarif_refs <= references, "un tarif porte sur une reference absente du lot produits"

    try:
        xmlid("loc", "!!!")
    except ValueError:
        pass
    else:  # pragma: no cover - garde-fou
        raise AssertionError("une cle sans caractere exploitable doit etre refusee")

    print("selfcheck : OK")
    print(f"  {len(roots)} categories racines, {len(children)} sous-categories")
    print(f"  {len(rows)} produits, {len(partners)} fournisseurs ({len(excluded)} exclus)")
    print(f"  {len(vsf)} tarifs VSF, {len(others)} tarifs autres")
    rattaches = sum(1 for row in internal if row[2])
    print(
        f"  {len(internal)} emplacements a creer ({rattaches} rattaches a un depot, "
        f"{len(internal) - rattaches} sous « {UNRESOLVED_LOCATION} »), "
        f"{len(skipped)} deja resolus, {len(anomalies)} anomalies"
    )
    print(f"  {len(couts)} couts exploitables")
    print(f"  {len(ecartes)} reference(s) exclue(s) : format d'eurocode non exploitable (D3)")
    print(f"  valorisation : cout {COST_METHOD}, inventaire {VALUATION} (D8)")


# --- Entree ----------------------------------------------------------------------------


PHASES = {
    "categories": phase_categories,
    "warehouses": phase_warehouses,
    "locations": phase_locations,
    "suppliers": phase_suppliers,
    "products": phase_products,
    "supplierinfo": phase_supplierinfo,
    "costs": phase_costs,
    "check": phase_check,
}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("phase", choices=[*PHASES, "selfcheck"])
    parser.add_argument("--commit", action="store_true", help="ecrire reellement dans Odoo")
    parser.add_argument("--limit", type=int, help="limiter le nombre de lignes (essai)")
    parser.add_argument("--url", default=DEFAULT_URL)
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.phase == "selfcheck":
        phase_selfcheck()
        return 0

    odoo = Odoo(args.url, args.commit)
    mode = "ECRITURE" if args.commit else "dry-run (aucune ecriture)"
    print(f"Phase {args.phase} sur {args.url} — {mode}\n")
    PHASES[args.phase](odoo, args.limit)
    if not args.commit:
        print("\nAucune ecriture effectuee. Relancer avec --commit pour appliquer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
