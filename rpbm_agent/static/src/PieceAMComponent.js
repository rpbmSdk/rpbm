/** @odoo-module **/


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
 * @property {number} prix
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
 * @property {string} finValidite
 * @property {PieceAM} pieceAm
 * @property {number|null} prixImport
 * @property {number} quantiteInDevis
 * @property {string} remarque
 */


export class PieceAMComponent extends Component {
    static props = {
        metaPieceAM: { type: Object },
        selectedPieceAMId: { type: Number },
    }
    static template = "rpbm_agent.PieceAMComponent";

    setup() {
        super.setup();
        
        /** @type {PieceAM} */
        this.pieceAM = this.props.metaPieceAM.pieceAm;
    }

    get style() {
        return this.pieceAM.id === this.props.selectedPieceAMId ? "background-color: azure !important;" : "";
    }
    /**
     * Retourne la date de début et de fin de validité formatée, si il n'y a pas de date de fin, retourne uniquement la date de début
     * @return {string}
     */
    get dateLibelle() {
        if (this.pieceAM.debutValidite && this.pieceAM.finValidite) {
            return `De ${this.pieceAM.debutValidite} à ${this.pieceAM.finValidite}`;
        } else if (this.pieceAM.debutValidite) {
            return `A partir du ${this.pieceAM.debutValidite}`;
        }
    }
}