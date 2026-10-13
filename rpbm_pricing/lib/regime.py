"""Régime d'un dossier (assurance ou hors assurance), sans dépendance à Odoo."""

INSURANCE = "insurance"
PRIVATE = "private"
SELECTION = [(INSURANCE, "Assurance"), (PRIVATE, "Hors assurance")]
LABELS = dict(SELECTION)

# Noms normalisés (``rpbm_agent.models.legacy_fields.normalize``) des modèles de devis assurance.
INSURANCE_TEMPLATE_NAMES = frozenset({
    "pare brise v",
    "lunette arriere",
    "glace mobile",
    "glace fixe",
    "reglage adas (assurance)",
})


def dossier_regime(has_opportunity, has_insurer):
    """``None`` sans opportunité, ``INSURANCE`` si elle porte un assureur, sinon ``PRIVATE``."""
    if not has_opportunity:
        return None
    return INSURANCE if has_insurer else PRIVATE


def template_regime(normalized_name):
    """Régime d'un modèle de devis d'après son nom normalisé, ``None`` s'il ne se déduit pas."""
    name = normalized_name or ""
    if name in INSURANCE_TEMPLATE_NAMES:
        return INSURANCE
    if "hors assurance" in name:
        return PRIVATE
    return None


def warnings(template_regime, dossier_regime, has_xglass_labor):
    """Avertissements du devis : divergence modèle / dossier (P-05), main-d'œuvre X'Glass hors assurance (P-16)."""
    messages = []
    if template_regime and dossier_regime and template_regime != dossier_regime:
        messages.append("Le modèle de devis est « %s », le dossier est « %s »." % (
            LABELS[template_regime], LABELS[dossier_regime]))
    if dossier_regime == PRIVATE and has_xglass_labor:
        messages.append("Main-d'œuvre X'Glass proposée sur un dossier hors assurance : "
                        "vérifiez la grille hors assurance.")
    return messages
