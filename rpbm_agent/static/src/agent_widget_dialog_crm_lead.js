/** @odoo-module **/

import { AbstractRecord, AgentWidgetDialog } from "./agent_widget_dialog";
import { onWillStart } from "@odoo/owl";
// /**
// @typedef {Object} CrmLead
// @prop {number} id

//  */

class CrmLead extends AbstractRecord{
    constructor(record) {
        super(record);
        this.immatriculationField = 'x_studio_field_NVioD'
        this.calqueField = 'x_studio_field_eENQz'
    }

    get immatriculation(){
        return this.recordData[this.immatriculationField];
    }

    get calque(){
        return this.recordData[this.calqueField];
    }
}

export class AgentWidgetDialogCrmLead extends AgentWidgetDialog {
    setup() {
        super.setup();

        /** @type {CrmLead} */
        this.crmLead = new CrmLead(this.record);

        this.state.immatriculationValue = this.crmLead.immatriculation;

        onWillStart(async () => {
            if(this.state.immatriculationValue){
                await this.onSearchImmatriculation()
                if (this.vehicules.length > 0){
                    this.onSelectVehicule(this.vehicules[0])
                    await this.getPlanche()
                    this.calques.forEach(calque => console.log(calque.libelle))
                }
            }
        });
        
    }

    async onConfirm() {
        await super.onConfirm();
        const data = {};
        data[this.crmLead.immatriculationField] = this.state.immatriculationValue;
        const OdooVehiculeId = await this.getOdooVehicule()
        this.record.update({
            [this.crmLead.immatriculationField]: this.state.immatriculationValue
        });
    }
}