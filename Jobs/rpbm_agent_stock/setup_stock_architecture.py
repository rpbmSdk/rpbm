"""Met en place l'architecture stock 1 (entrepot unique, 5 sites en zones) sur rpbm-preprod.

    pyenv exec python setup_stock_architecture.py <phase> [--commit] [--profile ...]

Implemente Jobs/Gestion Stock/architectures/01-architecture-1-zones.md §2.1-2.7 (l'architecture
recommandee, cf. questions-ouvertes.md Q1). Ce fichier reste la seule source de verite : toute
divergence entre la spec et ce script est un bug de CE script, pas de la doc. Voir
tests/test_setup_stock_architecture.py pour la garde-fou anti-derive (comptages statiques).

Phases, dans l'ordre des dependances (chacune resout ses propres prealables par recherche,
jamais par hypothese sur un id) :

    locations      stock.location       Dépôts (nouveau parent), Galleria, Genipa, Camion,
                                         A controler, CASSE ; re-rattache et renomme les racks
                                         existants Stock D1/Stock D2 en Dépôt 1/Dépôt 2 sous Dépôts
    picking_types  stock.picking.type   34 types (31 invariants + 3 reserves aux regles)
    routes         stock.route          3 routes RPBM + amendement de Buy (product_categ_selectable)
    rules          stock.rule           6 regles metier + amendement de la regle Acheter existante
                                         (location_dest_id -> Stock, picking_type_id -> D2/IN)
    putaway        stock.putaway.rule   1 regle "filet" (Stock -> Dépôt 2) ; les 2 regles
                                         "reception -> rack" de la spec §2.7 ne sont pas creees,
                                         decision RPBM (2026-09) -- D1/IN et D2/IN livrent deja
                                         directement sur leur depot, pas de rack dedie
    carriers       delivery.carrier     3 transporteurs
    check          lecture seule        relevé de l'etat actuel, sans comparaison a la cible

Prealable : rpbm_agent installe (install_module.py) et l'entrepot RPBM existant sur l'instance.
Cette architecture RESTRUCTURE des emplacements existants. Constat en direct sur l'instance
rebuild (2026-09) : RPBM/Stock D1, RPBM/Stock D2 (avec leurs racks reels), GALLERIA et GENIPA
avaient survecu au rebuild (tous freres directs de RPBM, aucun noeud Stock intermediaire) ;
Camion et Dépôts n'existaient pas du tout. La phase locations cree Stock/Dépôts/Camion/A
controler/CASSE et re-rattache Stock D1/D2 (renommes Dépôt 1/Dépôt 2) et GALLERIA/GENIPA sous
le nouvel arbre, plutot que de supposer leur existence ou leur absence. Chaque phase resout
l'existant par nom (insensible a la casse) avant de creer, jamais de creation aveugle : si un
prealable est absent ou ambigu, la phase
s'arrete avec une erreur explicite. Secrets lus depuis ~/.paradigme/.env, jamais affiches.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable

from common import Odoo, xmlid

WAREHOUSE_NAME = "RPBM"

# --- §2.2 stock.location -------------------------------------------------------------------
# Etat constate en direct sur l'instance (2026-09) : RPBM (view, id 11) a exactement 4 enfants
# directs -- GALLERIA, GENIPA, Stock D1 (= lot_stock_id actuel de l'entrepot) et Stock D2 --
# aucun noeud "Stock" intermediaire n'existe. C'est precisement la structure plate decrite comme
# defaut a corriger dans questions-ouvertes.md ("GALLERIA, GENIPA et Stock D2 sont des freres de
# Stock D1, pas des enfants") : cette phase construit l'arbre §2.2 par-dessus, sans recreer les
# racks existants ni deplacer leurs quants (un rack garde son id, seul son parent change).

# Premier noeud a creer : tout le reste en depend (directement ou via Dépôts).
STOCK_NODE = ("Stock", "internal", "RPBM_VIEW", {})

# Noeuds suivants, une fois Stock cree (nom, usage, parent, champs additionnels).
# "STOCK_ROOT" et "RPBM_VIEW" sont des marqueurs resolus dynamiquement dans phase_locations.
NEW_LOCATIONS = [
    ("Dépôts", "internal", "STOCK_ROOT", {}),
    ("Camion", "internal", "RPBM_VIEW", {"return_location": "1"}),
    ("A controler", "internal", "RPBM_VIEW", {}),
]
# CASSE est une localisation virtuelle (parent Virtual Locations, pas RPBM) : geree a part.
CASSE = ("CASSE", "inventory", "Virtual Locations", {"scrap_location": "1"})

# Emplacements EXISTANTS a re-rattacher sous le nouvel arbre, jamais recrees : seul location_id
# (et le nom pour les deux premiers) est ecrit. Le contenu des racks n'est pas touche.
# (nom actuel sur l'instance, nouveau parent, nouveau nom ou None si inchange, champs additionnels)
RELOCATED_EXISTING = [
    ("Stock D1", "DEPOTS_ROOT", "Dépôt 1", {}),
    ("Stock D2", "DEPOTS_ROOT", "Dépôt 2", {}),
    ("GALLERIA", "STOCK_ROOT", None, {"replenish_location": "1"}),
    ("GENIPA", "STOCK_ROOT", None, {"replenish_location": "1"}),
]

# --- §2.3 stock.picking.type --------------------------------------------------------------
# (sequence_code, nom, code, src, dest, reservation_method, create_backorder)
# src/dest : None = a resoudre autrement (Partners/Vendors, Partners/Customers) ou sans objet.
PICKING_TYPES_INTERNAL = [
    ("D1-GALL", "Transfert Dépôt 1 -> Galleria", "Dépôts/Dépôt 1", "Galleria", "at_confirm", "ask"),
    ("D1-GENI", "Transfert Dépôt 1 -> Genipa", "Dépôts/Dépôt 1", "Genipa", "at_confirm", "ask"),
    ("D1-CAM", "Transfert Dépôt 1 -> Camion", "Dépôts/Dépôt 1", "Camion", "manual", "always"),
    ("D1-D2", "Transfert Dépôt 1 -> Dépôt 2", "Dépôts/Dépôt 1", "Dépôts/Dépôt 2", "at_confirm", "ask"),
    ("D2-GALL", "Transfert Dépôt 2 -> Galleria", "Dépôts/Dépôt 2", "Galleria", "at_confirm", "ask"),
    ("D2-GENI", "Transfert Dépôt 2 -> Genipa", "Dépôts/Dépôt 2", "Genipa", "at_confirm", "ask"),
    ("D2-CAM", "Transfert Dépôt 2 -> Camion", "Dépôts/Dépôt 2", "Camion", "manual", "always"),
    ("D2-D1", "Transfert Dépôt 2 -> Dépôt 1", "Dépôts/Dépôt 2", "Dépôts/Dépôt 1", "at_confirm", "ask"),
    ("GALL-D1", "Transfert Galleria -> Dépôt 1", "Galleria", "Dépôts/Dépôt 1", "at_confirm", "ask"),
    ("GALL-D2", "Transfert Galleria -> Dépôt 2", "Galleria", "Dépôts/Dépôt 2", "at_confirm", "ask"),
    ("GALL-CAM", "Transfert Galleria -> Camion", "Galleria", "Camion", "manual", "always"),
    ("GALL-GENI", "Transfert Galleria -> Genipa", "Galleria", "Genipa", "at_confirm", "ask"),
    ("GENI-D1", "Transfert Genipa -> Dépôt 1", "Genipa", "Dépôts/Dépôt 1", "at_confirm", "ask"),
    ("GENI-D2", "Transfert Genipa -> Dépôt 2", "Genipa", "Dépôts/Dépôt 2", "at_confirm", "ask"),
    ("GENI-CAM", "Transfert Genipa -> Camion", "Genipa", "Camion", "manual", "always"),
    ("GENI-GALL", "Transfert Genipa -> Galleria", "Genipa", "Galleria", "at_confirm", "ask"),
    ("CAM-D1", "Retour Camion -> Dépôt 1", "Camion", "Dépôts/Dépôt 1", "at_confirm", "ask"),
    ("CAM-D2", "Retour Camion -> Dépôt 2", "Camion", "Dépôts/Dépôt 2", "at_confirm", "ask"),
    ("CAM-GALL", "Retour Camion -> Galleria", "Camion", "Galleria", "at_confirm", "ask"),
    ("CAM-GENI", "Retour Camion -> Genipa", "Camion", "Genipa", "at_confirm", "ask"),
    # §2.3.5 : les trois types reserves aux regles (jamais choisis a la main sur un transfert).
    ("DEP-GALL", "Transfert Dépôts -> Galleria", "Dépôts", "Galleria", "at_confirm", "ask"),
    ("DEP-GENI", "Transfert Dépôts -> Genipa", "Dépôts", "Genipa", "at_confirm", "ask"),
    ("STK-CAM", "Chargement camion", "Stock", "Camion", "manual", "always"),
]
# (sequence_code, nom, dest, return_picking_type_id)
PICKING_TYPES_INCOMING = [
    ("D1/IN", "Réception Dépôt 1", "Dépôts/Dépôt 1", "D1/RET"),
    ("D2/IN", "Réception Dépôt 2", "Dépôts/Dépôt 2", "D2/RET"),
    ("GALL/IN", "Réception Galleria", "Galleria", "GALL/RET"),
    ("GENI/IN", "Réception Genipa", "Genipa", "GENI/RET"),
]
# (sequence_code, nom, src, reservation_method, create_backorder, default_location_return_id)
PICKING_TYPES_OUTGOING = [
    ("GALL/OUT", "Livraison Galleria", "Galleria", "at_confirm", "ask", None),
    ("GENI/OUT", "Livraison Genipa", "Genipa", "at_confirm", "ask", None),
    ("CAM/OUT", "Pose sur site", "Camion", "manual", "always", "Camion"),
]
# (sequence_code, nom, src) -- retours fournisseur, rattaches en second temps a leur IN.
PICKING_TYPES_RETURNS = [
    ("D1/RET", "Retour fournisseur Dépôt 1", "Dépôts/Dépôt 1"),
    ("D2/RET", "Retour fournisseur Dépôt 2", "Dépôts/Dépôt 2"),
    ("GALL/RET", "Retour fournisseur Galleria", "Galleria"),
    ("GENI/RET", "Retour fournisseur Genipa", "Genipa"),
]

# --- §2.4 stock.route ----------------------------------------------------------------------
# (nom, sequence, product_selectable, product_categ_selectable, warehouse_selectable,
#  packaging_selectable, sale_selectable, shipping_selectable)
ROUTES = [
    ("Retrait / pose Galleria", 20, False, False, False, False, True, True),
    ("Retrait / pose Genipa", 21, False, False, False, False, True, True),
    ("Pose sur site - Camion", 22, False, False, False, False, True, True),
]

# --- §2.5 stock.rule -------------------------------------------------------------------------
# (nom, route, sequence, src, dest, picking_type_sequence_code, procure_method)
RULES = [
    ("Galleria -> Clients", "Retrait / pose Galleria", 10, "Galleria", "Partners/Customers", "GALL/OUT", "mts_else_mto"),
    ("Dépôts -> Galleria", "Retrait / pose Galleria", 20, "Dépôts", "Galleria", "DEP-GALL", "mts_else_mto"),
    ("Genipa -> Clients", "Retrait / pose Genipa", 10, "Genipa", "Partners/Customers", "GENI/OUT", "mts_else_mto"),
    ("Dépôts -> Genipa", "Retrait / pose Genipa", 20, "Dépôts", "Genipa", "DEP-GENI", "mts_else_mto"),
    ("Camion -> Clients", "Pose sur site - Camion", 10, "Camion", "Partners/Customers", "CAM/OUT", "make_to_order"),
    ("Stock -> Camion", "Pose sur site - Camion", 20, "Stock", "Camion", "STK-CAM", "mts_else_mto"),
]

# --- §2.7 stock.putaway.rule ------------------------------------------------------------------
# Decision RPBM (2026-09) : pas de rack de reception dedie -- D1/IN et D2/IN livrent deja
# directement sur Dépôt 1/Dépôt 2 via default_location_dest_id (§2.3.2), le rangement precis
# en rack reste manuel. Les deux regles "reception -> rack" de la spec (§2.7, lignes 1-2) sont
# donc redondantes avec ce que les types d'operation font deja et ne sont pas creees ici.
# Seule la regle "filet" reste necessaire : la regle Acheter (buy_pull_id) a pour
# location_dest_id RPBM/Stock (§4.2, structurel), et sans ce filet une reception fournisseur
# atterrirait au niveau Stock, jamais range dans un depot.
# (location_in, location_out, sequence, role)
PUTAWAY_RULES = [
    ("Stock", "Dépôts/Dépôt 2", 90, "filet -- rattrape la destination Stock de la regle Acheter"),
]

# --- §2.6 delivery.carrier ----------------------------------------------------------------
# (nom, route)
# Produits de service consommes par les transporteurs (product_id est requis par
# delivery.carrier, delivery/models/delivery_carrier.py:49). "Retrait comptoir" est partage par
# les deux comptoirs (meme prestation, prix nul) ; "Pose à domicile" est dedie au camion --
# renomme depuis "Frais de deplacement" (decision RPBM, 2026-09). Prix a 0.00 pour l'instant
# pour les deux, a revoir plus tard.
SERVICE_PRODUCTS = [
    ("Retrait comptoir", 0.0),
    ("Pose à domicile", 0.0),
]

# (nom du transporteur, route, nom du produit de service)
CARRIERS = [
    ("Retrait / pose Galleria", "Retrait / pose Galleria", "Retrait comptoir"),
    ("Retrait / pose Genipa", "Retrait / pose Genipa", "Retrait comptoir"),
    ("Pose sur site (Camion)", "Pose sur site - Camion", "Pose à domicile"),
]


# --- Resolution d'emplacements par chemin ---------------------------------------------------


def resolve_location(odoo: Odoo, path: str) -> int:
    """Resout RPBM/Stock/Dépôts/Dépôt 1 -> id, en cherchant le segment le plus specifique
    d'abord parmi les emplacements deja crees par ce script (xmlid), sinon par nom natif exact
    (insensible a la casse : la donnee reelle porte GALLERIA/GENIPA en majuscules, la spec
    Galleria/Genipa -- meme emplacement, casse differente, jamais renomme par ce script)."""
    name = path.split("/")[-1]
    found = odoo.resolve_xmlid(xmlid("loc", path))
    if found:
        return found
    found_native = odoo.search_read(
        "stock.location", [["name", "=ilike", name], ["usage", "!=", "view"]], ["id", "complete_name"]
    )
    if len(found_native) == 1:
        return found_native[0]["id"]
    raise RuntimeError(
        f"Emplacement {path!r} introuvable ou ambigu ({len(found_native)} candidat(s)) : "
        "verifier le rattachement des racks existants avant de rejouer cette phase."
    )


def resolve_warehouse(odoo: Odoo) -> dict:
    return odoo.search_read(
        "stock.warehouse", [["name", "=", WAREHOUSE_NAME]],
        ["id", "lot_stock_id", "view_location_id"],
    )[0]


# --- Phases ------------------------------------------------------------------------------


def phase_locations(odoo: Odoo, _limit: int | None) -> None:
    warehouse = resolve_warehouse(odoo)
    view_id = warehouse["view_location_id"][0]
    virtual = odoo.resolve_id("stock.location", [["usage", "=", "view"], ["name", "=", "Virtual Locations"]], "Virtual Locations")

    # 1. Stock -- prealable de tout le reste (Dépôts et le re-rattachement de GALLERIA/GENIPA
    # en dependent). N'existe pas encore sur l'instance : RPBM n'a aujourd'hui que 4 enfants
    # directs (GALLERIA, GENIPA, Stock D1, Stock D2), aucun noeud intermediaire.
    name, usage, _parent, extra = STOCK_NODE
    row = {"id": xmlid("loc", name), "name": name, "location_id/.id": str(view_id), "usage": usage, **extra}
    fields = sorted(row)
    odoo.load("stock.location", fields, [[row[f] for f in fields]], "emplacement Stock (nouveau)")
    stock_id = odoo.resolve_xmlid(xmlid("loc", "Stock")) if odoo.commit else None

    # 2. Dépôts (parent Stock), Camion + A controler (parent RPBM).
    rows = []
    for name, usage, parent_marker, extra in NEW_LOCATIONS:
        parent_id = {"RPBM_VIEW": view_id, "STOCK_ROOT": stock_id}[parent_marker]
        row = {"id": xmlid("loc", name), "name": name, "usage": usage,
               "location_id/.id": str(parent_id) if parent_id else ""}
        row.update(extra)
        rows.append(row)
    if not odoo.commit:
        print("  [dry-run] Dépôts/Camion/A controler : cree(s) apres Stock (id reel indisponible sans --commit).")
    fields = sorted({key for row in rows for key in row})
    odoo.load("stock.location", fields, [[row.get(f, "") for f in fields] for row in rows], "Dépôts / Camion / A controler")
    depots_id = odoo.resolve_xmlid(xmlid("loc", "Dépôts")) if odoo.commit else None

    # 3. CASSE (parent Virtual Locations).
    casse_name, casse_usage, _parent, casse_extra = CASSE
    casse_row = {"id": xmlid("loc", "CASSE"), "name": casse_name, "location_id/.id": str(virtual), "usage": casse_usage, **casse_extra}
    fields = sorted(casse_row)
    odoo.load("stock.location", fields, [[casse_row[f] for f in fields]], "emplacement CASSE")

    # 4. Re-rattachement des emplacements EXISTANTS (jamais recrees, contenu des racks
    # inchange) : Stock D1/D2 -> Dépôts (renommes Dépôt 1/Dépôt 2), GALLERIA/GENIPA -> Stock.
    print("\nRe-rattachement des emplacements existants (donnee reelle, jamais recreee) :")
    for current_name, parent_marker, new_name, extra in RELOCATED_EXISTING:
        parent_id = {"STOCK_ROOT": stock_id, "DEPOTS_ROOT": depots_id}[parent_marker]
        existing = odoo.search_read("stock.location", [["name", "=ilike", current_name]], ["id", "location_id"], limit=1)
        if not existing:
            print(f"  ATTENTION : {current_name!r} introuvable sur l'instance -- re-rattachement ignore.")
            continue
        values = {"location_id": parent_id, **{k: (v == "1") for k, v in extra.items()}}
        if new_name:
            values["name"] = new_name
        if not odoo.commit:
            print(f"  [dry-run] {current_name!r} (id {existing[0]['id']}, parent actuel {existing[0]['location_id']}) : {values}")
            continue
        odoo.execute("stock.location", "write", [existing[0]["id"]], values)
        print(f"  {current_name!r} (id {existing[0]['id']}) -> {values}")

    # 5. Repoint lot_stock_id sur le nouveau Stock -- LE correctif deja identifie comme
    # necessaire "quelle que soit la configuration retenue" (questions-ouvertes.md), pas une
    # consequence secondaire de cette phase. Effet sur wh_input_stock_loc_id etc. non trace
    # avant execution reelle (01-architecture-1-zones.md §6 point 4) : verifie ci-dessous.
    if not odoo.commit:
        print(f"\n  [dry-run] warehouse.lot_stock_id : {warehouse['lot_stock_id']} -> Stock (nouveau)")
    else:
        odoo.execute("stock.warehouse", "write", [warehouse["id"]], {"lot_stock_id": stock_id})
        after = odoo.search_read(
            "stock.warehouse", [["id", "=", warehouse["id"]]],
            ["lot_stock_id", "wh_input_stock_loc_id", "wh_output_stock_loc_id"],
        )[0]
        print(f"\n  warehouse.lot_stock_id repointe sur Stock (id {stock_id}).")
        print(f"  Verification post-repoint (effet non trace au prealable, §6 point 4) : {after}")


def phase_picking_types(odoo: Odoo, _limit: int | None) -> None:
    warehouse = resolve_warehouse(odoo)
    company_id = odoo.search_read("res.users", [["id", "=", odoo.uid]], ["company_id"])[0]["company_id"][0]
    vendors = odoo.resolve_id("stock.location", [["usage", "=", "supplier"], ["name", "=", "Vendors"]], "Partners/Vendors")
    customers = odoo.resolve_id("stock.location", [["usage", "=", "customer"], ["name", "=", "Customers"]], "Partners/Customers")

    def loc(path: str) -> int:
        return resolve_location(odoo, path)

    created: dict[str, str] = {}

    rows = []
    for seq, name, src, dest, method, backorder in PICKING_TYPES_INTERNAL:
        entry = xmlid("picktype", seq)
        created[seq] = entry
        rows.append({
            "id": entry, "name": name, "sequence_code": seq, "code": "internal",
            "warehouse_id/.id": str(warehouse["id"]), "company_id/.id": str(company_id),
            "default_location_src_id/.id": str(loc(src)),
            "default_location_dest_id/.id": str(loc(dest)),
            "reservation_method": method, "create_backorder": backorder,
        })
    fields = sorted({key for row in rows for key in row})
    odoo.load("stock.picking.type", fields, [[row.get(f, "") for f in fields] for row in rows], "types internal (23)")

    rows = []
    for seq, name, dest, _return_code in PICKING_TYPES_INCOMING:
        entry = xmlid("picktype", seq)
        created[seq] = entry
        rows.append({
            "id": entry, "name": name, "sequence_code": seq, "code": "incoming",
            "warehouse_id/.id": str(warehouse["id"]), "company_id/.id": str(company_id),
            "default_location_src_id/.id": str(vendors),
            "default_location_dest_id/.id": str(loc(dest)),
        })
    fields = sorted({key for row in rows for key in row})
    odoo.load("stock.picking.type", fields, [[row.get(f, "") for f in fields] for row in rows], "types incoming (4)")

    rows = []
    for seq, name, src, method, backorder, return_dest in PICKING_TYPES_OUTGOING:
        entry = xmlid("picktype", seq)
        created[seq] = entry
        row = {
            "id": entry, "name": name, "sequence_code": seq, "code": "outgoing",
            "warehouse_id/.id": str(warehouse["id"]), "company_id/.id": str(company_id),
            "default_location_src_id/.id": str(loc(src)),
            "default_location_dest_id/.id": str(customers),
            "reservation_method": method, "create_backorder": backorder,
        }
        if return_dest:
            row["default_location_return_id/.id"] = str(loc(return_dest))
        rows.append(row)
    fields = sorted({key for row in rows for key in row})
    odoo.load("stock.picking.type", fields, [[row.get(f, "") for f in fields] for row in rows], "types outgoing (3)")

    rows = []
    for seq, name, src in PICKING_TYPES_RETURNS:
        entry = xmlid("picktype", seq)
        created[seq] = entry
        rows.append({
            "id": entry, "name": name, "sequence_code": seq, "code": "outgoing",
            "warehouse_id/.id": str(warehouse["id"]), "company_id/.id": str(company_id),
            "default_location_src_id/.id": str(loc(src)),
            "default_location_dest_id/.id": str(vendors),
        })
    fields = sorted({key for row in rows for key in row})
    odoo.load("stock.picking.type", fields, [[row.get(f, "") for f in fields] for row in rows], "types retours fournisseur (4)")

    print("\nRattachement des retours a leur reception (return_picking_type_id) :")
    for in_seq, _name, _dest, ret_seq in PICKING_TYPES_INCOMING:
        if not odoo.commit:
            print(f"  [dry-run] {in_seq}.return_picking_type_id = {ret_seq}")
            continue
        in_id = odoo.resolve_xmlid(created[in_seq])
        ret_id = odoo.resolve_xmlid(created[ret_seq])
        odoo.execute("stock.picking.type", "write", [in_id], {"return_picking_type_id": ret_id})
        print(f"  {in_seq} (id {in_id}) -> return_picking_type_id = {ret_seq} (id {ret_id})")

    total = len(PICKING_TYPES_INTERNAL) + len(PICKING_TYPES_INCOMING) + len(PICKING_TYPES_OUTGOING) + len(PICKING_TYPES_RETURNS)
    print(f"\nTotal : {total} types d'operation (attendu : 34).")


def phase_routes(odoo: Odoo, _limit: int | None) -> None:
    rows = []
    for name, sequence, prod, categ, wh, pack, sale, ship in ROUTES:
        rows.append([
            xmlid("route", name), name, str(sequence),
            "1" if prod else "0", "1" if categ else "0", "1" if wh else "0",
            "1" if pack else "0", "1" if sale else "0", "1" if ship else "0",
        ])
    fields = [
        "id", "name", "sequence", "product_selectable", "product_categ_selectable",
        "warehouse_selectable", "packaging_selectable", "sale_selectable", "shipping_selectable",
    ]
    odoo.load("stock.route", fields, rows, "routes architecture 1 (3)")

    buy_id = odoo.resolve_id("stock.route", [["name", "like", "Buy"]], "route Buy")
    print(f"\nAmendement route Buy (id {buy_id}) : product_categ_selectable = True")
    if odoo.commit:
        odoo.execute("stock.route", "write", [buy_id], {"product_categ_selectable": True})
    else:
        print("  [dry-run] write product_categ_selectable=True sur la route Buy.")


def phase_rules(odoo: Odoo, _limit: int | None) -> None:
    warehouse = resolve_warehouse(odoo)
    company_id = odoo.search_read("res.users", [["id", "=", odoo.uid]], ["company_id"])[0]["company_id"][0]
    customers = odoo.resolve_id("stock.location", [["usage", "=", "customer"], ["name", "=", "Customers"]], "Partners/Customers")

    rows = []
    for name, route, sequence, src, dest, picktype_seq, procure_method in RULES:
        route_id = odoo.resolve_xmlid(xmlid("route", route)) if odoo.commit else None
        picktype_id = odoo.resolve_xmlid(xmlid("picktype", picktype_seq)) if odoo.commit else None
        dest_id = customers if dest == "Partners/Customers" else (resolve_location(odoo, dest) if odoo.commit else None)
        src_id = resolve_location(odoo, src) if odoo.commit else None
        row = {
            "id": xmlid("rule", name), "name": name,
            "route_id/.id": str(route_id) if route_id else "",
            "sequence": str(sequence),
            "location_src_id/.id": str(src_id) if src_id else "",
            "location_dest_id/.id": str(dest_id) if dest_id else "",
            "picking_type_id/.id": str(picktype_id) if picktype_id else "",
            "procure_method": procure_method, "action": "pull",
            "warehouse_id/.id": str(warehouse["id"]), "company_id/.id": str(company_id),
            "group_propagation_option": "propagate", "auto": "manual",
            "propagate_cancel": "1" if procure_method != "mts_else_mto" else "0",
        }
        rows.append(row)
        if not odoo.commit:
            print(f"  [dry-run] regle {name} : {route} / {src} -> {dest} via {picktype_seq} ({procure_method})")
    if odoo.commit:
        fields = sorted({key for row in rows for key in row})
        odoo.load("stock.rule", fields, [[row.get(f, "") for f in fields] for row in rows], "regles metier (6)")

    print("\nAmendement de la regle Acheter existante (buy_pull_id, §4.2 -- structurel, pas creee "
          "par cette phase, seulement modifiee) :")
    if not odoo.commit:
        print("  [dry-run] location_dest_id -> Stock, picking_type_id -> D2/IN")
        return
    buy_pull = odoo.search_read("stock.warehouse", [["id", "=", warehouse["id"]]], ["buy_pull_id"])[0]["buy_pull_id"]
    d2_in_id = odoo.resolve_xmlid(xmlid("picktype", "D2/IN"))
    stock_id = resolve_location(odoo, "Stock")
    if not (buy_pull and d2_in_id and stock_id):
        print(f"  ATTENTION : amendement non applique (buy_pull_id={buy_pull}, D2/IN={d2_in_id}, Stock={stock_id})")
        return
    odoo.execute("stock.rule", "write", [buy_pull[0]], {"location_dest_id": stock_id, "picking_type_id": d2_in_id})
    print(f"  regle Acheter (id {buy_pull[0]}) : location_dest_id -> Stock (id {stock_id}), "
          f"picking_type_id -> D2/IN (id {d2_in_id})")


def phase_putaway(odoo: Odoo, _limit: int | None) -> None:
    company_id = odoo.search_read("res.users", [["id", "=", odoo.uid]], ["company_id"])[0]["company_id"][0]
    rows = []
    for location_in, location_out, sequence, role in PUTAWAY_RULES:
        in_id = resolve_location(odoo, location_in) if odoo.commit else None
        out_id = resolve_location(odoo, location_out) if odoo.commit else None
        rows.append({
            "id": xmlid("putaway", f"{location_in}_{location_out}"),
            "location_in_id/.id": str(in_id) if in_id else "",
            "location_out_id/.id": str(out_id) if out_id else "",
            "company_id/.id": str(company_id), "sequence": str(sequence),
        })
        if not odoo.commit:
            print(f"  [dry-run] putaway {location_in} -> {location_out} (seq {sequence}, {role})")
    if odoo.commit:
        fields = sorted({key for row in rows for key in row})
        odoo.load("stock.putaway.rule", fields, [[row.get(f, "") for f in fields] for row in rows], "putaway (filet Stock -> Dépôt 2)")


def phase_carriers(odoo: Odoo, _limit: int | None) -> None:
    # 1. Produits de service -- prealable requis par delivery.carrier.product_id
    # (delivery/models/delivery_carrier.py:49). Idempotent via xmlid, comme le reste.
    rows = [
        {"id": xmlid("product", name), "name": name, "detailed_type": "service",
         "sale_ok": "1", "purchase_ok": "0", "list_price": str(price)}
        for name, price in SERVICE_PRODUCTS
    ]
    if not odoo.commit:
        for name, price in SERVICE_PRODUCTS:
            print(f"  [dry-run] produit de service {name!r} (prix {price})")
    else:
        fields = sorted({key for row in rows for key in row})
        odoo.load("product.template", fields, [[row[f] for f in fields] for row in rows], "produits de service (2)")

    price_by_product = dict(SERVICE_PRODUCTS)

    # 2. Transporteurs, un par route -- recherche prealable pour ne jamais dupliquer (create()
    # n'est pas idempotent via xmlid comme load(), delivery.carrier n'ayant pas de mecanisme
    # d'identifiant externe naturel dans ce flux).
    for name, route, product_name in CARRIERS:
        if not odoo.commit:
            print(f"  [dry-run] transporteur {name!r} : route={route!r} produit={product_name!r} "
                  f"prix={price_by_product[product_name]}")
            continue
        existing = odoo.search_read("delivery.carrier", [["name", "=", name]], ["id"], limit=1)
        if existing:
            print(f"  {name} : deja present (id {existing[0]['id']}), non recree.")
            continue
        route_id = odoo.resolve_xmlid(xmlid("route", route))
        product_tmpl_id = odoo.resolve_xmlid(xmlid("product", product_name))
        product_id = None
        if product_tmpl_id:
            variant = odoo.search_read("product.product", [["product_tmpl_id", "=", product_tmpl_id]], ["id"], limit=1)
            product_id = variant[0]["id"] if variant else None
        if not route_id or not product_id:
            print(f"  {name} : prealable manquant (route={route_id}, produit service={product_id}) -- ignore.")
            continue
        carrier_id = odoo.call(
            "delivery.carrier", "create", None, {
                "name": name, "delivery_type": "fixed",
                "product_id": product_id, "fixed_price": price_by_product[product_name],
                "route_ids": [(6, 0, [route_id])],
                "integration_level": "rate",
            },
            label=f"transporteur {name}",
        )
        print(f"  {name} : cree (id {carrier_id}), produit {product_name!r} (id {product_id}), "
              f"prix {price_by_product[product_name]}")


def phase_check(odoo: Odoo, _limit: int | None) -> None:
    warehouse = odoo.search_read("stock.warehouse", [["name", "=", WAREHOUSE_NAME]], ["id", "lot_stock_id"])
    print(f"Entrepot {WAREHOUSE_NAME} : {warehouse}")
    for model, label in [
        ("stock.location", "emplacements"),
        ("stock.picking.type", "types d'operation"),
        ("stock.route", "routes"),
        ("stock.rule", "regles"),
        ("stock.putaway.rule", "putaway"),
        ("delivery.carrier", "transporteurs"),
    ]:
        count = odoo.search_count(model, [])
        print(f"  {label} ({model}) : {count}")


PHASES = {
    "locations": phase_locations,
    "picking_types": phase_picking_types,
    "routes": phase_routes,
    "rules": phase_rules,
    "putaway": phase_putaway,
    "carriers": phase_carriers,
    "check": phase_check,
}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("phase", choices=list(PHASES))
    parser.add_argument("--commit", action="store_true", help="ecrire reellement dans Odoo")
    parser.add_argument("--limit", type=int, help="reserve, non utilise par ces phases")
    parser.add_argument("--profile", default=None, help="profil paradigme-mcp (defaut : lu depuis .paradigme.yaml)")
    args = parser.parse_args(list(argv) if argv is not None else None)

    odoo = Odoo(args.profile, args.commit)
    mode = "ECRITURE" if args.commit else "dry-run (aucune ecriture)"
    print(f"Phase {args.phase} sur {odoo.url} (profil {odoo.profile!r}) — {mode}\n")
    PHASES[args.phase](odoo, args.limit)
    if not args.commit:
        print("\nAucune ecriture effectuee. Relancer avec --commit pour appliquer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
