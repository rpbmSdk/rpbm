"""Donne Achats (manager) et Inventaire aux acheteurs (docs/metier/roles-achats.md). Idempotent."""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

# ponytail: logins en dur, à passer en paramètre si la liste d'acheteurs bouge souvent
BUYERS = ("rpbm003@gmail.com", "rpbm004@gmail.com")
GROUPS = ("purchase.group_purchase_manager", "stock.group_stock_user")


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    groups = [g for g in (env.ref(x, raise_if_not_found=False) for x in GROUPS) if g]
    if len(groups) < len(GROUPS):
        _logger.warning("rpbm_agent roles achats : groupe absent (module purchase installé ?)")
    users = env["res.users"].with_context(active_test=False).search([("login", "in", BUYERS)])
    users.write({"groups_id": [(4, g.id) for g in groups]})
    missing = set(BUYERS) - set(users.mapped("login"))
    _logger.info("rpbm_agent roles achats : %s mis à jour, introuvables : %s", users.mapped("login"), sorted(missing))
