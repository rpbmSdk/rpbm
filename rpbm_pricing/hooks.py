"""Mises en place du module.

Chaque mise en place est une méthode idempotente appelée par ``setup(env)`` : à l'installation
par ``post_init_hook``, puis par les migrations des versions qui en ajoutent une (les migrations
ne tournent pas à l'installation, ``odoo/modules/migration.py``).
"""
import logging

_logger = logging.getLogger(__name__)


def setup(env):
    _logger.info("rpbm_pricing: mise en place")
    env["sale.order.template"]._rpbm_template_regime_setup()
    env["sale.order.line"]._rpbm_rule8_install()


def post_init_hook(env):
    setup(env)


def uninstall_hook(env):
    _logger.info("rpbm_pricing: retrait de la garde de la règle 8")
    env["sale.order.line"]._rpbm_rule8_uninstall()
