"""Garde de l'automatisation Studio « Tarif x glass » (règle 8, IMP-2) : docs/regle-8.md.

L'action de la règle 8 reçoit ``legacy_fields.RULE8_GUARD_VALUE`` : elle écrit ``rpbm_rule8_price``
tant que ce module est chargé, la formule d'origine sinon. Seule cette valeur Studio est modifiée ;
le domaine et le déclencheur de l'automatisation restent ceux de Studio.
"""
import logging

from odoo import api, fields, models
from odoo.tools import float_round

from ..lib import regime
from . import params
from .legacy_fields import (
    RULE8_ACTION_XMLID,
    RULE8_AUTOMATION_XMLID,
    RULE8_GUARD_VALUE,
    RULE8_ORIGINAL_VALUE,
)

_logger = logging.getLogger(__name__)

# Instantané de la valeur d'origine, écrit par la mise en place (pas par les données).
RULE8_ORIGINAL_PARAM = "rpbm_pricing.rule8_original_value"
# Catégories non pièces (P-09), enfants compris : 19 « Consommable », 20 « Film solaire », 22 « Services ».
RULE8_EXCLUDED_CATEGORY_XMLIDS = (
    "__import__.rpbm_categ_consommable",
    "__import__.rpbm_categ_film_solaire",
    "__import__.rpbm_categ_services",
)


def _squash(text):
    return "".join(str(text or "").split())


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # Témoin lu par l'action de la règle 8 (``in record._fields``) : ne pas renommer.
    rpbm_rule8_price = fields.Float(
        "Prix de la règle 8", digits="Product Price", compute="_compute_rpbm_rule8_price")

    @api.model
    def _rpbm_rule8_excluded_categories(self):
        roots = self.env["product.category"]
        for xmlid in RULE8_EXCLUDED_CATEGORY_XMLIDS:
            category = self.env.ref(xmlid, raise_if_not_found=False)
            if category:
                roots |= category
            else:
                _logger.debug("rpbm_pricing: catégorie %s absente, ignorée par la règle 8", xmlid)
        return roots and roots.search([("id", "child_of", roots.ids)])

    def _rpbm_rule8_value(self, excluded=None):
        """Barème × coefficient, ou ``None`` si la règle 8 ne doit pas toucher le prix de la ligne."""
        self.ensure_one()
        product = self.product_id
        if not product or not self.rpbm_xglass_price or product.type == "service":
            return None
        if excluded is None:
            excluded = self._rpbm_rule8_excluded_categories()
        if product.categ_id in excluded:
            return None
        if (params.get_bool(self.env, *params.RULE8_INSURANCE_ONLY) and self.order_id
                and self.order_id._rpbm_dossier_regime() == regime.PRIVATE):
            return None
        value = self.rpbm_xglass_price * params.get_float(self.env, *params.INSURANCE_COEFFICIENT)
        rounding = params.get_float(self.env, *params.PRICE_ROUNDING)
        return float_round(value, precision_rounding=rounding) if rounding > 0 else value

    @api.depends("rpbm_xglass_price", "price_unit", "product_id", "order_id.opportunity_id")
    def _compute_rpbm_rule8_price(self):
        excluded = self._rpbm_rule8_excluded_categories()
        for line in self:
            value = line._rpbm_rule8_value(excluded)
            line.rpbm_rule8_price = line.price_unit if value is None else value

    @api.model
    def _rpbm_rule8_action(self):
        """Action de la règle 8 : par xmlid, sinon seule action ``price_unit`` à la valeur d'origine ou garde."""
        action = self.env.ref(RULE8_ACTION_XMLID, raise_if_not_found=False)
        if action:
            return action.sudo()
        actions = self.env["ir.actions.server"].sudo().search([
            ("model_name", "=", "sale.order.line"),
            ("state", "=", "object_write"),
            ("update_field_id.name", "=", "price_unit"),
            ("value", "in", [RULE8_ORIGINAL_VALUE, RULE8_GUARD_VALUE]),
        ])
        if len(actions) > 1:
            _logger.warning("rpbm_pricing: %s actions candidates pour la règle 8 (%s), aucune retenue",
                            len(actions), actions.ids)
            return False
        return actions or False

    @api.model
    def _rpbm_rule8_automation(self, action=None):
        """Automatisation qui porte l'action de la règle 8 ; ``False`` sans ``base_automation``."""
        if "base.automation" not in self.env:
            return False
        automation = self.env.ref(RULE8_AUTOMATION_XMLID, raise_if_not_found=False)
        if automation:
            return automation.sudo()
        action = action or self._rpbm_rule8_action()
        if not action:
            return False
        automations = self.env["base.automation"].sudo().with_context(active_test=False).search([
            ("action_server_ids", "in", action.ids)])
        if len(automations) > 1:
            _logger.warning("rpbm_pricing: %s automatisations portent l'action %s, aucune retenue",
                            len(automations), action.id)
            return False
        return automations or False

    @api.model
    def _rpbm_rule8_guard_active(self):
        """Vrai si l'automatisation de la règle 8 est active et que son action porte la garde."""
        action = self._rpbm_rule8_action()
        automation = action and self._rpbm_rule8_automation(action)
        return bool(automation and automation.active and action.value == RULE8_GUARD_VALUE)

    @api.model
    def _rpbm_rule8_install(self, action=None):
        """Pose la garde ; une valeur autre que l'originale (espaces ignorés) n'est jamais écrasée."""
        action = (action or self._rpbm_rule8_action() or self.env["ir.actions.server"]).sudo()
        if not action:
            _logger.info("rpbm_pricing: action de la règle 8 introuvable, garde non posée")
            return False
        if action.value == RULE8_GUARD_VALUE:
            return True
        if _squash(action.value) != _squash(RULE8_ORIGINAL_VALUE):
            _logger.warning("rpbm_pricing: valeur inattendue de l'action %s (%r), garde non posée",
                            action.id, action.value)
            return False
        self.env["ir.config_parameter"].sudo().set_param(RULE8_ORIGINAL_PARAM, action.value)
        # Le nom est réécrit tel quel : sinon base_automation le recalcule depuis la valeur.
        action.write({"value": RULE8_GUARD_VALUE, "name": action.name})
        _logger.info("rpbm_pricing: garde de la règle 8 posée sur l'action %s", action.id)
        return True

    @api.model
    def _rpbm_rule8_uninstall(self, action=None):
        """Restaure la valeur sauvegardée (à défaut l'originale) si l'action porte la garde."""
        action = (action or self._rpbm_rule8_action() or self.env["ir.actions.server"]).sudo()
        if not action or action.value != RULE8_GUARD_VALUE:
            return False
        original = params.get_str(self.env, RULE8_ORIGINAL_PARAM) or RULE8_ORIGINAL_VALUE
        action.write({"value": original, "name": action.name})
        _logger.info("rpbm_pricing: règle 8 d'origine restaurée sur l'action %s", action.id)
        return True

    def _compute_price_unit(self):
        # La règle 8 ne repasse qu'au changement du barème : sans cette surcharge, une modification de
        # quantité ramènerait la ligne au list_price. Les lignes facturées restent au natif (inchangées).
        guarded = self.browse()
        if self and self._rpbm_rule8_guard_active():
            excluded = self._rpbm_rule8_excluded_categories()
            for line in self - self._lines_without_price_recomputation():
                if line.qty_invoiced > 0:
                    continue
                value = line._rpbm_rule8_value(excluded)
                if value is not None:
                    line.price_unit = value
                    guarded |= line
        super(SaleOrderLine, self - guarded)._compute_price_unit()
