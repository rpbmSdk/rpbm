/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { useState, Component } from "@odoo/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

// Clés de la sélection native crm.lead.rpbm_part_type (libellés identiques au serveur).
export const PART_TYPES = [
    ["windshield", "Pare-brise"],
    ["rear_window", "Lunette arrière"],
    ["side_window", "Glace latérale"],
    ["other", "Autre"],
];

/**
 * Propose une pièce concernée à partir du libellé du calque X'Glass.
 * La valeur reste visible et modifiable dans la dialog avant tout enregistrement.
 */
export function suggestPieceConcernee(calqueLabel) {
    switch ((calqueLabel || "").trim().toUpperCase()) {
        case "PARE-BRISE":
            return "windshield";
        case "GLACE AR":
            return "rear_window";
        case "GLACE PORTE AV":
        case "GLACE PORTE AR":
        case "GLACE FIXE PORTE AR":
            return "side_window";
        default:
            return "other";
    }
}

export class AbstractRecord {
    constructor(record) {
        Object.assign(this, record);
    }
    get recordData() {
        return this.data;
    }
}

/**
 * Champs natifs du module lus/écrits par le widget. Ils portent les mêmes noms sur
 * crm.lead et sur sale.order (miroirs related écrivables vers l'opportunité).
 */
export class AbstractWidgetRecord extends AbstractRecord {
    partnerField = "partner_id";
    immatriculationField = "rpbm_license_plate";
    vehiculeField = "rpbm_vehicle_id";
    categorieXglassField = "rpbm_xglass_category";
    pieceConcerneeField = "rpbm_part_type";
    baseEurocodeField = "rpbm_eurocode_base";
    xglassPieceIdField = "rpbm_xglass_piece_id";
    pieceOeIdField = "rpbm_piece_oe_id";
    pieceAmIdField = "rpbm_piece_am_id";
    fullEurocodeField = "rpbm_eurocode";
    vsfDesignationField = "rpbm_vsf_designation";
    vsfStockField = "rpbm_vsf_stock";
    constructorReferenceField = "rpbm_constructor_reference";

    get immatriculation() {
        return this.recordData[this.immatriculationField];
    }

    get categorieXglass() {
        return this.recordData[this.categorieXglassField];
    }

    get baseEurocode() {
        return this.recordData[this.baseEurocodeField];
    }

    get pieceConcernee() {
        return this.recordData[this.pieceConcerneeField];
    }

    get partnerId(){
        return this.recordData[this.partnerField][0];
    }

}

const initialAsyncWidgetState = {
    loading: false,
    loadingMessage: "",
}

export class asyncWidget extends Component {
    static props = {
        ...standardWidgetProps,
    }
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        /** @type {AbstractWidgetRecord} */
        this.record = this.props.record;
        // Chaque composant doit posséder son propre état réactif. Partager le
        // même proxy faisait afficher le chargement d'un article sur tous les
        // autres articles de la dialog.
        this.state = useState({ ...initialAsyncWidgetState });
    }

    /**
     * Return true if the widget is loading
     * @returns {boolean}
     *  */
    get isLoading() {
        return this.state.loading;
    }

    /**
     * Return the loading message
     * @returns {string}
     *  */
    get loadingMessage() {
        return this.state.loadingMessage;
    }

    /**
     * Set the loading message
     * @param {string} message - the message to display
     * */
    setLoadingMessage(message) {
        this.state.loadingMessage = message;
    }

    /**
     * Set the loading state to true
     *  */
    startLoading() {
        this.state.loading = true;
    }

    /**
     * Set the loading state to false
     *  */
    stopLoading() {
        this.state.loading = false;
    }

    /**
     * Run an async function and set the loading state to true before and to false after
     * @param {Function} fn - async function to run
     */
    async runAsync(fn, message = "") {
        this.startLoading();
        this.state.loadingMessage = message;
        try {
            await fn();
        }
        catch (e) {
            console.error(e);
            this.notification.add(e.data?.message || e.message || "Une erreur est survenue", { type: "danger" });
        }
        this.stopLoading();
    }
}
