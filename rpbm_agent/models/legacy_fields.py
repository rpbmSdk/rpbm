"""Correspondance entre les champs natifs ``rpbm_*`` et les champs Studio historiques.

Seul endroit du module où un nom ``x_studio_*`` apparaît. Chaque accès est gardé par
``name in model._fields`` : le module s'installe et fonctionne sur une base où ces champs
n'existent plus. Pendant la transition, le mixin recopie chaque écriture native vers le champ
Studio (les automatisations et calculs Studio continuent de tourner) et, inversement, une
saisie Studio seule met à jour le champ natif (les équipes gardent leurs vues).
"""
import logging
import re
import unicodedata
from datetime import date, datetime

from odoo import api, models

_logger = logging.getLogger(__name__)

PART_TYPES = [
    ("windshield", "Pare-brise"),
    ("rear_window", "Lunette arrière"),
    ("side_window", "Glace latérale"),
    ("other", "Autre"),
]
# Valeurs de la sélection Studio « Pièce concernée » (pilote la cascade de prix Studio).
PART_TYPE_TO_LEGACY = {
    "windshield": "Pare-Brise",
    "rear_window": "Lunette arrière",
    "side_window": "Glace Latérale",
    "other": "Autre...",
}
INTERVENTION_LOCATIONS = [
    ("galleria", "GALLERIA"),
    ("genipa", "GENIPA"),
    ("domicile", "DOMICILE"),
    ("lavage_place_armes", "LAVAGE PLACE D'ARMES"),
    ("lavage_marin", "LAVAGE MARIN"),
]
LOCATION_TO_LEGACY = dict(INTERVENTION_LOCATIONS)
# Clés fleet.FUEL_TYPES -> libellés de la sélection Studio « Énergie Moteur ».
FUEL_TO_LEGACY = {
    "diesel": "Diesel",
    "gasoline": "Essence",
    "electric": "Électrique",
    "full_hybrid": "Hybride",
    "plug_in_hybrid_diesel": "Hybride",
    "plug_in_hybrid_gasoline": "Hybride",
}
LEGACY_TO_FUEL = {"diesel": "diesel", "essence": "gasoline", "electrique": "electric", "hybride": "full_hybrid"}

# {modèle: {champ natif: (champ Studio historique, convertisseur)}}
LEGACY_FIELDS = {
    "crm.lead": {
        "rpbm_license_plate": ("x_studio_field_NVioD", None),
        "rpbm_vehicle_brand_id": ("x_studio_field_KyCjB", "brand"),
        "rpbm_vehicle_model_id": ("x_studio_field_ZhaeY", "model"),
        "rpbm_vin": ("x_studio_field_PfJlB", None),
        "rpbm_fuel_type": ("x_studio_field_TAhpP", "fuel"),
        "rpbm_vehicle_detail_model": ("x_studio_field_i8fWl", None),
        "rpbm_first_registration_date": ("x_studio_field_Eh6Wd", "month_year"),
        "rpbm_part_type": ("x_studio_field_eENQz", "part_type"),
        "rpbm_eurocode_base": ("x_studio_field_ORIyy", None),
        "rpbm_eurocode": ("x_studio_field_NwRik", None),
        "rpbm_vsf_designation": ("x_studio_field_j8eh3", None),
        "rpbm_vsf_stock": ("x_studio_field_BKtpw", "int_char"),
        "rpbm_constructor_reference": ("x_studio_field_MNzfJ", None),
        "rpbm_intervention_location": ("x_studio_lieu_intervention", "location"),
    },
    "sale.order.line": {
        "rpbm_xglass_price": ("x_studio_prix_x_glass", None),
    },
}

_LEGACY_VIN_RE = re.compile(r"var\s*=\s*([A-HJ-NPR-Z0-9]{17})\s*;")


def normalize(value):
    """Clé de comparaison : sans accents, casse et espaces indifférents."""
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text).strip().casefold()


def is_legacy_malformed_vin(value):
    """VIN produit par l'ancien parseur X'Glass, de la forme ``var = <VIN>;``."""
    return bool(_LEGACY_VIN_RE.fullmatch(str(value or "").strip()))


def clean_vin(value):
    text = str(value or "").strip()
    match = _LEGACY_VIN_RE.fullmatch(text)
    return match.group(1) if match else text


def month_year_to_date(value):
    """``MM/YYYY`` (format Studio et X'Glass) ou date ISO -> ``date`` (1er du mois), sinon None."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    for fmt in ("%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:10] if fmt == "%Y-%m-%d" else text, fmt).date()
        except ValueError:
            continue
    return None


def date_to_month_year(value):
    return value.strftime("%m/%Y") if value else False


class NameIndex:
    """Index par nom normalisé d'un référentiel (Studio ``x_name`` ou Fleet ``name``), avec création.

    Une orthographe exactement égale à la source est privilégiée en cas d'homonymes ; sinon la
    première correspondance est retenue. « Inconnu » et les noms vides ne sont jamais créés.
    """

    def __init__(self, env, model_name, name_field="name", domain=None):
        self.env, self.model_name, self.name_field = env, model_name, name_field
        self.rows = {}
        records = env[model_name].sudo().with_context(active_test=False).search_read(domain or [], [name_field])
        for row in records:
            self.rows.setdefault(normalize(row[name_field]), []).append((row["id"], row[name_field]))

    def find(self, name):
        candidates = self.rows.get(normalize(name)) or []
        if not candidates:
            return False
        exact = [candidate for candidate in candidates if candidate[1] == str(name).strip()]
        if len(exact) == 1:
            return exact[0][0]
        if len(candidates) > 1:
            _logger.warning("rpbm_agent: %s ambigu pour %r (%s correspondances), première retenue",
                            self.model_name, name, len(candidates))
        return candidates[0][0]

    def get_or_create(self, name, extra_vals=None):
        key = normalize(name)
        if not key or key == "inconnu":
            return False
        found = self.find(name)
        if found:
            return found
        record = self.env[self.model_name].sudo().create({self.name_field: str(name).strip(), **(extra_vals or {})})
        self.rows.setdefault(key, []).append((record.id, record[self.name_field]))
        return record.id


class _SyncCache:
    """Index construits à la demande, une fois par appel de synchronisation."""

    def __init__(self, env):
        self.env = env
        self._indexes = {}

    def studio(self, comodel_name):
        return self._index(("studio", comodel_name), comodel_name, "x_name")

    def fleet_brands(self):
        return self._index(("brand",), "fleet.vehicle.model.brand", "name")

    def fleet_models(self, brand_id):
        return self._index(("model", brand_id), "fleet.vehicle.model", "name", [("brand_id", "=", brand_id)])

    def _index(self, key, model_name, name_field, domain=None):
        if key not in self._indexes:
            self._indexes[key] = NameIndex(self.env, model_name, name_field, domain)
        return self._indexes[key]


def _as_raw(value):
    """Valeur comparable/écrivable : id pour un enregistrement, False pour vide (0 reste 0)."""
    if isinstance(value, models.BaseModel):
        return value.id or False
    return False if value in (None, "") else value


# Convertisseurs (env, record, valeur, cache, natifs en attente) -> valeur convertie, ou None si
# non convertible (le champ cible est alors laissé tel quel).
def _identity(env, record, value, cache, pending):
    return _as_raw(value)


def _brand_to_legacy(env, record, brand, cache, pending):
    if not brand:
        return False
    studio_field = record._fields[LEGACY_FIELDS["crm.lead"]["rpbm_vehicle_brand_id"][0]]
    return cache.studio(studio_field.comodel_name).get_or_create(brand.name)


def _brand_to_native(env, record, legacy, cache, pending):
    return cache.fleet_brands().get_or_create(legacy.x_name) if legacy else False


def _model_to_legacy(env, record, model, cache, pending):
    if not model:
        return False
    studio_field = record._fields[LEGACY_FIELDS["crm.lead"]["rpbm_vehicle_model_id"][0]]
    return cache.studio(studio_field.comodel_name).get_or_create(model.name)


def _model_to_native(env, record, legacy, cache, pending):
    if not legacy:
        return False
    brand_id = pending.get("rpbm_vehicle_brand_id") or record.rpbm_vehicle_brand_id.id
    if not brand_id:
        return None  # un modèle Fleet exige une marque
    return cache.fleet_models(brand_id).get_or_create(legacy.x_name, {"brand_id": brand_id})


def _fuel_to_legacy(env, record, value, cache, pending):
    return FUEL_TO_LEGACY.get(value) if value else False


def _fuel_to_native(env, record, value, cache, pending):
    return LEGACY_TO_FUEL.get(normalize(value)) if value else False


def _month_year_to_legacy(env, record, value, cache, pending):
    return date_to_month_year(value)


def _month_year_to_native(env, record, value, cache, pending):
    return month_year_to_date(value) if value else False


def _part_type_to_legacy(env, record, value, cache, pending):
    return PART_TYPE_TO_LEGACY.get(value) if value else False


def _part_type_to_native(env, record, value, cache, pending):
    if not value:
        return False
    return next((key for key, label in PART_TYPE_TO_LEGACY.items() if normalize(label) == normalize(value)), None)


def _location_to_legacy(env, record, value, cache, pending):
    return LOCATION_TO_LEGACY.get(value) if value else False


def _location_to_native(env, record, value, cache, pending):
    if not value:
        return False
    return next((key for key, label in INTERVENTION_LOCATIONS if normalize(label) == normalize(value)), None)


def _int_to_legacy(env, record, value, cache, pending):
    return False if value is None or value is False else str(value)


def _int_to_native(env, record, value, cache, pending):
    text = str(value or "").strip()
    if not text:
        return False
    return int(text) if text.isdigit() else None


CONVERTERS = {
    None: (_identity, _identity),
    "brand": (_brand_to_legacy, _brand_to_native),
    "model": (_model_to_legacy, _model_to_native),
    "fuel": (_fuel_to_legacy, _fuel_to_native),
    "month_year": (_month_year_to_legacy, _month_year_to_native),
    "part_type": (_part_type_to_legacy, _part_type_to_native),
    "location": (_location_to_legacy, _location_to_native),
    "int_char": (_int_to_legacy, _int_to_native),
}


def referenced_elsewhere(env, model_name, field_name):
    """Où un champ est encore cité : vues, automatisations, actions serveur, filtres, exports,
    autres champs. Sert de garde avant toute suppression."""
    pattern = re.compile(r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape(field_name))
    found = []
    views = env["ir.ui.view"].sudo().with_context(active_test=False).search([("arch_db", "ilike", field_name)])
    found += ["ir.ui.view %s (%s)" % (view.id, view.xml_id or view.name)
              for view in views if pattern.search(view.arch_db or "")]
    if "base.automation" in env:
        for auto in env["base.automation"].sudo().with_context(active_test=False).search([("model_name", "=", model_name)]):
            text = " ".join(filter(None, [auto.filter_domain, auto.filter_pre_domain,
                                          " ".join(auto.trigger_field_ids.mapped("name"))]))
            if pattern.search(text):
                found.append("base.automation %s (%s)" % (auto.id, auto.name))
    for action in env["ir.actions.server"].sudo().search([("model_name", "=", model_name)]):
        text = " ".join(str(action[name] or "") for name in ("code", "update_path") if name in action._fields)
        if pattern.search(text):
            found.append("ir.actions.server %s (%s)" % (action.id, action.name))
    for flt in env["ir.filters"].sudo().with_context(active_test=False).search([("model_id", "=", model_name)]):
        if pattern.search(" ".join(filter(None, [flt.domain, flt.context, flt.sort]))):
            found.append("ir.filters %s (%s)" % (flt.id, flt.name))
    for line in env["ir.exports.line"].sudo().search([("export_id.resource", "=", model_name), ("name", "=like", field_name + "%")]):
        if pattern.search(line.name or ""):
            found.append("ir.exports.line %s" % line.id)
    other_fields = env["ir.model.fields"].sudo().search([
        "|", "|", ("related", "ilike", field_name), ("depends", "ilike", field_name), ("compute", "ilike", field_name),
    ])
    for field in other_fields:
        if (field.model, field.name) == (model_name, field_name):
            continue
        if pattern.search(" ".join(filter(None, [field.related, field.depends, field.compute]))):
            found.append("ir.model.fields %s.%s" % (field.model, field.name))
    return found


class RpbmLegacySyncMixin(models.AbstractModel):
    _name = "rpbm.legacy.sync.mixin"
    _description = "Synchronisation des champs natifs avec les champs Studio historiques"

    def _rpbm_legacy_map(self):
        """{natif: (studio, convertisseur)} restreint aux champs Studio réellement présents."""
        return {native: (studio, kind)
                for native, (studio, kind) in LEGACY_FIELDS.get(self._name, {}).items()
                if studio in self._fields}

    def _rpbm_legacy_triggers(self):
        """{champ: natifs dérivés à resynchroniser quand ce champ est écrit}."""
        return {}

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("rpbm_legacy_sync"):
            records._rpbm_sync_legacy(vals_list)
        return records

    def write(self, vals):
        result = super().write(vals)
        if not self.env.context.get("rpbm_legacy_sync"):
            self._rpbm_sync_legacy([vals] * len(self))
        return result

    def _rpbm_sync_legacy(self, vals_list):
        mapping = self._rpbm_legacy_map()
        if not mapping:
            return
        triggers = self._rpbm_legacy_triggers()
        cache = _SyncCache(self.env)
        for record, vals in zip(self, vals_list):
            touched = {native for native in mapping if native in vals}
            for trigger, derived in triggers.items():
                if trigger in vals:
                    touched.update(native for native in derived if native in mapping)
            reverse = {native for native, (studio, _kind) in mapping.items() if studio in vals and native not in vals}
            if not touched and not reverse:
                continue
            native_vals, studio_vals = {}, {}
            # Studio -> natif d'abord : une saisie Studio explicite prime.
            for native in [name for name in mapping if name in reverse]:
                studio, kind = mapping[native]
                converted = CONVERTERS[kind][1](self.env, record, record[studio], cache, native_vals)
                if converted is not None and _as_raw(record[native]) != _as_raw(converted):
                    native_vals[native] = _as_raw(converted)
            for native in [name for name in mapping if name in touched and name not in reverse]:
                studio, kind = mapping[native]
                converted = CONVERTERS[kind][0](self.env, record, record[native], cache, native_vals)
                if converted is not None and _as_raw(record[studio]) != _as_raw(converted):
                    studio_vals[studio] = _as_raw(converted)
            synced = record.with_context(rpbm_legacy_sync=True)
            if native_vals:
                synced.write(native_vals)
            if studio_vals:
                synced.write(studio_vals)
