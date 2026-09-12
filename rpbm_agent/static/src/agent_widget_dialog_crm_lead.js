/** @odoo-module **/

import { AbstractRecord, AbstractWidgetRecord } from "./utils";
import { AgentWidgetDialog } from "./agent_widget_dialog";
import { onWillStart } from "@odoo/owl";
// /**
// @typedef {Object} CrmLead
// @prop {number} id

//  */

class CrmLead extends AbstractWidgetRecord{
    constructor(record) {
        super(record);
        this.immatriculationField = 'x_studio_field_NVioD'
        this.baseEurocodeField = 'x_studio_field_ORIyy'
        this.fullEurocodeField = 'x_studio_field_NwRik'
        this.vsfDesignationField = 'x_studio_field_j8eh3'
        this.vsfStockField = 'x_studio_field_BKtpw'
        this.constructorReferenceField = 'x_studio_field_MNzfJ'
    }

    
}

export class AgentWidgetDialogCrmLead extends AgentWidgetDialog {
    setup() {
        super.setup();

        /** @type {CrmLead} */
        this.record = new CrmLead(this.record);

        this.state.immatriculationValue = this.record.immatriculation;

        onWillStart(async () => {
            await this.onWillStart();
            
        });
        
    }

    async onWillStart(){
        await super.onWillStart();
        
    }

}
