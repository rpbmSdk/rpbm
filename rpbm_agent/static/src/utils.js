/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { useState, Component } from "@odoo/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

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

    categorieXglassField = "x_studio_categorie_xglass";
    vehiculeField = "x_studio_vehicle_id";
    immatriculationField = "x_studio_immatriculation";
    baseEurocodeField = "x_studio_base_eurocode";
    // calqueField = "x_studio_calque";

    constructor(record) {
        super(record);
        // this.vehiculeField = vehiculeField;
        // this.immatriculationField = immatriculationField;
    }

    get immatriculation() {
        return this.recordData[this.immatriculationField];
    }

    get calque() {
        return this.recordData[this.calqueField];
    }

    get categorieXglass() {
        return this.recordData[this.categorieXglassField];
    }

    get baseEurocode() {
        return this.recordData[this.baseEurocodeField];
    }

}

const asyncWidgetState = {
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
        this.orm = useService("orm");
        /** @type {AbstractWidgetRecord} */
        this.record = this.props.record;
        this.state = useState(asyncWidgetState);
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
     * Toogle the loading state
     *  */
    toogleLoading() {
        this.state.loading = !this.state.loading;
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
        console.log("stopLoading");
        console.log(this.isLoading);
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
        }
        this.stopLoading();
    }
}