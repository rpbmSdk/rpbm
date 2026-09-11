"""Client Odoo XML-RPC partage par les scripts de ce dossier.

Meme patron que Jobs/Gestion Stock/import_odoo.py, volontairement duplique plutot
qu'importe entre dossiers : les deux traitent des domaines differents (catalogue
articles vs module + architecture stock) et ne doivent pas partager de dependance
fragile via sys.path.

Connexion resolue en appliquant litteralement les skills paradigme-mcp-local puis
paradigme-mcp, jamais par une URL ou un nom de profil code en dur : .paradigme.yaml
(a la racine du depot) donne le nom de profil, ~/.paradigme/paradigme_odoo_mcp.yaml
ses metadonnees, ~/.paradigme/.env ses secrets. Ne jamais afficher un secret. Ce
choix rend ces scripts rejouables tels quels sur un autre profil (production, par
exemple) via --profile, sans toucher au code.

Aucune dependance PyYAML : ce paquet n'est pas declare dans requirements.txt et n'est
pas installe dans le .venv du projet (verifie) -- un mini-parseur suffit pour les deux
fichiers YAML ici en jeu (mappings imbriques, scalaires, pas de listes).

Toute methode d'ecriture est protegee par le flag --commit ; sans lui le client refuse
silencieusement d'appeler load/create/write/unlink/button_*/call de methode et affiche
ce qu'il aurait fait.
"""

from __future__ import annotations

import re
import unicodedata
import xmlrpc.client
from pathlib import Path

ENV_PATH = Path.home() / ".paradigme" / ".env"
PROFILES_PATH = Path.home() / ".paradigme" / "paradigme_odoo_mcp.yaml"

# Prefixe reserve aux enregistrements de ce dossier (architecture stock), distinct de
# celui de Jobs/Gestion Stock/import_odoo.py (rpbm_<genre>_<cle>) pour ne jamais
# collisionner sur le meme espace de noms __import__.
XMLID_MODULE = "__import__"
XMLID_PREFIX = "rpbm_arch1"

# Prefixe des donnees de recette (ventes/transferts de test), repris tel quel de la
# procedure d'audit existante (Jobs/Gestion Stock/architectures/audits/
# procedure-audit-implementation.md §4) pour rester compatible avec les runs manuels
# deja produits.
AUDIT_PREFIX = "ARCH1-AUDIT"


def load_env(path: Path = ENV_PATH) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"Fichier de secrets introuvable : {path}")
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("'\"")
    return values


def _parse_simple_yaml(text: str) -> dict:
    """Parseur minimal : mappings imbriques par indentation (pas de listes, pas
    d'ancrages) -- suffisant pour .paradigme.yaml et paradigme_odoo_mcp.yaml."""
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, _, value = line.strip().partition(":")
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


def find_paradigme_config(start: Path | None = None) -> Path:
    """Cherche .paradigme.yml puis .paradigme.yaml depuis start vers ses parents,
    comme le decrit la skill paradigme-mcp-local. Jamais de profil par defaut : si
    rien n'est trouve, on arrete plutot que de deviner."""
    current = (start or Path(__file__).resolve().parent)
    for directory in [current, *current.parents]:
        for name in (".paradigme.yml", ".paradigme.yaml"):
            candidate = directory / name
            if candidate.exists():
                return candidate
    raise FileNotFoundError(
        f"Aucun .paradigme.yml/.paradigme.yaml trouve depuis {current} vers ses parents."
    )


def resolve_profile_name(profile: str | None) -> str:
    if profile:
        return profile
    config_path = find_paradigme_config()
    config = _parse_simple_yaml(config_path.read_text(encoding="utf-8"))
    name = config.get("odoo", {}).get("profile")
    if not name:
        raise RuntimeError(f"odoo.profile absent ou vide dans {config_path}")
    return name


def load_profile(profile: str | None = None) -> dict[str, str]:
    """Resout url/database/transport/username/password pour un profil, en
    appliquant litteralement paradigme-mcp : profile=None lit .paradigme.yaml,
    sinon le nom est pris tel quel (utile pour cibler explicitement un autre
    profil, ex. la production, sans toucher au fichier local)."""
    profile_name = resolve_profile_name(profile)

    if not PROFILES_PATH.exists():
        raise FileNotFoundError(f"Fichier de profils introuvable : {PROFILES_PATH}")
    profiles = _parse_simple_yaml(PROFILES_PATH.read_text(encoding="utf-8")).get("profiles", {})
    entry = profiles.get(profile_name)
    if not entry:
        raise RuntimeError(f"Profil {profile_name!r} absent de {PROFILES_PATH}")

    env = load_env()

    def resolve(field: str) -> str:
        if field in entry:
            return entry[field]
        env_key = entry.get(f"{field}_env")
        if not env_key:
            raise RuntimeError(f"Ni {field!r} ni {field}_env defini pour le profil {profile_name!r}")
        value = env.get(env_key)
        if not value:
            raise RuntimeError(f"Variable {env_key!r} absente ou vide dans {ENV_PATH}")
        return value

    if "url" not in entry:
        raise RuntimeError(f"Champ 'url' absent du profil {profile_name!r} ({PROFILES_PATH}).")
    return {
        "profile": profile_name,
        "url": entry["url"],
        "database": resolve("database"),
        "transport": entry.get("transport", "xmlrpc"),
        "username": resolve("username"),
        "password": resolve("password"),
    }


def normalize_key(value: str) -> str:
    """Cle normalisee : sans accent, espaces uniques, casse indifferente."""
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", normalize_key(value).lower()).strip("_")


def xmlid(kind: str, key: str) -> str:
    slug = slugify(key)
    if not slug:
        raise ValueError(f"Identifiant externe vide pour {kind} : {key!r}")
    return f"{XMLID_PREFIX}_{kind}_{slug}"


def audit_tag(run_id: str, scenario: str) -> str:
    """Marqueur pose sur toute donnee de recette creee par verify_flows.py.

    Format ARCH1-AUDIT-<run_id>-<scenario>, identique a la convention de la procedure
    d'audit manuelle existante - rollback.py recherche exactement ce prefixe et ne
    touche jamais a autre chose.
    """
    return f"{AUDIT_PREFIX}-{run_id}-{scenario}"


class Odoo:
    """Client XML-RPC minimal. Les lectures sont toujours autorisees ; toute ecriture
    (load/create/write/unlink/methode) est un no-op signale tant que commit est faux."""

    def __init__(self, profile: str | None = None, commit: bool = False) -> None:
        conn = load_profile(profile)
        if conn["transport"] != "xmlrpc":
            raise RuntimeError(
                f"Profil {conn['profile']!r} : transport {conn['transport']!r} non supporte "
                "par ce client (xmlrpc uniquement)."
            )

        self.profile = conn["profile"]
        self.url = conn["url"].rstrip("/")
        self.db = conn["database"]
        self.password = conn["password"]
        self.commit = commit

        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.uid = common.authenticate(self.db, conn["username"], self.password, {})
        if not self.uid:
            raise RuntimeError(f"Echec d'authentification Odoo sur {self.url} (profil {self.profile!r}).")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    # --- lecture, toujours autorisee ---------------------------------------------------

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

    def resolve_xmlid(self, xml_id: str) -> int | None:
        """id reel derriere un identifiant externe __import__.<xml_id>, ou None."""
        found = self.search_read(
            "ir.model.data",
            [["module", "=", XMLID_MODULE], ["name", "=", xml_id]],
            ["res_id"],
            limit=1,
        )
        return found[0]["res_id"] if found else None

    # --- ecriture, gardee par --commit --------------------------------------------------

    def call(self, model: str, method: str, ids: list[int] | int | None, *args, label: str = "", **kwargs):
        """Appel de methode arbitraire (button_*, action_*, update_list...).

        Hors du jeu d'outils model_search_read/write/create/unlink expose par le
        serveur MCP paradigme-mcp : necessaire pour installer un module ou confirmer
        un document, d'ou l'usage direct de XML-RPC dans tout ce dossier.

        ids=None pour une methode de modele qui ne prend aucun recordset cible
        (ex. update_list()) : aucun argument ids n'est alors envoye du tout, pas
        meme une liste vide -- Odoo la passerait sinon comme argument positionnel
        reel de la methode (`update_list() takes 1 positional argument but 2 were
        given`).
        """
        if isinstance(ids, int):
            ids = [ids]
        if not self.commit:
            shown = () if ids is None else (ids,)
            print(f"  [dry-run] {label or method} : {model}.{method}({', '.join(map(str, shown + args))}, {kwargs})")
            return None
        call_args = args if ids is None else (ids, *args)
        return self.execute(model, method, *call_args, **kwargs)

    def load(self, model: str, fields: list[str], rows: list[list], label: str) -> dict:
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

        result = self.execute(
            model, "load", fields, rows,
            context={"tracking_disable": True, "mail_create_nolog": True},
        )
        ids = result.get("ids")
        if ids:
            report["loaded"] = len(ids)
        else:
            report["failed"] = len(rows)
            report["messages"] = result.get("messages", [])
            print(f"  {label} : lot REJETE ({len(rows)} lignes) : {report['messages']}")
        print(f"  {label} : {report['loaded']} charge(s), {report['failed']} en echec.")
        return report

    def unlink(self, model: str, ids: list[int], label: str = "") -> bool:
        if not ids:
            return True
        if not self.commit:
            print(f"  [dry-run] suppression {label or model} : {ids}")
            return False
        return bool(self.execute(model, "unlink", ids))
