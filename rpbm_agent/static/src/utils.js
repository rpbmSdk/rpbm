/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { useState, Component } from "@odoo/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

export const PIECE_CONCERNEE_OPTIONS = [
    "Pare-Brise",
    "Lunette arrière",
    "Glace Latérale",
    "Autre...",
];

/**
 * Propose une valeur de tarification legacy à partir du libellé X'Glass.
 * La valeur reste visible et modifiable dans la dialog avant tout enregistrement.
 */
export function suggestPieceConcernee(calqueLabel) {
    switch ((calqueLabel || "").trim().toUpperCase()) {
        case "PARE-BRISE":
            return "Pare-Brise";
        case "GLACE AR":
            return "Lunette arrière";
        case "GLACE PORTE AV":
        case "GLACE PORTE AR":
        case "GLACE FIXE PORTE AR":
            return "Glace Latérale";
        default:
            return "Autre...";
    }
}

export class AbstractRecord {
    constructor(record) {
        Object.assign(this, record);
    }
    get recordData() {
        return this.data;
    }
    get odooId() {
        return this.recordData.id;
    }
}

export class AbstractWidgetRecord extends AbstractRecord {
    /** Modèles sur lesquels ont peut ajouter un widget et récupérer / éditer les données (ex. crm.lead, sale.order, etc) */

    partnerField = "partner_id";
    categorieXglassField = "x_studio_categorie_xglass";
    vehiculeField = "x_studio_vehicle_id";
    immatriculationField = "x_studio_immatriculation";
    baseEurocodeField = "x_studio_base_eurocode";
    pieceConcerneeField = "x_studio_field_eENQz";
    fullEurocodeField = undefined;
    vsfDesignationField = undefined;
    vsfStockField = undefined;
    constructorReferenceField = undefined;

    constructor(record) {
        super(record);
        // this.vehiculeField = vehiculeField;
        // this.immatriculationField = immatriculationField;
    }

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
