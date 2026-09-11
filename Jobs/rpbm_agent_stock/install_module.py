"""Installe (ou verifie) le module rpbm_agent sur une instance Odoo, de facon rejouable.

    pyenv exec python install_module.py [--commit] [--profile ...]

Corrige un trou constate en direct sur rpbm-preprod apres un rebuild : le module n'apparait
meme pas dans ir.module.module (pas seulement desinstalle) tant que la liste des apps n'a
pas ete rafraichie. Sequence :

    1. ir.module.module.update_list()          -> fait apparaitre rpbm_agent s'il est absent
    2. recherche name = rpbm_agent              -> etat reel (installed/uninstalled/absent)
    3. button_immediate_install() si necessaire -> declenche pre_init_hook (FIELDS_TO_ENSURE)

Sans --commit : lecture seule, affiche l'etat trouve et l'action qui serait prise.
Secrets lus depuis ~/.paradigme/.env, jamais affiches. Voir Jobs/rpbm_agent_stock/README.md
pour le sequencement complet du lot (module -> catalogue -> architecture stock -> verification).
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable

from common import Odoo

MODULE_NAME = "rpbm_agent"
# Champ cree par le pre_init_hook du module (hooks.py, FIELDS_TO_ENSURE) : sa presence
# apres install est le signal le plus direct que le hook a bien tourne.
SENTINEL_FIELD = ("product.template", "x_studio_eurocode")


def check_state(odoo: Odoo) -> str:
    """Etat reel du module : 'absent', ou la valeur de ir.module.module.state."""
    found = odoo.search_read(
        "ir.module.module", [["name", "=", MODULE_NAME]], ["id", "state", "latest_version"]
    )
    if not found:
        return "absent"
    print(
        f"  ir.module.module : id={found[0]['id']} state={found[0]['state']} "
        f"version={found[0].get('latest_version')}"
    )
    return found[0]["state"]


def run(odoo: Odoo) -> int:
    model, field = SENTINEL_FIELD
    print(f"Recherche initiale de {MODULE_NAME} dans ir.module.module...")
    state = check_state(odoo)

    if state == "absent":
        print(f"  Absent de la liste des apps -> update_list() {'(dry-run)' if not odoo.commit else ''}")
        odoo.call("ir.module.module", "update_list", None, label="update_list")
        if odoo.commit:
            state = check_state(odoo)
        else:
            print("  [dry-run] etat post-update_list non observable sans --commit.")

    if state == "installed":
        print(f"{MODULE_NAME} deja installe : aucune action.")
    elif state == "absent" and not odoo.commit:
        print("Dry-run : impossible de savoir si update_list() suffira sans --commit.")
    else:
        module_id = odoo.resolve_id("ir.module.module", [["name", "=", MODULE_NAME]], MODULE_NAME) \
            if odoo.commit else None
        print(f"  Etat '{state}' -> button_immediate_install()")
        if module_id:
            odoo.call("ir.module.module", "button_immediate_install", module_id, label="install")
        else:
            print(f"  [dry-run] {MODULE_NAME} : button_immediate_install() serait appele.")

    if odoo.commit:
        fields = odoo.field_names(model)
        if field in fields:
            print(f"Verification : {model}.{field} present -> pre_init_hook execute.")
        else:
            print(f"ATTENTION : {model}.{field} absent apres install -> le hook n'a pas tourne.")
            return 1
    else:
        print(f"\nDry-run : relancer avec --commit pour installer reellement {MODULE_NAME}.")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--commit", action="store_true", help="ecrire reellement dans Odoo")
    parser.add_argument("--profile", default=None, help="profil paradigme-mcp (defaut : lu depuis .paradigme.yaml)")
    args = parser.parse_args(list(argv) if argv is not None else None)

    odoo = Odoo(args.profile, args.commit)
    mode = "ECRITURE" if args.commit else "dry-run (aucune ecriture)"
    print(f"install_module sur {odoo.url} (profil {odoo.profile!r}) — {mode}\n")
    return run(odoo)


if __name__ == "__main__":
    sys.exit(main())
