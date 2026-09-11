"""Audit structurel de l'architecture stock 1 -- lecture seule, aucune ecriture, jamais.

    pyenv exec python verify_structural.py [--profile ...]

Operationnalise Jobs/Gestion Stock/architectures/audits/procedure-audit-implementation.md §6
et architecture-1-compliance-matrix.md : compare l'instance a la cible definie dans
setup_stock_architecture.py (reutilisee telle quelle, jamais recopiee -- une seule source de
verite pour "ce qui doit exister"). Statuts repris de la procedure existante : PASS, FAIL, WARN,
NOT_APPLICABLE. Aucun --commit possible : ce script n'ecrit jamais dans Odoo.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable

from common import Odoo
from setup_stock_architecture import (
    CARRIERS,
    PICKING_TYPES_INCOMING,
    PICKING_TYPES_INTERNAL,
    PICKING_TYPES_OUTGOING,
    PICKING_TYPES_RETURNS,
    PUTAWAY_RULES,
    RULES,
    ROUTES,
    resolve_location,
    resolve_warehouse,
)

RESULTS: list[tuple[str, str, str]] = []  # (statut, controle, detail)


def record(status: str, check: str, detail: str = "") -> None:
    RESULTS.append((status, check, detail))
    print(f"  [{status}] {check}" + (f" -- {detail}" if detail else ""))


def check_picking_types(odoo: Odoo) -> None:
    print("\n=== 26+8 types d'operation (34 attendus, §2.3) ===")
    all_expected = (
        [(seq, name) for seq, name, *_ in PICKING_TYPES_INTERNAL]
        + [(seq, name) for seq, name, *_ in PICKING_TYPES_INCOMING]
        + [(seq, name) for seq, name, *_ in PICKING_TYPES_OUTGOING]
        + [(seq, name) for seq, name, *_ in PICKING_TYPES_RETURNS]
    )
    for seq, name in all_expected:
        found = odoo.search_read(
            "stock.picking.type", [["sequence_code", "=", seq]],
            ["id", "name", "default_location_src_id", "default_location_dest_id"], limit=1,
        )
        if not found:
            record("FAIL", f"type {seq} ({name})", "absent")
        else:
            record("PASS", f"type {seq} ({name})", f"id={found[0]['id']}")
    total = odoo.search_count("stock.picking.type", [["sequence_code", "in", [s for s, _ in all_expected]]])
    status = "PASS" if total == len(all_expected) else "WARN"
    record(status, "total types architecture 1", f"{total}/{len(all_expected)} attendus (31 invariants + 3 reserves aux regles = 34)")


def check_routes(odoo: Odoo) -> None:
    print("\n=== 3 routes RPBM + amendement Buy (§2.4) ===")
    for name, sequence, prod, categ, wh, pack, sale, ship in ROUTES:
        found = odoo.search_read(
            "stock.route", [["name", "=", name]],
            ["id", "sequence", "product_selectable", "sale_selectable", "shipping_selectable"], limit=1,
        )
        if not found:
            record("FAIL", f"route {name}", "absente")
            continue
        row = found[0]
        ok = row["sale_selectable"] == sale and row["shipping_selectable"] == ship and row["product_selectable"] == prod
        record("PASS" if ok else "WARN", f"route {name}", f"id={row['id']} sale={row['sale_selectable']} shipping={row['shipping_selectable']}")

    buy = odoo.search_read("stock.route", [["name", "like", "Buy"]], ["id", "product_categ_selectable"], limit=1)
    if not buy:
        record("FAIL", "route Buy", "introuvable")
    else:
        record(
            "PASS" if buy[0]["product_categ_selectable"] else "FAIL",
            "route Buy -- product_categ_selectable",
            f"id={buy[0]['id']} valeur={buy[0]['product_categ_selectable']}",
        )


def check_rules(odoo: Odoo) -> None:
    print("\n=== 6 regles metier (§2.5) ===")
    for name, route, sequence, src, dest, picktype_seq, procure_method in RULES:
        found = odoo.search_read(
            "stock.rule", [["name", "=", name]],
            ["id", "procure_method", "picking_type_id"], limit=1,
        )
        if not found:
            record("FAIL", f"regle {name}", "absente")
            continue
        row = found[0]
        ok = row["procure_method"] == procure_method
        record("PASS" if ok else "WARN", f"regle {name}", f"id={row['id']} procure_method={row['procure_method']}")

    buy_pull = odoo.search_read("stock.rule", [["route_id", "like", "Buy"]], ["id", "location_dest_id", "picking_type_id"])
    for row in buy_pull:
        record(
            "PASS" if "Stock" in (row["location_dest_id"] or [None, ""])[1] else "WARN",
            "regle Acheter (buy_pull_id) -- location_dest_id",
            f"id={row['id']} dest={row['location_dest_id']} type={row['picking_type_id']}",
        )


def check_putaway(odoo: Odoo) -> None:
    print("\n=== Putaway (§2.7 -- filet uniquement, decision RPBM 2026-09) ===")
    for location_in, location_out, sequence, role in PUTAWAY_RULES:
        in_id = resolve_location(odoo, location_in)
        out_id = resolve_location(odoo, location_out)
        found = odoo.search_read(
            "stock.putaway.rule", [["location_in_id", "=", in_id], ["location_out_id", "=", out_id]],
            ["id", "sequence"], limit=1,
        )
        if not found:
            record("FAIL", f"putaway {location_in} -> {location_out}", role)
        else:
            record("PASS", f"putaway {location_in} -> {location_out}", f"id={found[0]['id']} ({role})")


def check_carriers(odoo: Odoo) -> None:
    print("\n=== 3 transporteurs (§2.6) ===")
    for name, route, product_name in CARRIERS:
        found = odoo.search_read("delivery.carrier", [["name", "=", name]], ["id", "product_id", "route_ids"], limit=1)
        if not found:
            record("FAIL", f"transporteur {name}", f"absent (produit attendu {product_name!r})")
        else:
            record("PASS", f"transporteur {name}", f"id={found[0]['id']} produit={found[0]['product_id']}")


def check_vigilance_points(odoo: Odoo) -> None:
    """Points explicitement marques 'non verifie'/'non tranche' en §4.6 de la spec :
    observation brute, jamais de PASS/FAIL automatique -- un humain doit lire le detail."""
    print("\n=== Points de vigilance §4.6 (observation, pas de verdict automatique) ===")
    warehouse = resolve_warehouse(odoo)
    record("OBSERVED", "lot_stock_id de RPBM", f"{warehouse['lot_stock_id']}")

    dep_gall = odoo.search_read("stock.picking.type", [["sequence_code", "=", "DEP-GALL"]], ["sequence_code"], limit=1)
    if dep_gall:
        record(
            "NOT_RUN",
            "F4 -- transfert DEP-GALL devient Galleria->Galleria et s'annule proprement",
            "necessite de jouer verify_flows.py --tests T2 ou F4 pour observer, pas deductible en lecture seule",
        )

    out_type = odoo.search_read(
        "stock.picking.type", [["code", "=", "outgoing"], ["name", "like", "Livraisons"]],
        ["id", "name"],
    )
    record("OBSERVED", "types 'Livraisons' natifs existants (§4.6 point 6)", str(out_type))


def phase_check(odoo: Odoo, _limit: int | None) -> int:
    check_picking_types(odoo)
    check_routes(odoo)
    check_rules(odoo)
    check_putaway(odoo)
    check_carriers(odoo)
    check_vigilance_points(odoo)

    fails = [r for r in RESULTS if r[0] == "FAIL"]
    warns = [r for r in RESULTS if r[0] == "WARN"]
    print(f"\n=== Verdict : {len(RESULTS)} controles -- {len(fails)} FAIL, {len(warns)} WARN ===")
    return 1 if fails else 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", default=None, help="profil paradigme-mcp (defaut : lu depuis .paradigme.yaml)")
    args = parser.parse_args(list(argv) if argv is not None else None)

    odoo = Odoo(args.profile, commit=False)  # verify_structural.py n'ecrit jamais, quel que soit l'argument.
    print(f"verify_structural sur {odoo.url} (profil {odoo.profile!r}) — lecture seule\n")
    return phase_check(odoo, None)


if __name__ == "__main__":
    sys.exit(main())
