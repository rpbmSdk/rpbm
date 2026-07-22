import logging

_logger = logging.getLogger(__name__)

# (modèle, nom du champ, description, ttype, relation)
# Champs x_studio_* consommés par le widget/controller et manquants sur au moins
# une instance connue (voir docs/technique/champs/ pour le détail complet).
#
# Volontairement absent de cette liste : crm.lead.x_studio_base_eurocode — le
# widget cible le champ Studio déjà existant x_studio_field_ORIyy (voir
# static/src/agent_widget_dialog_crm_lead.js), pas un nouveau champ disjoint
# qui dupliquerait la notion de "Base Eurocode" sur ce modèle.
FIELDS_TO_ENSURE = [
    ("fleet.vehicle", "x_studio_detail_model", "Détail du modèle", "char", None),
    ("fleet.vehicle", "x_studio_date_mec", "Date de mise en circulation", "date", None),
    ("crm.lead", "x_studio_vehicle_id", "Véhicule", "many2one", "fleet.vehicle"),
    ("crm.lead", "x_studio_categorie_xglass", "Catégorie X'Glass", "char", None),
    ("sale.order", "x_studio_vehicle_id", "Véhicule", "many2one", "fleet.vehicle"),
    ("sale.order", "x_studio_categorie_xglass", "Catégorie X'Glass", "char", None),
    ("product.product", "x_studio_reference_constructeur", "Référence constructeur", "char", None),
]


def pre_init_hook(env):
    """Crée les champs x_studio_* manquants avant le chargement des vues du
    module, qui les référencent (voir docs/technique/configuration.md).

    context={'studio': True} fait passer le champ créé par le mixin
    web_studio.studio_mixin (Enterprise) s'il est installé : celui-ci trace
    automatiquement le champ comme une customisation Studio (ir.model.data
    rattaché au module studio_customization), exactement comme s'il avait été
    créé à la main dans Studio — il survit donc à une désinstallation de ce
    module. Sans web_studio, ce contexte est ignoré sans erreur.
    """
    Fields = env["ir.model.fields"].sudo().with_context(studio=True)
    IrModel = env["ir.model"].sudo()

    for model_name, field_name, description, ttype, relation in FIELDS_TO_ENSURE:
        if Fields.search_count([("model", "=", model_name), ("name", "=", field_name)]):
            _logger.info("rpbm_agent: %s.%s déjà présent, ignoré", model_name, field_name)
            continue

        vals = {
            "name": field_name,
            "model_id": IrModel._get_id(model_name),
            "field_description": description,
            "ttype": ttype,
            "state": "manual",
        }
        if relation:
            vals["relation"] = relation

        Fields.create(vals)
        _logger.info("rpbm_agent: %s.%s créé (pre_init_hook)", model_name, field_name)
