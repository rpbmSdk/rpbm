"""Rejoue la migration 17.0.260921.1 (idempotente) : dates MEC aux formats MM/YY, YYYY et JJ/MM/AAAA
restées vides, et champs créés par l'ancien module conservés à tort (références entre eux, ou
homonymes sur d'autres modèles) lors du premier passage sur le build 37939198.
"""
import importlib.util
from pathlib import Path


def migrate(cr, version):
    path = Path(__file__).resolve().parents[1] / "17.0.260921.1" / "post-native-fields.py"
    spec = importlib.util.spec_from_file_location("rpbm_agent_post_native_fields", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.migrate(cr, version)
