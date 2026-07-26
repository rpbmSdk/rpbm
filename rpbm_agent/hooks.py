import logging

_logger = logging.getLogger(__name__)

# Champs x_studio_* consommes par le widget/controller et manquants sur au
# moins une instance connue (voir docs/technique/champs/ pour le detail
# complet). Les champs sale.order lies a l'opportunite sont stockes afin de
# suivre la convention Studio existante de l'instance.
#
# Volontairement absent de cette liste : crm.lead.x_studio_base_eurocode — le
# widget cible le champ Studio deja existant x_studio_field_ORIyy (voir
# static/src/agent_widget_dialog_crm_lead.js), pas un nouveau champ disjoint
# qui dupliquerait la notion de "Base Eurocode" sur ce modele.
FIELDS_TO_ENSURE = [
    {
        "model": "fleet.vehicle",
        "name": "x_studio_detail_model",
        "description": "D\u00e9tail du mod\u00e8le",
        "ttype": "char",
    },
    {
        "model": "fleet.vehicle",
        "name": "x_studio_date_mec",
        "description": "Date de mise en circulation",
        "ttype": "date",
    },
    {
        "model": "crm.lead",
        "name": "x_studio_vehicle_id",
        "description": "V\u00e9hicule",
        "ttype": "many2one",
        "relation": "fleet.vehicle",
    },
    {
        "model": "crm.lead",
        "name": "x_studio_categorie_xglass",
        "description": "Cat\u00e9gorie X'Glass",
        "ttype": "char",
    },
    {
        "model": "sale.order",
        "name": "x_studio_vehicle_id",
        "description": "V\u00e9hicule",
        "ttype": "many2one",
        "relation": "fleet.vehicle",
        "related": "opportunity_id.x_studio_vehicle_id",
        "store": True,
    },
    {
        "model": "sale.order",
        "name": "x_studio_categorie_xglass",
        "description": "Cat\u00e9gorie X'Glass",
        "ttype": "char",
        "related": "opportunity_id.x_studio_categorie_xglass",
        "store": True,
    },
    {
        "model": "product.product",
        "name": "x_studio_reference_constructeur",
        "description": "R\u00e9f\u00e9rence constructeur",
        "ttype": "char",
    },
]


def _field_values(env, field_spec):
    vals = {
        "name": field_spec["name"],
        "model_id": env["ir.model"]._get_id(field_spec["model"]),
        "field_description": field_spec["description"],
        "ttype": field_spec["ttype"],
        "state": "manual",
    }
    for attribute in ("relation", "related", "store"):
        if attribute in field_spec:
            vals[attribute] = field_spec[attribute]
    return vals


def _related_field_values(field_spec):
    """Retourne les proprietes modifiables pour un champ related existant."""
    vals = {"field_description": field_spec["description"]}
    for attribute in ("relation", "related", "store"):
        if attribute in field_spec:
            vals[attribute] = field_spec[attribute]
    return vals


def _align_related_sale_order_fields(env):
    """Aligne les champs existants de sale.order sans les supprimer.

    Les vues, y compris les vues Studio, referencent ces champs pendant une
    migration. Les supprimer rendrait donc temporairement les vues invalides.
    Une valeur stockee dans un ancien champ independant bloque l'upgrade pour
    eviter qu'un changement de semantique ne l'ecrase.
    """
    Fields = env["ir.model.fields"].sudo().with_context(studio=True)
    related_specs = [
        spec
        for spec in FIELDS_TO_ENSURE
        if spec["model"] == "sale.order" and spec.get("related")
    ]
    for field_spec in related_specs:
        field = Fields.search(
            [("model", "=", field_spec["model"]), ("name", "=", field_spec["name"])],
            limit=1,
        )
        if field and field.related == field_spec["related"] and field.store:
            continue
        if field:
            if (
                field.ttype != field_spec["ttype"]
                or field.relation != field_spec.get("relation")
            ):
                raise RuntimeError(
                    "rpbm_agent: impossible d'aligner %s.%s : definition incompatible"
                    % (field_spec["model"], field_spec["name"])
                )
            if field.related and field.related != field_spec["related"]:
                raise RuntimeError(
                    "rpbm_agent: impossible d'aligner %s.%s : related existant incompatible"
                    % (field_spec["model"], field_spec["name"])
                )
            if not field.related:
                used_count = env[field_spec["model"]].with_context(active_test=False).search_count(
                    [(field_spec["name"], "!=", False)]
                )
                if used_count:
                    raise RuntimeError(
                        "rpbm_agent: impossible d'aligner %s.%s : %s valeur(s) existante(s)"
                        % (field_spec["model"], field_spec["name"], used_count)
                    )
            field.write(_related_field_values(field_spec))
        else:
            Fields.create(_field_values(env, field_spec))
        _logger.info(
            "rpbm_agent: %s.%s aligne comme related vers %s",
            field_spec["model"],
            field_spec["name"],
            field_spec["related"],
        )


def pre_init_hook(env):
    """Cree les champs x_studio_* manquants avant le chargement des vues.

    context={'studio': True} fait passer le champ cree par le mixin
    web_studio.studio_mixin (Enterprise) s'il est installe : celui-ci trace
    automatiquement le champ comme une customisation Studio (ir.model.data
    rattache au module studio_customization), exactement comme s'il avait ete
    cree a la main dans Studio — il survit donc a une desinstallation de ce
    module. Sans web_studio, ce contexte est ignore sans erreur.
    """
    Fields = env["ir.model.fields"].sudo().with_context(studio=True)

    for field_spec in FIELDS_TO_ENSURE:
        if Fields.search_count(
            [("model", "=", field_spec["model"]), ("name", "=", field_spec["name"])]
        ):
            _logger.info(
                "rpbm_agent: %s.%s deja present, ignore",
                field_spec["model"],
                field_spec["name"],
            )
            continue
        Fields.create(_field_values(env, field_spec))
        _logger.info(
            "rpbm_agent: %s.%s cree (pre_init_hook)",
            field_spec["model"],
            field_spec["name"],
        )
