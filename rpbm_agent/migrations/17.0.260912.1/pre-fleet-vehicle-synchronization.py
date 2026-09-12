"""Installe les champs Fleet et migre les references Studio connues."""

from odoo import SUPERUSER_ID, api

from odoo.addons.rpbm_agent.hooks import (
    _align_related_sale_order_fields,
    pre_init_hook,
)


def migrate(cr, installed_version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    pre_init_hook(env)
    _align_related_sale_order_fields(env)
