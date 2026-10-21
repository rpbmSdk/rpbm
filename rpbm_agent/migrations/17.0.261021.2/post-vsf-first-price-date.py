"""Premier tarif VSF de chaque article sans date de début (prix d'achat à 0 €, PO00025).

Une demande de prix datée avant ce tarif ne le trouvait pas à la fusion d'un besoin ou au
changement de quantité (purchase_stock stock_rule.py:251, purchase purchase_order_line.py:326).
Idempotent : seule la ligne VSF la plus ancienne d'un article est visée, et seulement si aucune
autre ligne VSF de l'article n'a déjà une date vide ou plus ancienne. SQL seulement : ni
``write_date`` ni automatisation ; les lignes de commande existantes ne sont pas recalculées.
"""
import logging

from odoo import SUPERUSER_ID, api
from odoo.exceptions import UserError

from odoo.addons.rpbm_agent.controllers.vsf_config import get_vsf_partner_id

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    try:
        partner_id = get_vsf_partner_id(api.Environment(cr, SUPERUSER_ID, {}))
    except UserError as error:  # base sans fournisseur VSF : rien à reprendre, la mise à jour continue
        _logger.warning("rpbm_agent: reprise du premier tarif VSF ignorée : %s", error)
        return
    cr.execute(
        """
        UPDATE product_supplierinfo s SET date_start = NULL
        WHERE s.partner_id = %s AND s.date_start IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM product_supplierinfo o
              WHERE o.partner_id = s.partner_id AND o.product_tmpl_id = s.product_tmpl_id AND o.id <> s.id
                AND (o.date_start IS NULL OR o.date_start < s.date_start
                     OR (o.date_start = s.date_start AND o.id < s.id)))
        RETURNING s.id
        """,
        (partner_id,),
    )
    ids = sorted(row[0] for row in cr.fetchall())
    _logger.info("rpbm_agent: premier tarif VSF (partenaire %s) sans date de début : %s ligne(s), ex. ids %s",
                 partner_id, len(ids), ids[:20])
