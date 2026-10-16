"""Installation du module.

Les migrations ne tournent pas à l'installation (``odoo/modules/migration.py``) : le
``post_init_hook`` rejoue celles qui sont idempotentes, pour qu'une base installée à neuf
(ex. « Branch Rebuild » d'Odoo.sh) ait ses champs natifs remplis depuis les champs Studio.
"""
import importlib.util
from pathlib import Path

MIGRATIONS = Path(__file__).resolve().parent / "migrations"


def run_migration(cr, relative_path, version=None):
    """Exécute ``migrate(cr, version)`` d'un script de ``migrations/`` (nom à tirets, non importable)."""
    path = MIGRATIONS / relative_path
    spec = importlib.util.spec_from_file_location("rpbm_agent_" + path.stem.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.migrate(cr, version)


def replay_native_fields(cr, version=None):
    run_migration(cr, "17.0.260921.1/post-native-fields.py", version)


def post_init_hook(env):
    env.flush_all()  # les scripts lisent et écrivent en SQL
    replay_native_fields(env.cr)
    run_migration(env.cr, "17.0.260928.3/post-roles-achats.py")
