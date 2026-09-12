"""Bascule les vues et courriels vers les champs Fleet apres rechargement."""

from odoo import SUPERUSER_ID, api

from odoo.addons.rpbm_agent.hooks import _replace_legacy_vehicle_references


def migrate(cr, installed_version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _replace_legacy_vehicle_references(env)
