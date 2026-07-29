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
 * @property {string} refConstructeur
 * @property {number|null} prixHT
 * @property {number} stock
 * @property {boolean} available
 * @property {{thumbnailUrl: string, fullUrl?: string}[]} images
 * @property {string[]} fullImageUrls
 * @property {{label: string, value: string}[]} technicalDetails
 * @property {number|null} largeurMm
 * @property {number|null} longueurMm
 * @property {ArticleVsf[]} suggestedArticles
 * @property {boolean} [detailsLoaded]
 * @property {boolean} [detailsUnavailable]
 */

/**
 * @typedef {Object} Product
 * @property {number} id
 * @property {string} name
 * @property {string} default_code
 * @property {'reference_interne'|'eurocode'|'nom'|'créé'} [matched_by]
 */

/**
 * @typedef {Object} OdooVehicule
 * @property {number} id
 */
