/** @odoo-module **/

import { Component } from "@odoo/owl";

/**
 * @typedef {Object} CriterePiece
 * @property {boolean} ciceron
 * @property {string} cleTradValeur
 * @property {number} id
 * @property {string} type
 * @property {boolean} cicerone
 * @property {string} cleTradLibelle
 * @property {boolean} discriminantArbo
 * @property {boolean} discriminantFiltre
 * @property {number} id
 * @property {string|null} image
 * @property {string} libelle
 * @property {number|null} ordre
 * @property {number|null} tolerance
 * @property {boolean} traduisible
 * @property {string} typeValeur
 * @property {string|null} unit
 * @property {string} valeur
 */

/**
 * @typedef {Object} Fournisseur
 * @property {number|null} codeEtai
 * @property {number} id
 * @property {string} libelle
 * @property {number|null} ordre
 * @property {string|null} refimage
 * @property {string|null} gammeFournisseur
 */

/**
 * @typedef {Object} PieceAM
 * @property {null|any} caracteristiquesPieceValeur
 * @property {CriterePiece[]} criterePieces
 * @property {string} description
 * @property {Fournisseur} fournisseur
 * @property {number|null} idcaracteristiquepieceam
 * @property {number} id
 * @property {string} libelle
 * @property {number|null} prix
 * @property {string} reference
 * @property {string} referenceClean
 * @property {string|null} referenceCmt
 * @property {string|null} refimage
 * @property {Array} variantes
 * @property {number|null} prixImport
 * @property {number} quantiteInDevis
 * @property {string} remarque
 */

/**
 * @typedef {Object} MetaPieceAM
 * @property {string} debutValidite
 * @property {string|null} finValidite
 * @property {PieceAM} pieceAm
 * @property {number|null} prixImport
 * @property {number} quantiteInDevis
 * @property {string} remarque
 */


export class PieceAMComponent extends Component {
    static props = {
        metaPieceAM: { type: Object },
        selectedPieceAMId: { type: Number, optional: true },
        // Ligne compacte (encart « Autres marques AM ») au lieu d'une carte.
        compact: { type: Boolean, optional: true },
    }
    static template = "rpbm_agent.PieceAMComponent";

    /** @returns {PieceAM} */
    get pieceAM() {
        return this.props.metaPieceAM.pieceAm;
    }

    get style() {
        return this.pieceAM.id === this.props.selectedPieceAMId ? "background-color: azure !important;" : "";
    }

    get fournisseur() {
        return this.pieceAM.fournisseur?.libelle || "";
    }

    /**
     * Validité portée par l'entrée (pas par pieceAm), libellés X'Glass
     * `elementSit.lbl.validite.*` (controllers/xglass_lbl.py).
     * @return {string}
     */
    get dateLibelle() {
        const { debutValidite, finValidite } = this.props.metaPieceAM;
        if (debutValidite && finValidite) {
            return `De ${debutValidite} à ${finValidite}`;
        } else if (debutValidite) {
            return `A partir de ${debutValidite}`;
        } else if (finValidite) {
            return `Jusqu'à ${finValidite}`;
        }
        return "";
    }

    /** Comme X'Glass : remarque de l'entrée puis description, sauf remarque vide ou « - ». */
    get description() {
        const remarque = (this.props.metaPieceAM.remarque || "").trim();
        return [remarque === "-" ? "" : remarque, this.pieceAM.description].filter(Boolean).join("; ");
    }

    get hasPrix() {
        return this.pieceAM.prix !== null && this.pieceAM.prix !== undefined;
    }
}
