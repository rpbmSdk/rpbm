"""Lecture des paramètres système ``rpbm_pricing.*``.

Une valeur absente ou invalide donne le défaut (avec un avertissement si elle est invalide), jamais
une exception : ces lectures tournent aussi dans l'automatisation Studio de la règle 8.
"""
import logging

_logger = logging.getLogger(__name__)

# Clés et valeurs de repli, identiques aux données noupdate (docs/parametres.md).
INSURANCE_COEFFICIENT = ("rpbm_pricing.insurance_coefficient", 1.5)
PRICE_ROUNDING = ("rpbm_pricing.price_rounding", 0.0)
RULE8_INSURANCE_ONLY = ("rpbm_pricing.rule8_insurance_only", False)
COLISAGE_MIN_PIECES = ("rpbm_pricing.colisage_min_pieces", 500.0)
COLISAGE_MIN_FEES = ("rpbm_pricing.colisage_min_fees", 629.0)
COLISAGE_BOAT_MARCHS = ("rpbm_pricing.colisage_boat_marchs", "751102,795714,797088,855133,916930")

_TRUE = {"1", "true", "yes", "oui", "vrai"}
_FALSE = {"0", "false", "no", "non", "faux", ""}


def _raw(env, key):
    return env["ir.config_parameter"].sudo().get_param(key)


def get_str(env, key, default=""):
    value = _raw(env, key)
    return default if value is False or value is None else value


def get_float(env, key, default=0.0):
    value = _raw(env, key)
    if value is False or value is None:
        return default
    try:
        return float(str(value).strip().replace(",", "."))
    except ValueError:
        _logger.warning("rpbm_pricing: paramètre %s invalide (%r), défaut %r retenu", key, value, default)
        return default


def get_bool(env, key, default=False):
    value = _raw(env, key)
    if value is False or value is None:
        return default
    text = str(value).strip().casefold()
    if text in _TRUE:
        return True
    if text in _FALSE:
        return False
    _logger.warning("rpbm_pricing: paramètre %s invalide (%r), défaut %r retenu", key, value, default)
    return default
