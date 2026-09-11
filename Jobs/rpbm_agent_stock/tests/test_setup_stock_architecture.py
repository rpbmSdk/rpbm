"""Garde-fou anti-derive : les comptages codes en dur ici doivent rester egaux a ceux de
architectures/01-architecture-1-zones.md. Si la spec change sans que setup_stock_architecture.py
soit mis a jour, ce test echoue -- exactement le type de derive documentation/code deja rencontre
une fois dans ce projet (citations de ligne perimees dans reconciliation-stock-rpbm-agent.md).

Aucun reseau : ne verifie que la coherence interne des tables Python, pas l'etat d'une instance.

    pyenv exec python tests/test_setup_stock_architecture.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import setup_stock_architecture as arch  # noqa: E402


def test_34_picking_types() -> None:
    total = (
        len(arch.PICKING_TYPES_INTERNAL)
        + len(arch.PICKING_TYPES_INCOMING)
        + len(arch.PICKING_TYPES_OUTGOING)
        + len(arch.PICKING_TYPES_RETURNS)
    )
    assert total == 34, f"attendu 34 types (31 invariants + 3 reserves aux regles), trouve {total}"
    assert len(arch.PICKING_TYPES_INTERNAL) == 23, "20 transferts inter-sites + 3 types reserves aux regles"
    assert len(arch.PICKING_TYPES_INCOMING) == 4
    assert len(arch.PICKING_TYPES_OUTGOING) == 3
    assert len(arch.PICKING_TYPES_RETURNS) == 4


def test_3_routes() -> None:
    assert len(arch.ROUTES) == 3, "3 routes RPBM (Galleria, Genipa, Camion) -- Buy est amendee, pas creee"


def test_6_rules() -> None:
    assert len(arch.RULES) == 6, "6 regles metier -- la regle Acheter (buy_pull_id) est existante, pas creee"


def test_3_carriers() -> None:
    assert len(arch.CARRIERS) == 3


def test_unique_sequence_codes() -> None:
    codes = (
        [seq for seq, *_ in arch.PICKING_TYPES_INTERNAL]
        + [seq for seq, *_ in arch.PICKING_TYPES_INCOMING]
        + [seq for seq, *_ in arch.PICKING_TYPES_OUTGOING]
        + [seq for seq, *_ in arch.PICKING_TYPES_RETURNS]
    )
    assert len(codes) == len(set(codes)), f"sequence_code en double : {codes}"


def test_returns_reference_existing_incoming() -> None:
    incoming_codes = {seq for seq, *_ in arch.PICKING_TYPES_INCOMING}
    for seq, _name, _dest, return_code in arch.PICKING_TYPES_INCOMING:
        assert return_code.replace("IN", "RET") in [s for s, *_ in arch.PICKING_TYPES_RETURNS], \
            f"{seq} reference un retour absent de PICKING_TYPES_RETURNS"


def test_xmlid_distinct_from_gestion_stock_migration() -> None:
    from common import XMLID_PREFIX
    assert XMLID_PREFIX == "rpbm_arch1", (
        "le prefixe d'identifiant externe de ce dossier doit rester distinct de 'rpbm' "
        "(Jobs/Gestion Stock/import_odoo.py) pour ne jamais collisionner sur __import__"
    )


def main() -> None:
    test_34_picking_types()
    test_3_routes()
    test_6_rules()
    test_3_carriers()
    test_unique_sequence_codes()
    test_returns_reference_existing_incoming()
    test_xmlid_distinct_from_gestion_stock_migration()
    print("test_setup_stock_architecture : OK (7 assertions)")


if __name__ == "__main__":
    main()
