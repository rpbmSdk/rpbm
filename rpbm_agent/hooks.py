import logging
import re

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
    # Les donnees vehicule vivent dans Fleet. Ces champs rendent cette source
    # exploitable dans CRM sans recreer les anciens modeles Studio de marque et
    # modele, qui ne portaient aucune relation fiable entre eux.
    {
        "model": "crm.lead",
        "name": "x_rpbm_vehicle_brand_id",
        "description": "Marque du véhicule",
        "ttype": "many2one",
        "relation": "fleet.vehicle.model.brand",
        "related": "x_studio_vehicle_id.model_id.brand_id",
        "store": True,
    },
    {
        "model": "crm.lead",
        "name": "x_rpbm_vehicle_model_id",
        "description": "Modèle du véhicule",
        "ttype": "many2one",
        "relation": "fleet.vehicle.model",
        "related": "x_studio_vehicle_id.model_id",
        "store": True,
    },
    {
        "model": "crm.lead",
        "name": "x_rpbm_vehicle_brand_name",
        "description": "Marque du véhicule",
        "ttype": "char",
        "related": "x_rpbm_vehicle_brand_id.name",
        "store": True,
    },
    {
        "model": "crm.lead",
        "name": "x_rpbm_vehicle_model_name",
        "description": "Modèle du véhicule",
        "ttype": "char",
        "related": "x_rpbm_vehicle_model_id.name",
        "store": True,
    },
    {
        "model": "crm.lead",
        "name": "x_rpbm_vehicle_vin",
        "description": "VIN du véhicule",
        "ttype": "char",
        "related": "x_studio_vehicle_id.vin_sn",
        "store": True,
    },
    {
        "model": "crm.lead",
        "name": "x_rpbm_vehicle_detail_model",
        "description": "Détail du modèle du véhicule",
        "ttype": "char",
        "related": "x_studio_vehicle_id.x_studio_detail_model",
        "store": True,
    },
    {
        "model": "crm.lead",
        "name": "x_rpbm_vehicle_fuel_type",
        "description": "Énergie moteur du véhicule",
        "ttype": "selection",
        "related": "x_studio_vehicle_id.fuel_type",
        "store": True,
    },
    {
        "model": "crm.lead",
        "name": "x_rpbm_vehicle_date_mec",
        "description": "Date de première MEC du véhicule",
        "ttype": "date",
        "related": "x_studio_vehicle_id.x_studio_date_mec",
        "store": True,
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
    *[
        {
            "model": "sale.order",
            "name": name,
            "description": description,
            "ttype": ttype,
            "relation": relation,
            "related": "opportunity_id.%s" % name,
            "store": True,
        }
        for name, description, ttype, relation in (
            ("x_rpbm_vehicle_brand_id", "Marque du véhicule", "many2one", "fleet.vehicle.model.brand"),
            ("x_rpbm_vehicle_model_id", "Modèle du véhicule", "many2one", "fleet.vehicle.model"),
            ("x_rpbm_vehicle_brand_name", "Marque du véhicule", "char", None),
            ("x_rpbm_vehicle_model_name", "Modèle du véhicule", "char", None),
            ("x_rpbm_vehicle_vin", "VIN du véhicule", "char", None),
            ("x_rpbm_vehicle_detail_model", "Détail du modèle du véhicule", "char", None),
            ("x_rpbm_vehicle_fuel_type", "Énergie moteur du véhicule", "selection", None),
            ("x_rpbm_vehicle_date_mec", "Date de première MEC du véhicule", "date", None),
        )
    ],
    {
        "model": "sale.order",
        "name": "x_rpbm_vsf_constructor_reference",
        "description": "Référence constructeur VSF",
        "ttype": "char",
        "related": "opportunity_id.x_studio_field_MNzfJ",
        "store": True,
    },
    {
        "model": "product.product",
        "name": "x_studio_reference_constructeur",
        "description": "R\u00e9f\u00e9rence constructeur",
        "ttype": "char",
    },
    {
        "model": "product.template",
        "name": "x_studio_eurocode",
        "description": "Eurocode",
        "ttype": "char",
    },
    {
        "model": "product.template",
        "name": "x_studio_largeur_mm",
        "description": "Largeur (mm)",
        "ttype": "float",
    },
    {
        "model": "product.template",
        "name": "x_studio_longueur_mm",
        "description": "Longueur (mm)",
        "ttype": "float",
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
            expected_relation = field_spec.get("relation") or False
            if (
                field.ttype != field_spec["ttype"]
                or (field.relation or False) != expected_relation
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


LEGACY_VEHICLE_REFERENCE_REPLACEMENTS = (
    ("x_studio_field_KyCjB.x_name", "x_rpbm_vehicle_brand_name"),
    ("x_studio_field_ZhaeY.x_name", "x_rpbm_vehicle_model_name"),
    ("x_studio_many2one_field_rP62C.x_name", "x_rpbm_vehicle_brand_name"),
    ("x_studio_many2one_field_DkgHx.x_name", "x_rpbm_vehicle_model_name"),
    ("x_studio_field_KyCjB", "x_rpbm_vehicle_brand_id"),
    ("x_studio_field_ZhaeY", "x_rpbm_vehicle_model_id"),
    ("x_studio_many2one_field_rP62C", "x_rpbm_vehicle_brand_id"),
    ("x_studio_many2one_field_DkgHx", "x_rpbm_vehicle_model_id"),
    ("x_studio_marque__1", "x_rpbm_vehicle_brand_name"),
    ("x_studio_modle_", "x_rpbm_vehicle_model_name"),
)


def _replace_legacy_vehicle_text(value):
    """Retourne une expression Studio/QWeb pointee vers les champs Fleet."""
    replacement = value or ""
    for old, new in LEGACY_VEHICLE_REFERENCE_REPLACEMENTS:
        replacement = re.sub(
            r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape(old),
            new,
            replacement,
        )
    return replacement


def _replacement_field_names(value):
    """Retourne les champs Fleet introduits par une expression migree."""
    return frozenset(re.findall(r"\bx_rpbm_[A-Za-z0-9_]+\b", value or ""))


def _assert_replacement_fields_are_registered(env, value):
    """Refuse une migration si elle introduit un champ que le module ne livre pas.

    Cette verification est volontairement independante du modele de la vue : les
    templates QWeb peuvent traverser plusieurs modeles (par exemple
    ``doc.sale_order_id.x_rpbm_*``). La validation XML d'Odoo reste la source de
    verite pour la chaine complete.
    """
    replacement_fields = _replacement_field_names(value)
    if not replacement_fields:
        return
    registered_fields = {
        field.name
        for field in env["ir.model.fields"].sudo().search([])
    }
    unknown_fields = sorted(replacement_fields - registered_fields)
    if unknown_fields:
        raise RuntimeError(
            "rpbm_agent: la migration introduit des champs non enregistres: %s"
            % ", ".join(unknown_fields)
        )


def _write_view_reference_replacement(env, record, field_name, original, replacement):
    """Ecrit une vue, en ignorant uniquement une invalidite deja presente.

    ``ir.ui.view.write`` valide l'architecture complete, y compris les
    personnalisations Studio qui ne sont pas gerees par ce module. Un savepoint
    permet de sonder cette validation sans rendre la transaction inutilisable.
    Si l'architecture originale echoue aussi, la vue est conservee telle quelle
    et l'upgrade peut continuer. En revanche, une architecture originale valide
    (ou une erreur mentionnant une de nos references) remonte au chargeur Odoo.
    """
    try:
        with env.cr.savepoint():
            record.write({field_name: replacement})
        return True
    except Exception as replacement_error:
        record.invalidate_recordset([field_name])
        if any(
            field_name in str(replacement_error)
            for field_name in _replacement_field_names(replacement)
        ):
            raise

        probe = "%s\n<!-- rpbm_agent validation probe -->" % original
        try:
            with env.cr.savepoint():
                record.write({field_name: probe})
        except Exception as original_error:
            record.invalidate_recordset([field_name])
            _logger.warning(
                "rpbm_agent: vue ir.ui.view %s ignoree: architecture deja "
                "invalide avant migration (%s: %s)",
                record.id,
                type(original_error).__name__,
                original_error,
            )
            return False

        record.invalidate_recordset([field_name])
        raise


def _replace_legacy_vehicle_references(env):
    """Remplace les references Studio connues, sans toucher aux donnees.

    Les champs historiques restent presents pour les anciens dossiers. Seules
    les expressions de vues, QWeb et courriels sont migrees vers les nouveaux
    champs Fleet ; l'operation est donc rejouable sans effet supplementaire.
    """
    legacy_names = [item[0] for item in LEGACY_VEHICLE_REFERENCE_REPLACEMENTS]
    models_and_fields = (("ir.ui.view", "arch_db"), ("mail.template", "body_html"))
    available_models = set(env.registry.models)
    for model_name, field_name in models_and_fields:
        if model_name not in available_models:
            _logger.info("rpbm_agent: %s indisponible, inventaire ignore", model_name)
            continue
        records = env[model_name].sudo().with_context(active_test=False).search(
            [(field_name, "ilike", legacy_names[0])]
        )
        for legacy_name in legacy_names[1:]:
            records |= env[model_name].sudo().with_context(active_test=False).search(
                [(field_name, "ilike", legacy_name)]
            )
        for record in records:
            original = getattr(record, field_name) or ""
            replacement = _replace_legacy_vehicle_text(original)
            if replacement != original:
                if model_name == "ir.ui.view":
                    _assert_replacement_fields_are_registered(env, replacement)
                    migrated = _write_view_reference_replacement(
                        env, record, field_name, original, replacement
                    )
                    if not migrated:
                        continue
                else:
                    record.write({field_name: replacement})
                _logger.info(
                    "rpbm_agent: %s %s (%s) migre vers les champs Fleet",
                    model_name,
                    record.id,
                    field_name,
                )
            elif any(legacy_name in original for legacy_name in legacy_names):
                _logger.warning(
                    "rpbm_agent: %s %s contient une reference non remplacee; "
                    "controle manuel requis",
                    model_name,
                    record.id,
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
