"""Crée le champ Eurocode avant le chargement de la vue produit."""

from odoo import SUPERUSER_ID, api

from odoo.addons.rpbm_agent.hooks import pre_init_hook


def migrate(cr, installed_version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    pre_init_hook(env)
