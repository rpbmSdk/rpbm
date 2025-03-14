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
 * @typedef {Object} Calque
 * @property {number} id
 * @property {string} libelle
 */

/**
 * @typedef {Object} Planche
 * @property {number} id
 * @property {string} calques
 */