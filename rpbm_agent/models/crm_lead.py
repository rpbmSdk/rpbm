from odoo import api, fields, models
from odoo.addons.fleet.models.fleet_vehicle_model import FUEL_TYPES

from .legacy_fields import INTERVENTION_LOCATIONS, PART_TYPES, clean_vin

# Dérivés du véhicule Fleet lié ; restent saisissables pour les dossiers sans véhicule.
VEHICLE_DERIVED_FIELDS = (
    "rpbm_license_plate",
    "rpbm_vehicle_brand_id",
    "rpbm_vehicle_model_id",
    "rpbm_vin",
    "rpbm_fuel_type",
    "rpbm_vehicle_detail_model",
    "rpbm_first_registration_date",
)


class CrmLead(models.Model):
    _name = "crm.lead"
    _inherit = ["crm.lead", "rpbm.legacy.sync.mixin"]

    rpbm_vehicle_id = fields.Many2one("fleet.vehicle", string="Véhicule", index=True, ondelete="set null")
    rpbm_license_plate = fields.Char("Immatriculation", compute="_compute_rpbm_vehicle_fields", store=True, readonly=False)
    rpbm_vehicle_brand_id = fields.Many2one(
        "fleet.vehicle.model.brand", string="Marque du véhicule",
        compute="_compute_rpbm_vehicle_fields", store=True, readonly=False, index=True,
    )
    rpbm_vehicle_model_id = fields.Many2one(
        "fleet.vehicle.model", string="Modèle du véhicule",
        compute="_compute_rpbm_vehicle_fields", store=True, readonly=False, index=True,
    )
    rpbm_vin = fields.Char("VIN", compute="_compute_rpbm_vehicle_fields", store=True, readonly=False)
    rpbm_fuel_type = fields.Selection(
        FUEL_TYPES, string="Énergie", compute="_compute_rpbm_vehicle_fields", store=True, readonly=False,
    )
    rpbm_vehicle_detail_model = fields.Char(
        "Détail du modèle", compute="_compute_rpbm_vehicle_fields", store=True, readonly=False,
    )
    rpbm_first_registration_date = fields.Date(
        "Date de 1re mise en circulation", compute="_compute_rpbm_vehicle_fields", store=True, readonly=False,
    )
    rpbm_xglass_category = fields.Char("Catégorie X'Glass")
    rpbm_part_type = fields.Selection(PART_TYPES, string="Pièce concernée")
    rpbm_eurocode_base = fields.Char("Base Eurocode")
    rpbm_eurocode = fields.Char("Eurocode", index=True)
    rpbm_vsf_designation = fields.Char("Désignation VSF")
    rpbm_vsf_stock = fields.Integer("Stock VSF")
    rpbm_constructor_reference = fields.Char("Référence constructeur")
    rpbm_intervention_location = fields.Selection(INTERVENTION_LOCATIONS, string="Lieu d'intervention")
    rpbm_xglass_piece_id = fields.Char("Identifiant pièce X'Glass sélectionnée")
    rpbm_piece_oe_id = fields.Char("Identifiant pièce OE sélectionnée")
    rpbm_piece_am_id = fields.Char("Identifiant pièce après-marché sélectionnée")

    def _rpbm_legacy_triggers(self):
        return {"rpbm_vehicle_id": VEHICLE_DERIVED_FIELDS}

    @api.depends(
        "rpbm_vehicle_id", "rpbm_vehicle_id.license_plate", "rpbm_vehicle_id.model_id",
        "rpbm_vehicle_id.model_id.brand_id", "rpbm_vehicle_id.vin_sn", "rpbm_vehicle_id.fuel_type",
        "rpbm_vehicle_id.rpbm_detail_model", "rpbm_vehicle_id.rpbm_first_registration_date",
    )
    def _compute_rpbm_vehicle_fields(self):
        for lead in self:
            vehicle = lead.rpbm_vehicle_id
            derived = {
                "rpbm_license_plate": vehicle.license_plate,
                "rpbm_vehicle_brand_id": vehicle.model_id.brand_id,
                "rpbm_vehicle_model_id": vehicle.model_id,
                "rpbm_vin": clean_vin(vehicle.vin_sn),
                "rpbm_fuel_type": vehicle.fuel_type,
                "rpbm_vehicle_detail_model": vehicle.rpbm_detail_model,
                "rpbm_first_registration_date": vehicle.rpbm_first_registration_date,
            } if vehicle else {}
            for name in VEHICLE_DERIVED_FIELDS:
                # Fleet complète le dossier mais n'efface jamais une valeur existante.
                lead[name] = derived.get(name) or lead[name]
