import logging

from odoo import api, fields, models

from odoo.addons.rpbm_agent.models.legacy_fields import normalize

from ..lib import regime

_logger = logging.getLogger(__name__)


class SaleOrderTemplate(models.Model):
    _inherit = "sale.order.template"

    # Relais seulement : le régime qui fait foi est celui du dossier (sale.order.rpbm_regime).
    rpbm_regime = fields.Selection(regime.SELECTION, "Régime")

    @api.model
    def _rpbm_template_regime_setup(self):
        """Classe par leur nom les modèles sans régime (archivés compris) ; une valeur posée est respectée."""
        templates = self.sudo().with_context(active_test=False).search([("rpbm_regime", "=", False)])
        classified = 0
        for template in templates:
            value = regime.template_regime(normalize(template.name))
            if value:
                template.rpbm_regime = value
                classified += 1
        _logger.info("rpbm_pricing: %s modèle(s) de devis classé(s) sur %s sans régime", classified, len(templates))
        return classified
