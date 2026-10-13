"""Champs et enregistrements Studio historiques utilisés par le module.

Seul fichier de ``rpbm_pricing`` où un nom ``x_studio_*`` apparaît ; tout accès est gardé par
``name in model._fields`` : le module s'installe sur une base sans Studio.
"""

# crm.lead « Assurance (Simplifié) », many2one vers x_rpbm_assurances_simples.
INSURER_FIELD = "x_studio_field_ZiY2J"
# sale.order.line « Prix X'Glass », déclencheur de la règle 8 (recopié dans rpbm_xglass_price).
XGLASS_STUDIO_FIELD = "x_studio_prix_x_glass"

# Règle 8 « Tarif x glass » : automatisation 8 et action 1510 en préprod (lu le 2026-10-12).
RULE8_AUTOMATION_XMLID = "studio_customization.tarif_x_glass_a9a7386d-132e-4425-8818-e5d27b64af6d"
RULE8_ACTION_XMLID = "studio_customization.tarif_x_glass_a23325bd-2c11-4089-b3e2-bf1850d634be"
RULE8_ORIGINAL_VALUE = "record.x_studio_prix_x_glass*1.5"
# Sans le code du module, ``rpbm_rule8_price`` sort de ``_fields`` et l'action retombe sur l'original.
RULE8_GUARD_VALUE = (
    "record.rpbm_rule8_price if 'rpbm_rule8_price' in record._fields "
    "else record.x_studio_prix_x_glass*1.5"
)


def lead_has_insurer(lead):
    """Vrai si l'opportunité porte un assureur ; toujours faux sans le champ Studio."""
    return bool(lead) and INSURER_FIELD in lead._fields and bool(lead[INSURER_FIELD])
