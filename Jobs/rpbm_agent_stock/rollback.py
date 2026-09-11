"""Annule/supprime les donnees de recette d'un run verify_flows.py -- jamais rien d'autre.

    pyenv exec python rollback.py --run 20260912 [--commit] [--i-understand-this-is-production]

Ce n'est PAS un nettoyage automatique post-test : c'est un script separe, declenche
explicitement par un operateur, qui n'agit que sur les enregistrements portant le tag
ARCH1-AUDIT-<run>-* d'un run donne (voir common.audit_tag). La procedure d'audit existante
(architectures/audits/README.md) interdit tout nettoyage silencieux des donnees de recette ;
ce script respecte ce principe en ne s'executant jamais tout seul, uniquement sur demande, avec
un rapport explicite de ce qu'il ne peut pas faire.

Limite reelle d'Odoo, pas de ce script : une vente/un achat/un transfert confirme ne s'unlink
pas -- Odoo impose l'annulation d'abord. Le rollback ANNULE ce qui est confirme, SUPPRIME ce
qu'Odoo permet de supprimer, et RAPPORTE ce qui reste (document annule mais non supprimable,
numero de sequence deja consomme -- non recuperable, comportement normal d'Odoo). Ne jamais
presenter cela comme un echec du script.

Garde-fou production : si le nom de la base cible ne contient ni "preprod" ni "staging" ni
"test", --commit exige en plus --i-understand-this-is-production.

Dry-run par defaut : liste ce qui serait annule/supprime sans rien ecrire.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable

from common import Odoo, AUDIT_PREFIX

def find_tagged_orders(odoo: Odoo, run_id: str) -> list[dict]:
    """Point d'entree unique du tag : sale.order.client_order_ref. Les pickings/achats crees
    par la confirmation d'une vente ne portent PAS ce tag -- leur `origin` est le NOM de la
    vente (ex. "SO7748"), pas le client_order_ref. Il faut donc d'abord resoudre les ventes,
    puis chercher les documents aval par origin=nom de vente (constate en direct : une
    premiere version de ce script cherchait `origin like <tag>` sur stock.picking et ne
    trouvait jamais rien)."""
    return odoo.search_read(
        "sale.order", [["client_order_ref", "like", f"{AUDIT_PREFIX}-{run_id}-"]],
        ["id", "name", "state"],
    )


def find_related_by_origin(odoo: Odoo, model: str, order_names: list[str]) -> list[dict]:
    if not order_names:
        return []
    return odoo.search_read(model, [["origin", "in", order_names]], ["id", "name", "state"])


def _cancel(odoo: Odoo, model: str, record_id: int) -> None:
    """Annule un enregistrement, avec deux comportements Odoo constates en direct a contourner :

    - sale.order.action_cancel() ouvre un assistant de confirmation (sale.order.cancel) en
      interface -- appele par XML-RPC, il retourne juste ce dict sans jamais changer l'etat.
      Ecrire l'etat directement pour une donnee de recette sans facture ni consequence a
      notifier.
    - purchase.order.button_cancel() change bien l'etat, mais ne retourne rien (None) : le
      point de terminaison XML-RPC (pas JSON-RPC) ne sait pas serialiser None et leve une
      Fault meme quand l'ecriture a reussi. Capturee ici, l'etat reel est verifie ensuite par
      l'appelant plutot que de faire confiance a l'absence d'exception.
    """
    if model == "sale.order":
        odoo.execute(model, "write", [record_id], {"state": "cancel"})
        return
    cancel_method = {"purchase.order": "button_cancel", "stock.picking": "action_cancel"}[model]
    try:
        odoo.execute(model, cancel_method, [record_id])
    except Exception:  # noqa: BLE001 -- verifie par l'etat reel, pas par l'absence d'exception
        pass


def rollback_record(odoo: Odoo, model: str, record: dict, remaining: list[str]) -> None:
    label = f"{model} {record.get('name', record['id'])}"
    state = record.get("state")

    if not odoo.commit:
        print(f"  [dry-run] {label} (state={state}) : annuler si necessaire, puis supprimer")
        return

    # Essayer la suppression directe d'abord plutot que de deviner selon l'etat initial : un
    # bon de commande brouillon (draft) refuse quand meme l'unlink dans cette version d'Odoo
    # ("vous devez d'abord l'annuler"), constate en direct -- draft n'est donc pas toujours
    # suffisant, contrairement a l'hypothese initiale de ce script.
    try:
        odoo.execute(model, "unlink", [record["id"]])
        print(f"  {label} : supprime directement (etat initial {state!r}).")
        return
    except Exception:  # noqa: BLE001 -- on retente apres annulation ci-dessous
        pass

    if state != "cancel":
        _cancel(odoo, model, record["id"])
        refreshed = odoo.search_read(model, [["id", "=", record["id"]]], ["state"])
        state = refreshed[0]["state"] if refreshed else state
        print(f"  {label} : annule (etat={state}).")

    try:
        odoo.execute(model, "unlink", [record["id"]])
        print(f"  {label} : supprime apres annulation.")
    except Exception as error:  # noqa: BLE001
        remaining.append(f"{label} : annule mais non supprimable ({error}) -- normal si des ecritures/mouvements y sont rattaches.")


def run(odoo: Odoo, run_id: str) -> int:
    remaining: list[str] = []
    total = 0

    orders = find_tagged_orders(odoo, run_id)
    order_names = [o["name"] for o in orders]
    print(f"\n=== sale.order tagues (client_order_ref) {AUDIT_PREFIX}-{run_id}-* : {len(orders)} ===")
    for order in orders:
        print(f"  {order['name']} (id {order['id']}, state={order['state']})")

    # Documents aval d'abord (pickings puis achats), la vente elle-meme en dernier : Odoo
    # refuse d'annuler une vente dont un picking est encore en cours de traitement.
    for model in ("stock.picking", "purchase.order"):
        records = find_related_by_origin(odoo, model, order_names)
        print(f"\n=== {model} lies (origin) aux ventes ci-dessus : {len(records)} ===")
        for record in records:
            total += 1
            rollback_record(odoo, model, record, remaining)

    print(f"\n=== sale.order a annuler/supprimer : {len(orders)} ===")
    for order in orders:
        total += 1
        rollback_record(odoo, "sale.order", order, remaining)

    print(f"\n{total} enregistrement(s) trouve(s) pour le run {run_id!r}.")
    if remaining:
        print(f"\n{len(remaining)} element(s) restant(s) (comportement Odoo normal, pas une erreur de ce script) :")
        for line in remaining:
            print(f"  - {line}")
    elif total == 0:
        print("Rien a nettoyer : aucun enregistrement ne porte ce tag.")
    else:
        print("Tout supprime ou annule proprement.")
    if not odoo.commit:
        print("\nDry-run : relancer avec --commit pour executer reellement.")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True, help="identifiant de run passe a verify_flows.py --run")
    parser.add_argument("--commit", action="store_true", help="ecrire reellement dans Odoo")
    parser.add_argument(
        "--i-understand-this-is-production", action="store_true",
        help="requis en plus de --commit si la base cible ne semble pas etre une preprod/staging/test",
    )
    parser.add_argument("--profile", default=None, help="profil paradigme-mcp (defaut : lu depuis .paradigme.yaml)")
    args = parser.parse_args(list(argv) if argv is not None else None)

    odoo = Odoo(args.profile, args.commit)
    db_normalized = odoo.db.lower().replace("-", "").replace("_", "")
    is_safe_env = any(word in db_normalized for word in ("preprod", "staging", "test"))
    if args.commit and not is_safe_env and not args.i_understand_this_is_production:
        parser.error(
            f"La base {odoo.db!r} ne contient ni 'preprod' ni 'staging' ni 'test' dans son nom. "
            "Repasser avec --i-understand-this-is-production si c'est bien voulu."
        )

    mode = "ECRITURE" if args.commit else "dry-run (aucune ecriture)"
    print(f"rollback run={args.run} sur {odoo.url} (profil {odoo.profile!r}, base {odoo.db}) — {mode}")
    return run(odoo, args.run)


if __name__ == "__main__":
    sys.exit(main())
