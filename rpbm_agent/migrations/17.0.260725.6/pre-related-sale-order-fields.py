"""Aligne les champs X'Glass de sale.order sur l'opportunite liee."""

from odoo import SUPERUSER_ID, api

from odoo.addons.rpbm_agent.hooks import _align_related_sale_order_fields


def migrate(cr, installed_version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _align_related_sale_order_fields(env)
