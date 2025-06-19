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
    get odooId (){
        return this.recordData.id;
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
    async runAsync(fn, message="") {
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