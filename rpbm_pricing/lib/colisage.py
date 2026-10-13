"""Colisage VSF (un envoi, la « caisse » du client), sans dépendance à Odoo.

Méthode du classeur corrigé (docs/colisage.md) : pièces = compte 60710000 ou libellé PIECE, frais = le
reste, Pack VIN exclu, avoirs déduits ; coefficient = (pièces + frais) / pièces.
"""
import re

MARCH = "march"
COMPL = "compl"
PACK_VIN = "pack_vin"

PIECE = "piece"
FEE = "fee"
EXCLUDED = "excluded"

PIECE_ACCOUNT_PREFIX = "60710000"

# « 941797 - MARCH », « 916930 - MARCH BATEAU », « 931052 - COMPL MARITIME 2/2 », « 942260 - PACK VIN ».
_BILL_REF = re.compile(r"^\s*(\d{6})\s*-\s*(MARCH|COMPL|PACK VIN)\b", re.IGNORECASE)
_KINDS = {"MARCH": MARCH, "COMPL": COMPL, "PACK VIN": PACK_VIN}
# « FRAIS TRANSPORT 935879 DU 300726 », « COMP AERIEN FAC749977 DU 020125 », « F759807 DU130225 ».
_COMPL_TARGET = re.compile(r"(?<!\d)(\d{6})\s*DU(?![A-Z])", re.IGNORECASE)
# Les factures VSF disent « MARITIME » (COMPL) ou « BATEAU » (MARCH) pour un envoi par bateau.
_BOAT_WORDS = ("MARITIME", "BATEAU")


def parse_bill_ref(ref):
    """``(MARCH|COMPL|PACK_VIN, numéro)`` d'après la référence de la facture, sinon ``(None, None)``."""
    match = _BILL_REF.match(ref or "")
    if not match:
        return None, None
    return _KINDS[match.group(2).upper()], match.group(1)


def compl_target(label):
    """Numéro de la MARCH cité par un libellé de COMPL (6 chiffres suivis de « DU »), sinon ``None``."""
    match = _COMPL_TARGET.search(label or "")
    return match.group(1) if match else None


def classify_line(account_code, label):
    """``EXCLUDED`` (Pack VIN), ``PIECE`` (compte 60710000 ou libellé PIECE) ou ``FEE``."""
    text = (label or "").upper()
    if "PACK VIN" in text:
        return EXCLUDED
    if (account_code or "").startswith(PIECE_ACCOUNT_PREFIX) or "PIECE" in text:
        return PIECE
    return FEE


def totals(lines):
    """``(pièces, frais)`` de lignes ``(compte, libellé, montant HT, avoir)`` ; un avoir est déduit."""
    pieces = fees = 0.0
    for account_code, label, amount, refund in lines:
        kind = classify_line(account_code, label)
        if kind == EXCLUDED:
            continue
        signed = -amount if refund else amount
        if kind == PIECE:
            pieces += signed
        else:
            fees += signed
    return pieces, fees


def coefficient(pieces, fees):
    """Coefficient d'approche ``(pièces + frais) / pièces`` ; 0 sans pièces."""
    return (pieces + fees) / pieces if pieces > 0 else 0.0


def is_retained(pieces, fees, min_pieces, min_fees):
    """Colisage retenu pour la mesure : pièces et frais strictement au-dessus des seuils."""
    return pieces > min_pieces and fees > min_fees


def is_boat(number, texts, boat_numbers):
    """Envoi par bateau : numéro listé, ou « MARITIME » / « BATEAU » dans la référence ou un libellé."""
    if number in boat_numbers:
        return True
    return any(word in (text or "").upper() for text in texts for word in _BOAT_WORDS)
