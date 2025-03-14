/** @odoo-module **/

import { AgentWidgetDialog } from "./agent_widget_dialog";

// /**
// @typedef {Object} CrmLead
// @prop {number} id

//  */

class CrmLead {
    constructor(record) {
        Object.assign(this, record);
    }

    get data() {
        return this.data;
    }

    get immatriculation(){
        return this.data.x_studio_field_NVioD;
    }
}

export class AgentWidgetDialogCrmLead extends AgentWidgetDialog {
    setup() {
        super.setup();

        /** @type {CrmLead} */
        this.crmLead = new CrmLead(this.record);

        this.state.immatriculationValue = this.crmLead.immatriculation;
    
        
    
    }

    async onConfirm() {
        await super.onConfirm();
        this.record.data.x_studio_field_NVioD = this.state.immatriculationValue;
    }
}