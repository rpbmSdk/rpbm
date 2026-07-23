"""Pousse les identifiants X'Glass / VSF (lus depuis .env, à la racine du
module) vers les ir.config_parameter d'une instance Odoo cible, via XML-RPC
standard.

Usage :
    python push_credentials.py

N'ajoute aucune dépendance : python-dotenv est déjà utilisé par le module,
xmlrpc.client est de la bibliothèque standard. Ne logge/affiche jamais les
valeurs des secrets, seulement le nom des clés traitées. Idempotent
(set_param écrase sans condition) : rejouable sans risque.

En plus des 4 clés existantes (XGLASS_USER, XGLASS_PASS, VSF_LOGIN,
VSF_PASSWORD), ce script lit optionnellement ODOO_URL/ODOO_DB/ODOO_LOGIN/
ODOO_PASSWORD dans .env pour se connecter à l'instance cible ; si absentes,
elles sont demandées de manière interactive (getpass pour les secrets).

Le compte Odoo utilisé (ODOO_LOGIN) doit être administrateur technique
(groupe base.group_system) : ir.config_parameter n'est accessible qu'à ce
groupe, sinon set_param lève une AccessError remontée ici comme
xmlrpc.client.Fault.
"""
import getpass
import os
import sys
import xmlrpc.client
from pathlib import Path

import dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
dotenv.load_dotenv(ENV_PATH)

CREDENTIAL_KEYS = ["XGLASS_USER", "XGLASS_PASS", "VSF_LOGIN", "VSF_PASSWORD"]


def _get_or_prompt(key: str, secret: bool = False) -> str:
    value = os.getenv(key)
    if value:
        return value
    return getpass.getpass(f"{key}: ") if secret else input(f"{key}: ")


def main() -> None:
    print(f"Lecture depuis {ENV_PATH} (variables d'environnement / saisie manuelle en secours).")

    odoo_url = _get_or_prompt("ODOO_URL").rstrip("/")
    odoo_db = _get_or_prompt("ODOO_DB")
    odoo_login = _get_or_prompt("ODOO_LOGIN")
    odoo_password = _get_or_prompt("ODOO_PASSWORD", secret=True)

    credentials = {key: _get_or_prompt(key, secret=True) for key in CREDENTIAL_KEYS}

    common = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/common")
    uid = common.authenticate(odoo_db, odoo_login, odoo_password, {})
    if not uid:
        print("Échec d'authentification Odoo (identifiants invalides ?). Abandon.", file=sys.stderr)
        sys.exit(1)

    models = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/object")

    for key, value in credentials.items():
        try:
            models.execute_kw(
                odoo_db, uid, odoo_password,
                "ir.config_parameter", "set_param",
                [key, value],
            )
        except xmlrpc.client.Fault as e:
            print(f"Échec de l'écriture de {key} : {e.faultString}", file=sys.stderr)
            sys.exit(1)
        print(f"{key} : écrit avec succès sur {odoo_url} (db={odoo_db}).")

    print("Terminé.")


if __name__ == "__main__":
    main()
