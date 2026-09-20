"""Champs natifs ``rpbm_*`` : recopie des champs créés par l'ancien hook, backfill depuis les
champs Studio historiques, puis suppression des champs que le module avait lui-même créés.

Idempotent : chaque copie ne remplit que les valeurs natives encore vides, chaque suppression
n'a lieu que si le champ n'est plus référencé nulle part (vues, automatisations, filtres…).
"""
import logging

from odoo import SUPERUSER_ID, api
from odoo.tools.sql import column_exists

from odoo.addons.rpbm_agent.models.legacy_fields import (
    INTERVENTION_LOCATIONS,
    LEGACY_TO_FUEL,
    PART_TYPE_TO_LEGACY,
    NameIndex,
    referenced_elsewhere,
)

_logger = logging.getLogger(__name__)

FUEL_LEGACY_LABELS = {"Diesel": "diesel", "Essence": "gasoline", "Électrique": "electric", "Hybride": "full_hybrid"}
VIN_CLEANUP = r"regexp_replace({src}, '^\s*var\s*=\s*([A-HJ-NPR-Z0-9]{{17}})\s*;\s*$', '\1')"
INT_CAST = r"CASE WHEN {src} ~ '^\s*\d+\s*$' THEN trim({src})::integer END"
MONTH_YEAR = (
    r"CASE WHEN trim({src}) ~ '^(0[1-9]|1[0-2])/\d{{4}}$' THEN to_date(trim({src}), 'MM/YYYY')"
    r" WHEN trim({src}) ~ '^(0[1-9]|1[0-2])/\d{{2}}$' THEN to_date(trim({src}), 'MM/YY')"
    r" WHEN trim({src}) ~ '^(19|20)\d{{2}}$' THEN to_date(trim({src}), 'YYYY')"
    r" WHEN trim({src}) ~ '^\d{{2}}/(0[1-9]|1[0-2])/\d{{4}}$' THEN date_trunc('month', to_date(trim({src}), 'DD/MM/YYYY'))::date"
    r" END"
)

# (table, colonne source, colonne cible, expression, correspondance pour un CASE)
COPIES = [
    ("fleet_vehicle", "x_studio_detail_model", "rpbm_detail_model", None, None),
    ("fleet_vehicle", "x_studio_date_mec", "rpbm_first_registration_date", None, None),
    ("product_template", "x_studio_eurocode", "rpbm_eurocode", None, None),
    ("product_template", "x_studio_largeur_mm", "rpbm_width_mm", None, None),
    ("product_template", "x_studio_longueur_mm", "rpbm_length_mm", None, None),
    ("product_product", "x_studio_reference_constructeur", "rpbm_constructor_reference", None, None),
    ("crm_lead", "x_studio_categorie_xglass", "rpbm_xglass_category", None, None),
    ("crm_lead", "x_rpbm_xglass_piece_id", "rpbm_xglass_piece_id", None, None),
    ("crm_lead", "x_rpbm_piece_oe_id", "rpbm_piece_oe_id", None, None),
    ("crm_lead", "x_rpbm_piece_am_id", "rpbm_piece_am_id", None, None),
    ("sale_order_line", "x_rpbm_labor_operation_key", "rpbm_labor_operation_key", None, None),
    ("sale_order_line", "x_studio_prix_x_glass", "rpbm_xglass_price", None, None),
    # Champs Studio historiques de l'opportunité.
    ("crm_lead", "x_studio_field_NVioD", "rpbm_license_plate", None, None),
    ("crm_lead", "x_studio_field_PfJlB", "rpbm_vin", VIN_CLEANUP, None),
    ("crm_lead", "x_studio_field_i8fWl", "rpbm_vehicle_detail_model", None, None),
    ("crm_lead", "x_studio_field_ORIyy", "rpbm_eurocode_base", None, None),
    ("crm_lead", "x_studio_field_NwRik", "rpbm_eurocode", None, None),
    ("crm_lead", "x_studio_field_j8eh3", "rpbm_vsf_designation", None, None),
    ("crm_lead", "x_studio_field_MNzfJ", "rpbm_constructor_reference", None, None),
    ("crm_lead", "x_studio_field_BKtpw", "rpbm_vsf_stock", INT_CAST, None),
    ("crm_lead", "x_studio_field_Eh6Wd", "rpbm_first_registration_date", MONTH_YEAR, None),
    ("crm_lead", "x_studio_field_TAhpP", "rpbm_fuel_type", None, FUEL_LEGACY_LABELS),
    ("crm_lead", "x_studio_field_eENQz", "rpbm_part_type", None, {label: key for key, label in PART_TYPE_TO_LEGACY.items()}),
    ("crm_lead", "x_studio_lieu_intervention", "rpbm_intervention_location", None, {label: key for key, label in INTERVENTION_LOCATIONS}),
]

# Champs créés par le module (hook ou ancienne version), dépendants en premier.
MODULE_CREATED_FIELDS = (
    [("sale.order", "x_rpbm_vehicle_%s" % suffix) for suffix in (
        "brand_name", "model_name", "brand_id", "model_id", "vin", "detail_model", "fuel_type", "date_mec")]
    + [("crm.lead", "x_rpbm_vehicle_%s" % suffix) for suffix in (
        "brand_name", "model_name", "brand_id", "model_id", "vin", "detail_model", "fuel_type", "date_mec")]
    + [
        ("sale.order", "x_studio_vehicle_id"),
        ("sale.order", "x_studio_categorie_xglass"),
        ("sale.order", "x_rpbm_vsf_constructor_reference"),
        ("crm.lead", "x_studio_vehicle_id"),
        ("crm.lead", "x_studio_categorie_xglass"),
        ("fleet.vehicle", "x_studio_detail_model"),
        ("fleet.vehicle", "x_studio_date_mec"),
        ("product.template", "x_studio_eurocode"),
        ("product.template", "x_studio_largeur_mm"),
        ("product.template", "x_studio_longueur_mm"),
        ("product.product", "x_studio_reference_constructeur"),
    ]
)


def _copy_column(cr, table, src, dst, expression=None, case_map=None):
    if not (column_exists(cr, table, src) and column_exists(cr, table, dst)):
        _logger.info("rpbm_agent: %s.%s -> %s ignoré (colonne absente)", table, src, dst)
        return
    params = ()
    if case_map:
        expression = "CASE {src} " + " ".join(["WHEN %s THEN %s"] * len(case_map)) + " END"
        params = tuple(item for pair in case_map.items() for item in pair)
    # Les colonnes Studio portent des majuscules (x_studio_field_NVioD) : identifiants cites, sinon
    # Postgres les replie en minuscules (build 38336004 : column "x_studio_field_nviod" does not exist).
    src = f'"{src}"'
    expression = (expression or "{src}").format(src=src)
    cr.execute(
        f"UPDATE {table} SET {dst} = {expression} WHERE {dst} IS NULL AND {src} IS NOT NULL AND {src}::text <> ''",
        params,
    )
    _logger.info("rpbm_agent: %s.%s <- %s : %s ligne(s)", table, dst, src, cr.rowcount)


def _copy_vehicle_links(env):
    """Les 3 liens véhicule du hook passent par l'ORM : compute des dérivés et synchronisation."""
    if not column_exists(env.cr, "crm_lead", "x_studio_vehicle_id"):
        return
    env.cr.execute(
        "SELECT id, x_studio_vehicle_id FROM crm_lead WHERE x_studio_vehicle_id IS NOT NULL AND rpbm_vehicle_id IS NULL"
    )
    for lead_id, vehicle_id in env.cr.fetchall():
        env["crm.lead"].browse(lead_id).write({"rpbm_vehicle_id": vehicle_id})
    _logger.info("rpbm_agent: liens véhicule recopiés")


def _backfill_brand_model(env):
    """Marque/modèle natifs depuis les référentiels Studio, par groupe (marque, modèle)."""
    lead_fields = env["crm.lead"]._fields
    studio_brand, studio_model = "x_studio_field_KyCjB", "x_studio_field_ZhaeY"
    if studio_brand not in lead_fields or studio_model not in lead_fields:
        _logger.info("rpbm_agent: référentiels Studio marque/modèle absents, backfill ignoré")
        return
    brand_table = env[lead_fields[studio_brand].comodel_name]._table
    model_table = env[lead_fields[studio_model].comodel_name]._table
    env.cr.execute(f"""
        SELECT l.id, b.x_name, m.x_name
        FROM crm_lead l
        LEFT JOIN {brand_table} b ON b.id = l."{studio_brand}"
        LEFT JOIN {model_table} m ON m.id = l."{studio_model}"
        WHERE (l."{studio_brand}" IS NOT NULL OR l."{studio_model}" IS NOT NULL)
          AND (l.rpbm_vehicle_brand_id IS NULL OR l.rpbm_vehicle_model_id IS NULL)
    """)
    groups = {}
    for lead_id, brand_name, model_name in env.cr.fetchall():
        groups.setdefault((brand_name or "", model_name or ""), []).append(lead_id)

    brands = NameIndex(env, "fleet.vehicle.model.brand", "name")
    models_by_brand = {}
    for (brand_name, model_name), lead_ids in groups.items():
        brand_id = brands.get_or_create(brand_name)
        model_id = False
        if brand_id and model_name:
            if brand_id not in models_by_brand:
                models_by_brand[brand_id] = NameIndex(env, "fleet.vehicle.model", "name", [("brand_id", "=", brand_id)])
            model_id = models_by_brand[brand_id].get_or_create(model_name, {"brand_id": brand_id})
        env.cr.execute(
            "UPDATE crm_lead SET rpbm_vehicle_brand_id = COALESCE(rpbm_vehicle_brand_id, %s), "
            "rpbm_vehicle_model_id = COALESCE(rpbm_vehicle_model_id, %s) WHERE id IN %s",
            (brand_id or None, model_id or None, tuple(lead_ids)),
        )
    _logger.info("rpbm_agent: marque/modèle natifs renseignés pour %s groupe(s)", len(groups))


def _refresh_mirrors(env):
    env.cr.execute("""
        UPDATE sale_order so SET
            rpbm_vehicle_id = l.rpbm_vehicle_id,
            rpbm_vehicle_brand_id = l.rpbm_vehicle_brand_id,
            rpbm_vehicle_model_id = l.rpbm_vehicle_model_id,
            rpbm_license_plate = l.rpbm_license_plate
        FROM crm_lead l
        WHERE so.opportunity_id = l.id AND (
            so.rpbm_vehicle_id IS DISTINCT FROM l.rpbm_vehicle_id
            OR so.rpbm_vehicle_brand_id IS DISTINCT FROM l.rpbm_vehicle_brand_id
            OR so.rpbm_vehicle_model_id IS DISTINCT FROM l.rpbm_vehicle_model_id
            OR so.rpbm_license_plate IS DISTINCT FROM l.rpbm_license_plate)
    """)
    _logger.info("rpbm_agent: miroirs sale.order rafraîchis : %s ligne(s)", env.cr.rowcount)
    if column_exists(env.cr, "stock_picking", "sale_id"):
        env.cr.execute("""
            UPDATE stock_picking p SET rpbm_vehicle_id = so.rpbm_vehicle_id
            FROM sale_order so
            WHERE p.sale_id = so.id AND p.rpbm_vehicle_id IS DISTINCT FROM so.rpbm_vehicle_id
        """)
    env.invalidate_all()
    moves = env["account.move"].search([("invoice_line_ids.sale_line_ids.order_id.rpbm_vehicle_id", "!=", False)])
    if moves:
        env.add_to_compute(env["account.move"]._fields["rpbm_vehicle_id"], moves)
        env.flush_all()


def _drop_module_created_fields(env):
    Fields = env["ir.model.fields"].sudo()
    pending = list(MODULE_CREATED_FIELDS)
    for _ in range(len(pending)):  # plusieurs passes : un champ ne référencé que par un autre de la liste tombe à la passe suivante
        kept = []
        for model_name, field_name in pending:
            field = Fields.search([("model", "=", model_name), ("name", "=", field_name), ("state", "=", "manual")], limit=1)
            if not field:
                continue
            references = referenced_elsewhere(env, model_name, field_name)
            if references:
                kept.append((model_name, field_name, references))
                continue
            try:
                with env.cr.savepoint():
                    field.unlink()
                _logger.info("rpbm_agent: champ %s.%s supprimé", model_name, field_name)
            except Exception as error:  # noqa: BLE001 - la migration continue, le champ est signalé
                _logger.warning("rpbm_agent: %s.%s non supprimé : %s", model_name, field_name, error)
        if len(kept) == len(pending):
            break
        pending = [(model_name, field_name) for model_name, field_name, _ in kept]
    for model_name, field_name, references in kept:
        _logger.warning("rpbm_agent: %s.%s conservé, encore référencé par %s", model_name, field_name, references)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for table, src, dst, expression, case_map in COPIES:
        _copy_column(cr, table, src, dst, expression, case_map)
    env.invalidate_all()
    _copy_vehicle_links(env)
    _backfill_brand_model(env)
    env.flush_all()
    _refresh_mirrors(env)
    _drop_module_created_fields(env)
