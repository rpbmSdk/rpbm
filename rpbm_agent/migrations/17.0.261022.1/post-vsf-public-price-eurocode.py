"""Tarifs VSF au prix public + remise, eurocode en référence interne (17.0.261022.1).

(a) SQL : une ligne VSF à remise 0 dont le prix vaut exactement le net ``round(list_price × (1 − remise), 2)``
passe à (``list_price``, remise en %) ; le net calculé par Odoo bouge d'au plus 0,005 €. Les autres lignes VSF
à remise 0 (rapport différent, prix nul) ne sont pas touchées, seulement journalisées : la synchronisation les
historisera au prochain ajout au devis. Les lignes d'achat existantes ne sont pas recalculées (décision du
2026-10-22). Idempotent : une ligne convertie a une remise non nulle.
(b) ORM : ``default_code`` = eurocode pour les variantes dont la référence interne est encore la référence
constructeur (articles créés par le widget avant cette version). ORM et pas SQL : ``default_code`` du modèle
est calculé et stocké depuis la variante.
"""
import logging

from odoo import SUPERUSER_ID, api
from odoo.exceptions import UserError

from odoo.addons.rpbm_agent.controllers.vsf_config import get_vsf_discount, get_vsf_partner_id

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        partner_id = get_vsf_partner_id(env)
        fraction = get_vsf_discount(env)
    except UserError as error:  # base sans fournisseur VSF ou paramètre invalide : la mise à jour continue
        _logger.warning("rpbm_agent: reprise prix public VSF / eurocode ignorée : %s", error)
        return
    percent = round(fraction * 100, 2)
    cr.execute(
        """
        UPDATE product_supplierinfo s SET price = t.list_price, discount = %(percent)s
        FROM product_template t
        WHERE t.id = s.product_tmpl_id AND s.partner_id = %(partner)s
          AND COALESCE(s.discount, 0) = 0 AND t.list_price > 0
          AND s.price = ROUND(t.list_price * (1 - %(fraction)s::numeric), 2)
        RETURNING s.id
        """,
        {"partner": partner_id, "percent": percent, "fraction": str(fraction)},
    )
    converted = sorted(row[0] for row in cr.fetchall())
    cr.execute(
        "SELECT id FROM product_supplierinfo WHERE partner_id = %s AND COALESCE(discount, 0) = 0 ORDER BY id",
        (partner_id,),
    )
    skipped = [row[0] for row in cr.fetchall()]
    _logger.info("rpbm_agent: tarifs VSF (partenaire %s) passés au prix public + %s %% : %s ligne(s), ex. ids %s",
                 partner_id, percent, len(converted), converted[:20])
    _logger.info("rpbm_agent: tarifs VSF laissés au net (remise 0, net différent) : %s ligne(s), ids %s",
                 len(skipped), skipped)

    products = env["product.product"].with_context(active_test=False).search(
        [("rpbm_constructor_reference", "!=", False), ("product_tmpl_id.rpbm_eurocode", "!=", False)]
    ).filtered(lambda product: product.product_tmpl_id.rpbm_eurocode  # '' passe le domaine != False
               and product.default_code == product.rpbm_constructor_reference)
    for product in products:
        product.default_code = product.product_tmpl_id.rpbm_eurocode
    _logger.info("rpbm_agent: référence interne remplacée par l'eurocode : %s article(s), ids %s",
                 len(products), products.ids)
