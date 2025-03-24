/** @odoo-module **/

/**
 * @typedef {Object} VehiculeMarque
 * @property {number} id
 * @property {string} nom
 */

/**
 * @typedef {Object} VehiculeModel
 * @property {number} id
 * @property {string} gamme
 * @property {string} imageRef
 * @property {VehiculeMarque} marque
 */

/**
 * @typedef {Object} Vehicule
 * @property {number} id
 * @property {string} energieLibelle
 * @property {string} imageRef
 * @property {string} libelleCourt
 * @property {VehiculeModel} modele
 */

/**
 * @typedef {Object} VehiculeMeta
 * @property {string} vin
 * @property {string} cnit
 * @property {string} dateMec
 */

/**
 * @typedef {Object} Calque
 * @property {number} id
 * @property {string} libelle
 */

/**
 * @typedef {Object} Planche
 * @property {number} id
 * @property {Calque[]} calques
 */

/**
 * @typedef {Object} ArticleVsf
 * @property {string} name
 * @property {string} code
 * @property {number} prixVente
 * @property {number} prixVenteRPBM
 */

/**
 * @typedef {Object} Product
 * @property {number} id
 * @property {string} name
 * @property {string} default_code
 */