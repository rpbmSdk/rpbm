from __future__ import annotations

import csv
import re
import unicodedata
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable


FOLDER = Path(__file__).resolve().parent
CSV_PATH = FOLDER / "Gestion Stock V4 - Stock Complet.csv"
INVALID_CODES = {"0", "-", "---", "?"}

# Valeurs normalisees de la colonne FRS qui ne designent pas un fournisseur. Definies ici plutot
# que dans import_odoo.py, qui importe ce module : une seule liste pour les deux scripts.
NON_SUPPLIER_KEYS = {
    "", "-", "??", "?", "INVENTAIRE", "CLIENT", "PALETTE A IDENTIFIER",
    "CENTRE", "OCCASION", "OCCCASION", "CENTRALE CASSE",
}

SOURCE_COLUMNS = {
    "other_code": 4,
    "eurocode": 5,
    "source_type": 6,
    "designation": 7,
    "frs": 8,
    "quantity_current": 9,
    "public_price": 10,
    "purchase_price": 11,
    "cost_price": 13,
    "place": 19,
    "date_exit": 20,
    "inventory_status": 22,
    "inventory_notes": 23,
    "inventory_state": 25,
    "internal_eurocode": 58,
}

# Une ligne n'est exploitable que si elle porte les colonnes indispensables (jusqu'a INV ETAT,
# index 25). Les colonnes situees au-dela (EUROCODE INTERNE en 58) sont facultatives : le CSV
# source a 60 colonnes mais des lignes plus courtes existent, et filtrer sur l'index maximum
# ferait perdre des articles valides.
REQUIRED_MAX_INDEX = 25

# Format plausible d'un eurocode VSF (voir docs/cartographie/reconciliation-stock-rpbm-agent.md
# §2.13) : alphanumerique + tiret, 4 a 15 caracteres. Rejette les annotations entre parentheses,
# les suffixes de statut ("-PERDU"), le texte libre et les valeurs concatenees observees dans le
# fichier source - sans verification live contre VSF (ecartee pour l'instant, risque de
# detection du portail, cf. meme document).
EUROCODE_FORMAT_RE = re.compile(r"^[A-Z0-9-]{4,15}$", re.IGNORECASE)


def eurocode_format_valide(eurocode: str) -> bool:
    return bool(EUROCODE_FORMAT_RE.fullmatch(str(eurocode).strip()))


# Repartition des racks entre depots deportes (reponse RPBM du 2026-08-05) :
#   R101 a R336 -> Depot 1 ; R401 a R937, J..., T... -> Depot 2.
# Les bornes tombent sur la frontiere reelle des blocs (R3xx s'arrete a 336, R4xx commence
# a 401), la regle est donc exacte et non une approximation.
DEPOT1_RACKS = (101, 336)
DEPOT2_RACKS = (401, 937)
RACK_RE = re.compile(r"R([0-9]+)")
# Un code J/T doit porter au moins un chiffre. Cela ecarte les libelles ("JDESSUS", "TRINGLE")
# que RPBM a explicitement demande de laisser non rattaches le 2026-08-05, sans avoir a les
# enumerer un par un.
DEPOT2_PREFIX_RE = re.compile(r"[JT](?=[0-9A-Z]*[0-9])[0-9A-Z]+")


def place_warehouse(key: str) -> str:
    """Entrepot deporte deduit d'un code emplacement normalise, "" si non rattachable.

    Ne tranche que ce que la reponse client couvre sans ambiguite. Tout le reste ("R35" hors
    plage, "R108 R109" multi-racks, contenants, statuts) retourne "" et part en "A controler".
    """
    rack = RACK_RE.fullmatch(key)
    if rack:
        number = int(rack.group(1))
        if DEPOT1_RACKS[0] <= number <= DEPOT1_RACKS[1]:
            return "Depot 1"
        if DEPOT2_RACKS[0] <= number <= DEPOT2_RACKS[1]:
            return "Depot 2"
        return ""
    return "Depot 2" if DEPOT2_PREFIX_RE.fullmatch(key) else ""


def normalize_key(value: str) -> str:
    normalized = unicodedata.normalize("NFD", str(value).strip().upper())
    normalized = "".join(
        char for char in normalized
        if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"[^A-Z0-9]+", " ", normalized).strip()


def parse_decimal(value: str) -> Decimal | None:
    text = str(value).strip().replace(" ", "")
    if not text:
        return None
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def format_decimal(value: Decimal | None) -> str:
    if value is None:
        return ""
    text = format(value.quantize(Decimal("0.001")), "f").rstrip("0").rstrip(".")
    return text.replace(".", ",")


def category_mapping(source_type: str) -> dict[str, str]:
    """Type source (colonne TYPE) vers categorie Odoo, et sous-categorie sous Autres.

    Decision RPBM du 2026-07-23 : hormis CAMERA, les regroupements rattaches a Autres
    (Optique, Retroviseur EXT/INT, Cache retro, Leve-vitre, Toit panoramique, Baie de
    pare-brise) sont de vraies sous-categories product.category, et non de simples regles
    de renommage de libelle article. categories_odoo_proposition.csv fait foi pour les
    libelles finaux; ce mapping doit rester aligne dessus."""
    key = normalize_key(source_type)
    category = "Autres"
    subcategory = ""
    notes = "Valeur source rare ou non documentee : categorie Odoo Autres, classification manuelle requise."

    if key == "PARE BRISE":
        category = "Pare-brise"
        notes = "Type normalise; aucune sous-categorie Odoo."
    elif re.fullmatch(r"LUNETTES?", key):
        category = "Lunette"
        notes = "Type normalise; aucune sous-categorie Odoo."
    elif re.fullmatch(r"GLACES LATERALES?", key):
        category = "Glace laterale"
        notes = "Inclut glaces laterales, custodes et deflecteurs."
    elif re.fullmatch(r"(JOINTS?|ENJOLIVEURS?)", key):
        category = "Joint"
        notes = "Inclut joints et enjoliveurs."
    elif re.fullmatch(r"(TOIT|TOIT PANO|TOIT PANORAMIQUE|VITRE PAVILLON)", key):
        subcategory = "Toit panoramique"
        notes = "Sous-categorie Autres / Toit panoramique (decision RPBM du 2026-07-23)."
    elif re.fullmatch(r"(OPTIQUE|OPTIQUES|FEU|PHARE|PHARES|FAISCEAU|ANTIBROUILLARD)", key):
        subcategory = "Optique"
        notes = "Sous-categorie Autres / Optique (decision RPBM du 2026-07-23)."
    elif key == "RETROVISEUR INT":
        subcategory = "Retroviseur INT"
        notes = "Sous-categorie Autres / Retroviseur INT (decision RPBM du 2026-07-23)."
    elif key == "RETROVISEUR":
        subcategory = "Retroviseur EXT"
        notes = "Sous-categorie Autres / Retroviseur EXT (decision RPBM du 2026-07-23); libelle source RETROVISEUR renomme."
    elif key.startswith("CACHE RETRO"):
        subcategory = "Cache retro"
        notes = "Sous-categorie Autres / Cache retro (decision RPBM du 2026-07-23)."
    elif re.fullmatch(r"(LEVE VITRE|MECANISME LV|MECANISME)", key):
        subcategory = "Leve-vitre"
        notes = "Sous-categorie Autres / Leve-vitre (decision RPBM du 2026-07-23)."
    elif key == "BAIE DE PARE BRISE":
        subcategory = "Baie de pare-brise"
        notes = "Sous-categorie Autres / Baie de pare-brise (decision RPBM du 2026-07-23), source rare."
    elif key == "CAMERA":
        notes = "Article rare : categorie Odoo Autres, aucune sous-categorie Camera (exception explicite)."
    elif key == "AUTRES":
        notes = "Categorie Odoo Autres; valeur fourre-tout controlee."
    elif not key:
        notes = "TYPE absent : classification manuelle requise."

    return {
        "source_type": source_type.strip() or "__VIDE__",
        "target_category": category,
        "target_subcategory": subcategory,
        # Tous les articles importes sont stockables sans exception (D2). Le regime des
        # consommables ne concerne que la saisie posterieure a la migration.
        "product_type": "product",
        "stockable": "true",
        "notes": notes,
    }


def read_source_rows() -> tuple[list[str], list[dict[str, str]]]:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV introuvable: {CSV_PATH}")

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        for _ in range(4):
            next(reader)
        header = next(reader)
        rows = []
        for fields in reader:
            if len(fields) < REQUIRED_MAX_INDEX + 1:
                continue
            rows.append({
                name: fields[index].strip() if index < len(fields) else ""
                for name, index in SOURCE_COLUMNS.items()
            })
    return header, rows


def write_csv(filename: str, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path = FOLDER / filename
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def location_mapping(article_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in article_rows:
        if row["place"]:
            grouped[row["place"]].append(row)

    output = []
    for source in sorted(grouped):
        key = normalize_key(source)
        warehouse = ""
        parent = ""
        target = ""
        status = "to_check"
        notes = f"Source observee sur {len(grouped[source])} ligne(s)."

        if key == "D2":
            warehouse = "RPBM"
            parent = "RPBM/Stock D2"
            target = "RPBM/Stock D2"
            status = "existing_root"
            notes += " Racine Odoo existante en preproduction."
        elif key == "CASSE":
            target = "Virtual Locations/RPBM: Scrap"
            status = "proposed"
            notes += " Ne doit pas alimenter le stock vendable."
        elif key in {"GALLERIA", "GENIPA"}:
            warehouse = source
            status = "source_warehouse"
            notes += " Entrepot source confirme; rattachement vers la structure Odoo a definir."
        elif key == "CENTRE":
            notes += " Nature de la zone et rattachement a un entrepot a confirmer."
        elif place_warehouse(key):
            warehouse = place_warehouse(key)
            target = f"{warehouse}/Stock/{key}"
            parent = f"{warehouse}/Stock"
            status = "mapped"
            notes += f" Rattache a {warehouse} (repartition RPBM du 2026-08-05)."
        else:
            notes += " Valeur heterogene : rattachement a confirmer."

        output.append({
            "source_place": source,
            "warehouse": warehouse,
            "location_parent": parent,
            "location_name": target.split("/")[-1] if target else "",
            "location_complete_name": target,
            "mapping_status": status,
            "source_row_count": len(grouped[source]),
            "notes": notes,
        })
    return output


def product_rows(article_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    # Regroupement sur l'eurocode normalise et non sur la chaine brute : la source contient
    # des variantes de casse (2454ASMC / 2454asmc) et d'espacement (6084BGNRZ-O /
    # 6084BGNRZ - O) du meme article. Les grouper sur la chaine exacte creerait deux fiches
    # Odoo pour une seule reference physique - exactement le doublon que la migration
    # cherche a eviter. L'orthographe retenue est la plus frequente dans la source.
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in article_rows:
        grouped[normalize_key(row["eurocode"])].append(row)

    output = []
    for key in sorted(grouped):
        group = grouped[key]
        first = group[0]
        spellings = defaultdict(int)
        for row in group:
            spellings[row["eurocode"]] += 1
        reference = max(sorted(spellings), key=lambda code: spellings[code])
        mapping = category_mapping(first["source_type"])
        names = list(dict.fromkeys(row["designation"] for row in group if row["designation"]))
        suppliers = list(dict.fromkeys(row["frs"] for row in group if row["frs"]))
        purchase_prices = [
            value for value in (parse_decimal(row["purchase_price"]) for row in group)
            if value is not None and value > 0
        ]
        public_prices = [
            value for value in (parse_decimal(row["public_price"]) for row in group)
            if value is not None and value > 0
        ]
        # Cout Odoo (standard_price) : colonne PRIX RV, decision RPBM du 2026-07-23.
        cost_prices = [
            value for value in (parse_decimal(row["cost_price"]) for row in group)
            if value is not None and value > 0
        ]
        places = list(dict.fromkeys(row["place"] for row in group if row["place"]))
        other_codes = list(dict.fromkeys(row["other_code"] for row in group if row["other_code"]))
        internal_codes = list(
            dict.fromkeys(row["internal_eurocode"] for row in group if row["internal_eurocode"])
        )
        divergent = any(normalize_key(code) != key for code in internal_codes)
        format_valide = eurocode_format_valide(reference)

        notes = (
            "Doublon source consolide : controler quantites, prix et emplacements."
            if len(group) > 1
            else "Rapprochement Odoo par default_code a effectuer."
        )
        if not format_valide:
            notes += (
                " EXCLUE DE L'IMPORT (decision RPBM du 2026-08-05, D3) : format d'eurocode"
                " suspect (annotation, code constructeur, texte libre). Sans x_studio_eurocode"
                " valide, la fiche serait invisible au widget rpbm_agent et non synchronisable."
                " A reprendre a la main dans le fichier Excel si la reference doit exister."
            )
        if divergent:
            notes += (
                " EUROCODE INTERNE diverge de EUROCODE : arbitrage RPBM requis sur la reference"
                " qui fait foi."
            )
        if not cost_prices:
            notes += " PRIX RV absent : standard_price non calculable, phase de cout a exclure."
        if len(spellings) > 1:
            notes += (
                " Variantes de casse/espacement fusionnees dans la source : "
                + ", ".join(sorted(spellings))
                + "."
            )

        output.append({
            "product_reference": reference,
            "product_name": names[0] if names else reference,
            "source_type": first["source_type"] or "__VIDE__",
            "target_category": mapping["target_category"],
            "target_subcategory": mapping["target_subcategory"],
            "product_type": mapping["product_type"],
            "stockable": mapping["stockable"],
            "eurocode_format_valide": "true" if format_valide else "false",
            "supplier": suppliers[0] if suppliers else "",
            "purchase_price": format_decimal(purchase_prices[0] if purchase_prices else None),
            "cost_price": format_decimal(cost_prices[0] if cost_prices else None),
            "public_price": format_decimal(public_prices[0] if public_prices else None),
            "other_code": other_codes[0] if other_codes else "",
            "internal_eurocode": internal_codes[0] if internal_codes else "",
            "eurocode_divergent": "true" if divergent else "false",
            "source_row_count": len(group),
            "source_places": " | ".join(places),
            # Affichage de la decision D3, derive de format_valide : import_odoo.py filtre sur
            # eurocode_format_valide, qui reste la seule source de verite.
            "import_status": "import" if format_valide else "exclusion_format_eurocode",
            "notes": notes,
        })
    return output


def supplier_mapping(article_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    """Un fournisseur (FRS) par ligne : a rapprocher d'un res.partner Odoo existant, ou a creer
    s'il est absent. Chaque produit rattache a besoin d'un product.supplierinfo (prix depuis
    PRIX ACHAT), que le fournisseur soit VSF ou non (D9).

    Toutes les variantes VSF designent le partenaire existant id 5708 (D10) : aucun second
    partenaire VSF n'est cree, il produirait deux prix concurrents que l'historisation de
    rpbm_agent ne reconcilie jamais."""
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in article_rows:
        if row["frs"]:
            grouped[row["frs"]].append(row)

    output = []
    for supplier in sorted(grouped, key=lambda s: -len(grouped[s])):
        rows = grouped[supplier]
        eurocodes = {row["eurocode"] for row in rows}
        is_vsf = normalize_key(supplier).startswith("VSF")
        output.append({
            "source_frs": supplier,
            "row_count": len(rows),
            "unique_eurocode_count": len(eurocodes),
            "odoo_partner_action": (
                "reutiliser rpbm_agent.vsf_partner_id (res.partner 5708, confirme le 2026-08-05)"
                if is_vsf
                else "rapprocher un res.partner existant, sinon creer"
            ),
            "notes": (
                "Variante VSF : meme partenaire Odoo que VSF Centre, id 5708 (D10). Aucun second"
                " partenaire VSF n'est cree."
                if is_vsf
                else "Creer product.supplierinfo (prix = PRIX ACHAT) pour chaque produit rattache."
            ),
        })
    return output


def read_reconciliation_section(expected_codes: set[str]) -> str:
    path = FOLDER / "product_reconciliation.csv"
    if not path.exists():
        # Le fichier du 20/07 vient de l'ancien pipeline PowerShell et a ete archive. Signaler
        # son absence plutot que de taire la section : le rapprochement par default_code reste
        # un prerequis de P0, sans lui l'import peut creer des doublons.
        return (
            "## Rapprochement catalogue Odoo\n\n"
            "Aucun product_reconciliation.csv : le rapprochement du catalogue candidat avec les "
            "default_code Odoo reste a produire (phase P0). Sans lui, l'import peut creer un "
            "doublon pour chaque reference deja presente dans Odoo.\n\n"
        )

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    reconciliation_codes = {
        row.get("product_reference", "")
        for row in rows
        if row.get("decision") != "odoo_only"
    }
    if reconciliation_codes != expected_codes:
        return (
            "## Rapprochement catalogue Odoo\n\n"
            "Le fichier product_reconciliation.csv existant ne correspond pas au catalogue candidat "
            "actuellement genere; il doit etre regenere apres une nouvelle lecture Odoo.\n\n"
        )
    counts = defaultdict(int)
    for row in rows:
        counts[row.get("decision", "")] += 1

    return (
        "## Rapprochement catalogue Odoo\n\n"
        "Lecture du catalogue Odoo realisee via Paradigme MCP et comparaison par default_code :\n\n"
        f"- {counts['create_candidate']} candidats source absents du catalogue Odoo;\n"
        f"- {counts['existing_review']} references source deja presentes dans Odoo;\n"
        f"- {counts['odoo_only']} produits Odoo avec reference absents du CSV candidat.\n\n"
        "Conclusion : aucune creation ne doit etre lancee sans validation du contenu "
        "des candidats et des produits Odoo sans reference interne exploitable.\n\n"
    )


def write_quality_report(
    article_rows: list[dict[str, str]],
    category_rows: list[dict[str, object]],
    location_rows: list[dict[str, object]],
    catalog_rows: list[dict[str, str]],
    product_rows_: list[dict[str, object]],
    supplier_rows: list[dict[str, object]],
) -> None:
    valid_rows = [
        row for row in article_rows
        if row["eurocode"] and row["eurocode"] != "0"
    ]
    invalid_rows = [row for row in valid_rows if row["eurocode"] in INVALID_CODES]
    catalog_rows = [row for row in valid_rows if row["eurocode"] not in INVALID_CODES]
    positive_rows = [
        row for row in article_rows
        if (parse_decimal(row["quantity_current"]) or Decimal("0")) > 0
    ]
    duplicate_counts = defaultdict(int)
    for row in valid_rows:
        duplicate_counts[row["eurocode"]] += 1
    duplicate_groups = sum(count > 1 for count in duplicate_counts.values())
    rows_without_exit = sum(not row["date_exit"] for row in valid_rows)
    quantity_total = sum(
        parse_decimal(row["quantity_current"]) or Decimal("0")
        for row in positive_rows
    )
    unique_codes = len(duplicate_counts)
    format_invalides = sum(1 for row in product_rows_ if row["eurocode_format_valide"] == "false")
    # Volumes reellement importes apres exclusion des eurocodes non exploitables (D3).
    importables = [row for row in product_rows_ if row["eurocode_format_valide"] == "true"]
    couts_importes = sum(1 for row in importables if row["cost_price"])
    tarifs_vsf = sum(
        1 for row in importables
        if row["purchase_price"] and normalize_key(row["supplier"]).startswith("VSF")
    )
    tarifs_autres = sum(
        1 for row in importables
        if row["purchase_price"] and row["supplier"]
        and not normalize_key(row["supplier"]).startswith("VSF")
        and normalize_key(row["supplier"]) not in NON_SUPPLIER_KEYS
    )
    sans_cout = sum(1 for row in product_rows_ if not row["cost_price"])
    divergents = sum(1 for row in product_rows_ if row["eurocode_divergent"] == "true")
    sous_categories = len({
        row["target_subcategory"] for row in category_rows if row["target_subcategory"]
    })

    report = f"""# Rapport de qualite des donnees de migration

Date de generation : {date.today().isoformat()}
Source : Gestion Stock V4 - Stock Complet.csv (export du 29/01/2025)
Statut : preparation uniquement, aucune ecriture Odoo.

## Source CSV

| Controle | Resultat |
|---|---:|
| Lignes articles avec EUROCODE | {len(valid_rows)} |
| EUROCODE uniques | {unique_codes} |
| References invalides (-, ---, ?) | {len(invalid_rows)} |
| References candidates import (eurocode normalise) | {len(product_rows_)} |
| Variantes de casse/espacement fusionnees | {len({row['eurocode'] for row in catalog_rows}) - len(product_rows_)} |
| EUROCODE apparaissant plusieurs fois | {duplicate_groups} |
| Lignes avec quantite actuelle positive | {len(positive_rows)} |
| Quantite positive totale | {quantity_total} |
| Lignes sans DATE SORTIE | {rows_without_exit} |
| Emplacements source distincts | {len(location_rows)} |
| Types source distincts | {len({row['source_type'] or '__VIDE__' for row in valid_rows})} |
| EUROCODE au format suspect, exclu de l'import (D3) | {format_invalides} |
| **References effectivement importees** | **{len(importables)}** |
| Fournisseurs (FRS) source distincts | {len(supplier_rows)} |
| References sans PRIX RV (cout non calculable) | {sans_cout} |
| References dont EUROCODE INTERNE diverge de EUROCODE | {divergents} |
| Sous-categories Autres distinctes | {sous_categories} |

Volumes par phase d'import, apres exclusion : {len(importables)} produits,
{tarifs_vsf} tarifs VSF + {tarifs_autres} tarifs autres fournisseurs, {couts_importes} couts.

## Odoo preproduction lu via Paradigme MCP (releve du 2026-07-22)

- 13 categories produits existantes.
- 169 produits existants : 58 stockables, 75 consommables, 36 services.
- 1 entrepot actif : RPBM.
- 438 emplacements internes, dont 434 sous RPBM/Stock D1 et RPBM/Stock D2.
- Les categories existantes utilisent des politiques mixtes : average/real_time et standard/manual_periodic.

{read_reconciliation_section({row['eurocode'] for row in catalog_rows})}## Anomalies et risques

- Le CSV est anterieur a l'inventaire du 30/06/2026. Il ne constitue pas une source fiable pour le stock initial final.
- Les couleurs Google Sheets ne sont pas conservees dans le CSV; les statuts vendu/reserve/casse doivent etre confirmes par une colonne ou une source complementaire.
- GALLERIA et GENIPA sont des entrepots source; les valeurs JXX sont des emplacements dont l'entrepot parent reste a confirmer.
- La liste exhaustive des entrepots et le rattachement de chaque emplacement doivent etre fournis par les utilisateurs.
- Les lignes avec reference invalide sont exclues de products_to_import.csv et restent a investiguer.
- Le stock initial doit etre construit depuis l'inventaire valide du 30/06/2026.

## Prix fournisseurs et cout

- Les prix fournisseurs devront etre crees depuis PRIX ACHAT, apres rapprochement de FRS avec les fournisseurs Odoo.
- Decision RPBM du 2026-07-29 : ce rapprochement s'applique a **tous** les fournisseurs (FRS), pas seulement VSF - creer le res.partner Odoo manquant et le product.supplierinfo (PRIX ACHAT) pour chaque fournisseur non-VSF egalement (MPB, BLUE AUTO, A+ Glass, ...). Voir suppliers_mapping.csv.
- PRIX ACHAT est un prix unitaire; VALEUR (Av Fret) est probablement un montant de ligne avant fret : 760 lignes positives sur 768 suivent QTE Act x PRIX ACHAT.
- VALEUR est probablement un montant de ligne base sur PRIX RV : 761 lignes positives sur 768 suivent cette formule; elle ne doit pas devenir directement le cout unitaire Odoo.
- Decision RPBM du 2026-07-23 (D6) : le cout Odoo (standard_price) est la colonne PRIX RV, extraite dans products_to_import.csv (colonne cost_price). {sans_cout} references sur {len(product_rows_)} n'ont pas de PRIX RV exploitable et sont exclues de la phase de cout.
- Decision RPBM du 2026-08-05 (D7) : le fret est **inclus dans PRIX RV**. Aucune regle d'allocation a definir, la colonne FRET n'est pas reprise.
- Decision RPBM du 2026-08-05 (D8) : cout **standard** et valorisation **manuelle** - les valeurs par defaut d'Odoo 17, donc aucun compte comptable a parametrer. Ecrire standard_price sur des produits sans stock ne cree ni couche de valorisation ni ecriture comptable (_change_standard_price sort sur quantity_svl <= 0).

## Controle de format EUROCODE (2026-07-29, arbitre le 2026-08-05)

- {format_invalides} references sur {len(product_rows_)} (catalogue dedoublonne) ne passent pas le controle de format simple (alphanumerique + tiret, 4 a 15 caracteres) - voir eurocode_format_valide=false dans products_to_import.csv et la note associee sur chaque ligne concernee. Le format suspect indique une annotation, un code constructeur ou une donnee non-produit plutot qu'un vrai eurocode VSF.
- **Decision RPBM du 2026-08-05 (D3) : ces {format_invalides} references ne sont pas importees.** Sans x_studio_eurocode valide, elles seraient invisibles au widget rpbm_agent et non synchronisables a vie, tout en occupant une fiche Odoo. Le catalogue migre compte donc {len(importables)} produits.
- Verification live contre le portail VSF ecartee (decision RPBM du 2026-07-29, D15) : risque de se faire reperer par le portail. A documenter si reconsideree plus tard, voir docs/cartographie/reconciliation-stock-rpbm-agent.md.

## Fichiers produits

- categories_mapping.csv : mapping des types sources vers les categories et sous-categories cibles.
- locations_mapping.csv : mapping des emplacements source et anomalies de rattachement.
- suppliers_mapping.csv : fournisseurs (FRS) source distincts, a rapprocher d'un res.partner Odoo existant ou a creer.
- products_to_import.csv : catalogue dedoublonne par EUROCODE, avec fournisseur retenu, cout PRIX RV et controle de format eurocode. La colonne import_status distingue les references importees de celles exclues pour format d'eurocode. Les colonnes d'audit (other_code, internal_eurocode, source_places) restent presentes pour le controle local mais ne sont plus reprises dans Odoo (D4).
- stock_initial_to_import.csv : modele vide volontairement.

Ces fichiers alimentent import_odoo.py, qui execute l'import phase par phase (voir
plan-import-articles.md). Les identifiants externes Odoo sont derives des libelles et des
references par import_odoo.py, ils ne sont pas stockes dans ces CSV.

## Decisions bloquantes

Etat au 2026-08-05 - le detail est dans decisions.md et questions-ouvertes.md.

Tranchees : categories et typologie (tous stockables), rattachement D1/D2 des racks, methode de
cout et valorisation, identite du partenaire VSF (id 5708), sort des eurocodes suspects, fret.

Restent bloquantes :

1. **Forme des entrepots** : 5 entrepots distincts ou 1 entrepot a 5 zones. Conditionne la creation
   des entrepots et le parent des emplacements.
2. **Fournir le fichier corrige de l'inventaire du 30/06/2026** - sans lui, stock_initial_to_import.csv
   reste vide et l'import du stock ne peut pas etre prepare.
3. **Arbitrer l'ecart d'inventaire de 6 448,18 EUR.**

A noter, independamment : le lot_stock_id de l'entrepot RPBM pointe sur RPBM/Stock D1, dont
GALLERIA, GENIPA et Stock D2 sont des freres et non des enfants - seules 67 unites sur 799 sont
aujourd'hui reservables par une commande client. A corriger avant mise en service.
"""
    (FOLDER / "data_quality_report.md").write_text(report, encoding="utf-8")


def main() -> None:
    header, rows = read_source_rows()
    article_rows = [
        row for row in rows
        if row["eurocode"] and row["eurocode"] != "0"
    ]
    invalid_rows = [row for row in article_rows if row["eurocode"] in INVALID_CODES]
    catalog_rows = [row for row in article_rows if row["eurocode"] not in INVALID_CODES]

    source_types = sorted({row["source_type"] or "__VIDE__" for row in article_rows})
    category_rows = [category_mapping(source_type) for source_type in source_types]
    write_csv(
        "categories_mapping.csv",
        ["source_type", "target_category", "target_subcategory", "product_type", "stockable", "notes"],
        category_rows,
    )

    locations = location_mapping(article_rows)
    write_csv(
        "locations_mapping.csv",
        [
            "source_place", "warehouse", "location_parent", "location_name",
            "location_complete_name", "mapping_status", "source_row_count", "notes",
        ],
        locations,
    )

    products = product_rows(catalog_rows)
    write_csv(
        "products_to_import.csv",
        [
            "product_reference", "product_name", "source_type", "target_category",
            "target_subcategory", "product_type", "stockable", "eurocode_format_valide",
            "supplier", "purchase_price", "cost_price", "public_price", "other_code",
            "internal_eurocode", "eurocode_divergent", "source_row_count", "source_places",
            "import_status", "notes",
        ],
        products,
    )

    suppliers = supplier_mapping(article_rows)
    write_csv(
        "suppliers_mapping.csv",
        [
            "source_frs", "row_count", "unique_eurocode_count", "odoo_partner_action", "notes",
        ],
        suppliers,
    )

    write_csv(
        "stock_initial_to_import.csv",
        [
            "product_reference", "product_name", "category", "location", "quantity",
            "cost", "public_price", "status", "inventory_status", "notes",
        ],
        [],
    )
    write_quality_report(article_rows, category_rows, locations, catalog_rows, products, suppliers)

    unique_codes = len({row["eurocode"] for row in article_rows})
    merged = len({row["eurocode"] for row in catalog_rows}) - len(products)
    format_invalides = sum(1 for row in products if row["eurocode_format_valide"] == "false")
    print(f"Source: {CSV_PATH}")
    print(f"Rows: {len(rows)}")
    print(f"Unique EUROCODE: {unique_codes}")
    print(f"Candidate products: {len(products)} (case/spacing variants merged: {merged})")
    print(f"Invalid references excluded: {len(invalid_rows)}")
    print(f"Suspect eurocode format (eurocode_format_valide=false): {format_invalides}")
    print(f"Distinct suppliers (FRS): {len(suppliers)}")
    print("Generated: categories_mapping.csv, locations_mapping.csv, suppliers_mapping.csv, products_to_import.csv, stock_initial_to_import.csv, data_quality_report.md")


def check_place_warehouse() -> None:
    """Verifie la repartition RPBM du 2026-08-05 sur les cas reels du fichier source."""
    for key in ("R101", "R136", "R201", "R336"):
        assert place_warehouse(key) == "Depot 1", key
    for key in ("R401", "R538", "R642", "R739", "R837", "R900", "R937"):
        assert place_warehouse(key) == "Depot 2", key
    for key in ("J001", "J10", "J1A", "J11A", "JT001", "JC10", "JD5", "J80", "T001", "T729"):
        assert place_warehouse(key) == "Depot 2", key
    # "R317 ?" et "R636 ?" se normalisent en "R317"/"R636" : l'annotation d'incertitude porte
    # sur le rack, pas sur le depot, et les deux numeros sont dans une plage tranchee. Ils sont
    # donc rattaches, contrairement aux autres valeurs annotees.
    assert place_warehouse("R317") == "Depot 1"
    assert place_warehouse("R636") == "Depot 2"
    # Explicitement laisses non rattaches (decision RPBM du 2026-08-05).
    for key in ("R35", "R100", "R338", "R938", "R108 R109", "R303 R324", "CAISSE R117",
                "JDESSUS", "JD", "JC", "TRINGLE", "RACK PLAFOND 1", "CASSE",
                "GALLERIA", "CENTRE", "PALETTE SAVON", "PERDU D2", ""):
        assert place_warehouse(key) == "", key
    print("check_place_warehouse : OK")


if __name__ == "__main__":
    import sys

    if "--check" in sys.argv:
        check_place_warehouse()
    else:
        main()
