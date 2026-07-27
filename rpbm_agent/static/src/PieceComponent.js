/** @odoo-module **/

import { Component } from "@odoo/owl";
import { onWillStart, useRef, useEffect } from "@odoo/owl";

export class PieceComponent extends Component {
    static props = {
        piece: { type: Object },
        selectedPieceId: { type: Number },
    }
    static template = "rpbm_agent.PieceComponent";

    get style() {
        return this.props.piece.id === this.props.selectedPieceId ? "background-color: azure !important;" : "";
    }

    /**
     * Détails X'Glass immédiatement utiles pour distinguer des pièces OE aux
     * intitulés identiques. La réponse de /getPieces contient déjà pieceOe et
     * ses caractéristiques : aucun appel portail complémentaire n'est requis.
     */
    get displayAttributes() {
        const pieceOe = this.props.piece.pieceOe || {};
        const attributes = [];
        const add = (key, label, value) => {
            if (value) {
                attributes.push({ key, label, value });
            }
        };

        add("reference", "Réf. OE", pieceOe.referenceClean || pieceOe.reference);
        add(
            "detail",
            "Détail technique",
            pieceOe.descriptionTechnique || pieceOe.libelleComplementaire
        );
        add("couleur", "Couleur", pieceOe.couleur);

        for (const characteristic of pieceOe.caracteristiques || []) {
            const type = characteristic.type || {};
            if (characteristic.valeur && (type.discriminantArbo || type.discriminantFiltre)) {
                add(
                    `characteristic-${characteristic.id}`,
                    type.libelle || "Caractéristique",
                    characteristic.valeur
                );
            }
        }

        return attributes.slice(0, 4);
    }
}
