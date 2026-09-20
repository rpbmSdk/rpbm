"""Paramètres système VSF partagés par le widget et la synchronisation produit."""

from odoo import _
from odoo.exceptions import UserError

from . import vsf

VSF_PARTNER_PARAM = "rpbm_agent.vsf_partner_id"
VSF_DISCOUNT_PARAM = "rpbm_agent.vsf_discount"
DEFAULT_VSF_PARTNER_ID = 5708


def get_vsf_discount(env):
    """Retourne la remise RPBM configurée, avec le défaut historique à 20 %."""
    raw_value = env['ir.config_parameter'].sudo().get_param(
        VSF_DISCOUNT_PARAM, str(vsf.DEFAULT_RPBM_DISCOUNT)
    )
    try:
        discount = float(raw_value)
    except (TypeError, ValueError) as error:
        raise UserError(_("Le paramètre %s doit être un nombre compris entre 0 et 1.") % VSF_DISCOUNT_PARAM) from error
    if not 0 <= discount <= 1:
        raise UserError(_("Le paramètre %s doit être compris entre 0 et 1.") % VSF_DISCOUNT_PARAM)
    return discount


def get_vsf_partner_id(env):
    """Retourne le fournisseur VSF configuré et vérifie qu'il existe."""
    raw_value = env['ir.config_parameter'].sudo().get_param(
        VSF_PARTNER_PARAM, str(DEFAULT_VSF_PARTNER_ID)
    )
    try:
        partner_id = int(raw_value)
    except (TypeError, ValueError) as error:
        raise UserError(_("Le paramètre %s doit contenir l'identifiant numérique d'un partenaire.") % VSF_PARTNER_PARAM) from error
    if not env['res.partner'].browse(partner_id).exists():
        raise UserError(_("Le fournisseur VSF configuré (%s) n'existe pas.") % partner_id)
    return partner_id
