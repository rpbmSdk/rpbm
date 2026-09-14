"""Pousse les identifiants X'Glass / VSF vers une instance Odoo cible.

La cible Odoo est résolue exclusivement depuis le profil Paradigme sélectionné
par ``.paradigme.yaml`` : les métadonnées viennent de
``~/.paradigme/paradigme_odoo_mcp.yaml`` et les secrets Odoo de
``~/.paradigme/.env``. Les quatre secrets des portails restent dans le
``.env`` local du module.

Usage :
    python push_credentials.py

N'ajoute aucune dépendance : python-dotenv est déjà utilisé par le module,
xmlrpc.client est de la bibliothèque standard. Ne logge/affiche jamais les
valeurs des secrets, seulement le profil et les noms de clés traitées.
Idempotent (set_param écrase sans condition) : rejouable sans risque.

Le script échoue explicitement si le profil projet, le profil global, une
référence ``*_env`` ou une valeur requise est absente. Il ne lit ni
``.env.local``, ni les variables d'environnement du processus, et ne demande
pas de cible Odoo de manière interactive : cela évite de pousser vers une
instance différente de celle sélectionnée par le projet.

Le compte Odoo utilisé (ODOO_LOGIN) doit être administrateur technique
(groupe base.group_system) : ir.config_parameter n'est accessible qu'à ce
groupe, sinon set_param lève une AccessError remontée ici comme
xmlrpc.client.Fault.
"""
import sys
import xmlrpc.client
from pathlib import Path

import dotenv

MODULE_ENV_PATH = Path(__file__).resolve().parent / ".env"
PARADIGME_HOME = Path.home() / ".paradigme"
PARADIGME_ENV_PATH = PARADIGME_HOME / ".env"
PARADIGME_PROFILES_PATH = PARADIGME_HOME / "paradigme_odoo_mcp.yaml"

CREDENTIAL_KEYS = ["XGLASS_USER", "XGLASS_PASS", "VSF_LOGIN", "VSF_PASSWORD"]


def _parse_simple_yaml(text: str) -> dict:
    """Parse les mappings imbriqués utilisés par les deux fichiers Paradigme.

    PyYAML n'est pas une dépendance du module. Le format des fichiers de
    profils est volontairement limité à des mappings et des scalaires.
    """
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, separator, value = line.strip().partition(":")
        if not separator or not key:
            raise ValueError(f"Ligne YAML non supportée : {raw_line!r}")
        value = value.strip().strip("'\"")
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value:
            parent[key] = value
        else:
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
    return root


def _load_env(path: Path) -> dict[str, str]:
    """Lit un fichier dotenv sans modifier ``os.environ``."""
    if not path.exists():
        raise FileNotFoundError(f"Fichier de secrets introuvable : {path}")
    values = dotenv.dotenv_values(path, interpolate=False)
    return {key: value for key, value in values.items() if value is not None}


def _find_project_config() -> Path:
    """Cherche le premier .paradigme.yaml dans le dossier et ses parents."""
    start = Path(__file__).resolve().parent
    for directory in (start, *start.parents):
        for name in (".paradigme.yml", ".paradigme.yaml"):
            candidate = directory / name
            if candidate.exists():
                return candidate
    raise FileNotFoundError(
        f"Aucun .paradigme.yml/.paradigme.yaml trouve depuis {start}."
    )


def _resolve_odoo_profile() -> dict[str, str]:
    """Résout la connexion Odoo selon le contrat Paradigme, sans fallback."""
    project_config_path = _find_project_config()
    project_config = _parse_simple_yaml(project_config_path.read_text(encoding="utf-8"))
    if project_config.get("version") != "1":
        raise RuntimeError(f"Version de .paradigme.yaml non supportée : {project_config_path}")

    profile_name = project_config.get("odoo", {}).get("profile")
    if not profile_name:
        raise RuntimeError(f"odoo.profile absent ou vide dans {project_config_path}")

    if not PARADIGME_PROFILES_PATH.exists():
        raise FileNotFoundError(f"Fichier de profils introuvable : {PARADIGME_PROFILES_PATH}")
    profiles_config = _parse_simple_yaml(
        PARADIGME_PROFILES_PATH.read_text(encoding="utf-8")
    )
    profile = profiles_config.get("profiles", {}).get(profile_name)
    if not profile:
        raise RuntimeError(
            f"Profil {profile_name!r} absent de {PARADIGME_PROFILES_PATH}"
        )

    env = _load_env(PARADIGME_ENV_PATH)

    def resolve(field: str) -> str:
        literal = profile.get(field)
        env_key = profile.get(f"{field}_env")
        if literal and env_key:
            raise RuntimeError(
                f"Le profil {profile_name!r} définit à la fois {field} et {field}_env."
            )
        if literal:
            return literal
        if not env_key:
            raise RuntimeError(
                f"Ni {field!r} ni {field}_env défini pour le profil {profile_name!r}"
            )
        value = env.get(env_key)
        if not value:
            raise RuntimeError(
                f"Variable {env_key!r} absente ou vide dans {PARADIGME_ENV_PATH}"
            )
        return value

    transport = profile.get("transport")
    if transport != "xmlrpc":
        raise RuntimeError(
            f"Profil {profile_name!r} : transport {transport!r} non supporté par ce script."
        )
    return {
        "profile": profile_name,
        "url": resolve("url").rstrip("/"),
        "database": resolve("database"),
        "transport": transport,
        "username": resolve("username"),
        "password": resolve("password"),
    }


def _load_portal_credentials() -> dict[str, str]:
    values = _load_env(MODULE_ENV_PATH)
    missing = [key for key in CREDENTIAL_KEYS if not values.get(key)]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Clé(s) portail absente(s) ou vide(s) dans {MODULE_ENV_PATH} : {joined}")
    return {key: values[key] for key in CREDENTIAL_KEYS}


def main() -> None:
    connection = _resolve_odoo_profile()
    credentials = _load_portal_credentials()
    print(
        f"Profil Odoo sélectionné : {connection['profile']} "
        f"(transport={connection['transport']})"
    )

    common = xmlrpc.client.ServerProxy(f"{connection['url']}/xmlrpc/2/common")
    uid = common.authenticate(
        connection["database"], connection["username"], connection["password"], {}
    )
    if not uid:
        print("Échec d'authentification Odoo (identifiants invalides ?). Abandon.", file=sys.stderr)
        sys.exit(1)

    models = xmlrpc.client.ServerProxy(f"{connection['url']}/xmlrpc/2/object")

    for key, value in credentials.items():
        try:
            models.execute_kw(
                connection["database"], uid, connection["password"],
                "ir.config_parameter", "set_param",
                [key, value],
            )
        except xmlrpc.client.Fault as e:
            print(f"Échec de l'écriture de {key} : {e.faultString}", file=sys.stderr)
            sys.exit(1)
        print(f"{key} : écrit avec succès sur le profil {connection['profile']}.")

    print("Terminé.")


if __name__ == "__main__":
    main()
