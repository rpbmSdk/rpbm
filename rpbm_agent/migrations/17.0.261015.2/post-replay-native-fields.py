"""Rejoue la recopie Studio -> natif (17.0.260921.1, idempotente) sur les bases installées à neuf
avant le ``post_init_hook`` (pré-prod après le « Branch Rebuild » du 2026-10-13) : un natif vide
est rempli, un natif renseigné n'est jamais remplacé (écarts journalisés). SQL seulement : ni
automatisation Studio, ni ``write_date``, ni recalcul de ``price_unit``.
"""
from odoo.addons.rpbm_agent.hooks import replay_native_fields


def migrate(cr, version):
    replay_native_fields(cr, version)
