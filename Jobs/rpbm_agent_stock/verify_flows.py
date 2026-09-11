"""Recette fonctionnelle des chemins logistiques de vente -- ecrit de vraies donnees de test.

    pyenv exec python verify_flows.py --run 20260912 --tests T1,T3 --commit

Operationnalise Jobs/Gestion Stock/architectures/audits/procedure-audit-implementation.md §8-9
(recette T1-T8/MTO) et architecture-1-test-registry.md (choix des articles/racks de recette).
Chaque enregistrement cree porte le tag ARCH1-AUDIT-<run>-<scenario> (voir common.audit_tag) dans
client_order_ref, retrouvable ensuite par rollback.py -- jamais de nettoyage automatique ici,
conformement au principe de la procedure existante ("les mouvements, commandes, quants et
partenaires de recette ne sont pas supprimes ni annules" par ce script).

Contrainte stricte reprise de la procedure : ne jamais valider physiquement une reception, un
transfert ou une livraison de recette (pas de button_validate). Seule la creation/confirmation
de documents est jouee, pour observer la reservation et le picking genere -- pas leur execution.

Seuls T1 et T3 sont implementes ici comme exemples concrets et directement rejouables ; T2,
T4-T8 et MTO-1..4 suivent exactement le meme patron (choisir un article via le registre, creer
une vente taggee, observer le picking genere) -- a ajouter dans TESTS au fur et a mesure,
voir architecture-1-test-registry.md pour le choix de l'article de chaque scenario.

Sans --commit : dry-run, decrit ce qui serait cree sans rien ecrire.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from typing import Callable, Iterable

from common import Odoo, audit_tag


def _pick_product(odoo: Odoo, domain: list) -> dict | None:
    found = odoo.search_read(
        "product.product", domain, ["id", "name", "default_code"], limit=1
    )
    return found[0] if found else None


def _pick_product_at_location(odoo: Odoo, location_id: int) -> dict | None:
    """Un produit avec un quant > 0 precisement a cet emplacement (pas juste qty_available
    globale) : necessaire pour un test qui pretend verifier une reservation depuis ce site."""
    quants = odoo.search_read(
        "stock.quant", [["location_id", "=", location_id], ["quantity", ">", 0]],
        ["product_id"], limit=1,
    )
    if not quants:
        return None
    product_id = quants[0]["product_id"][0]
    return odoo.search_read("product.product", [["id", "=", product_id]], ["id", "name", "default_code"])[0]


def _create_sale_order(
    odoo: Odoo, run_id: str, scenario: str, product: dict, warehouse_id: int, carrier_name: str,
) -> dict:
    """Cree une vente taguee, en posant explicitement le mode d'expedition (carrier_id).

    Sans lui, Odoo retombe sur la route native de l'entrepot (RPBM: Livraisons Galleria, la
    seule active par defaut) et n'invoque jamais nos 3 nouvelles routes -- constate en direct :
    un premier essai sans carrier_id a produit ce fallback silencieux sur les deux scenarios.
    Le carrier est precisement le mecanisme documente pour eviter ca (questions-ouvertes.md,
    architectures-stock.md § B5 bis).
    """
    tag = audit_tag(run_id, scenario)
    partner = odoo.resolve_id("res.partner", [["name", "=", "RPBM"]], "partenaire RPBM (client de recette)")
    carrier_id = odoo.resolve_id("delivery.carrier", [["name", "=", carrier_name]], f"transporteur {carrier_name!r}")
    order_vals = {
        "partner_id": partner,
        "client_order_ref": tag,
        "warehouse_id": warehouse_id,
        "carrier_id": carrier_id,
        "order_line": [(0, 0, {"product_id": product["id"], "product_uom_qty": 1})],
    }
    if not odoo.commit:
        print(f"  [dry-run] {scenario} ({tag}) : sale.order pour {product['name']!r} sur entrepot {warehouse_id}, "
              f"transporteur {carrier_name!r}")
        return {"tag": tag, "order_id": None, "order_name": None, "picking_ids": []}

    order_id = odoo.execute("sale.order", "create", order_vals)
    odoo.execute("sale.order", "action_confirm", [order_id])
    order = odoo.search_read("sale.order", [["id", "=", order_id]], ["picking_ids", "name"])[0]
    print(f"  {scenario} ({tag}) : {order['name']} confirmee, pickings {order['picking_ids']}")
    return {"tag": tag, "order_id": order_id, "order_name": order["name"], "picking_ids": order["picking_ids"]}


def test_t1_article_galleria(odoo: Odoo, run_id: str) -> dict:
    """T1 -- article stocke a Galleria, vente Galleria -> controle principal GALL/OUT."""
    warehouse = odoo.resolve_id("stock.warehouse", [["name", "=", "RPBM"]], "entrepot RPBM")
    galleria_id = odoo.resolve_id("stock.location", [["name", "=ilike", "Galleria"]], "Galleria")
    product = _pick_product_at_location(odoo, galleria_id)
    if not product:
        print("  T1 : aucun article en stock a Galleria trouve pour la recette -- test non joue.")
        return {"scenario": "T1", "status": "NOT_RUN"}
    result = _create_sale_order(odoo, run_id, "T1", product, warehouse, "Retrait / pose Galleria")
    if odoo.commit and result["picking_ids"]:
        picking = odoo.search_read(
            "stock.picking", [["id", "in", result["picking_ids"]]],
            ["picking_type_id", "state"],
        )
        # picking_type_id.name affiche "RPBM: Livraison Galleria" (libelle humain), jamais le
        # sequence_code "GALL/OUT" -- comparer sur sequence_code, pas sur une sous-chaine du nom.
        types = odoo.search_read(
            "stock.picking.type", [["id", "in", [p["picking_type_id"][0] for p in picking]]],
            ["id", "sequence_code"],
        )
        codes = {t["id"]: t["sequence_code"] for t in types}
        gall_out = any(codes.get(p["picking_type_id"][0]) == "GALL/OUT" for p in picking)
        print(f"  T1 controle GALL/OUT : {'PASS' if gall_out else 'FAIL'} ({picking})")
    return {"scenario": "T1", **result}


def test_t3_article_absent(odoo: Odoo, run_id: str) -> dict:
    """T3 -- article absent de tout emplacement -> doit declencher achat + reception + transfert."""
    warehouse = odoo.resolve_id("stock.warehouse", [["name", "=", "RPBM"]], "entrepot RPBM")
    product = _pick_product(odoo, [["qty_available", "=", 0], ["seller_ids", "!=", False]])
    if not product:
        print("  T3 : aucun article sans stock avec fournisseur trouve -- test non joue.")
        return {"scenario": "T3", "status": "NOT_RUN"}
    result = _create_sale_order(odoo, run_id, "T3", product, warehouse, "Retrait / pose Galleria")
    if odoo.commit and result["order_id"]:
        # origin porte le NOM de la vente (ex. "SO7753"), jamais le tag client_order_ref --
        # meme lecon que rollback.py : chercher par tag ici ne trouve jamais rien.
        purchase = odoo.search_read(
            "purchase.order", [["origin", "=", result["order_name"]]], ["id", "name", "state"]
        )
        print(f"  T3 controle achat declenche : {'PASS' if purchase else 'FAIL'} ({purchase})")
    return {"scenario": "T3", **result}


TESTS: dict[str, Callable[[Odoo, str], dict]] = {
    "T1": test_t1_article_galleria,
    "T3": test_t3_article_absent,
}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", default=date.today().strftime("%Y%m%d"), help="identifiant de run, repris par rollback.py")
    parser.add_argument("--tests", default=",".join(TESTS), help=f"liste separee par des virgules parmi {list(TESTS)}")
    parser.add_argument("--commit", action="store_true", help="ecrire reellement dans Odoo (cree de vraies ventes de recette)")
    parser.add_argument("--profile", default=None, help="profil paradigme-mcp (defaut : lu depuis .paradigme.yaml)")
    args = parser.parse_args(list(argv) if argv is not None else None)

    requested = [name.strip() for name in args.tests.split(",") if name.strip()]
    unknown = [name for name in requested if name not in TESTS]
    if unknown:
        parser.error(f"tests inconnus : {unknown} -- disponibles : {list(TESTS)}")

    odoo = Odoo(args.profile, args.commit)
    mode = "ECRITURE (donnees de recette reelles)" if args.commit else "dry-run (aucune ecriture)"
    print(f"verify_flows run={args.run} sur {odoo.url} (profil {odoo.profile!r}) — {mode}\n")

    results = [TESTS[name](odoo, args.run) for name in requested]
    print(f"\n{len(results)} scenario(s) joue(s). Rappel : aucun nettoyage automatique -- "
          f"utiliser rollback.py --run {args.run} quand la recette est terminee.")
    if not args.commit:
        print("Aucune ecriture effectuee. Relancer avec --commit pour creer les donnees de recette.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
