/** @odoo-module **/

import { AbstractRecord, AgentWidgetDialog } from "./agent_widget_dialog";
import { onWillStart } from "@odoo/owl";

class SaleOrder extends AbstractRecord{
    constructor(record) {
        super(record);
        this.immatriculationField = 'immatriculation_'
        this.calqueField = 'x_studio_field_eENQz'
    }

    get immatriculation(){
        return this.recordData[this.immatriculationField];
    }

    get calque(){
        return this.recordData[this.calqueField];
    }
}

export class AgentWidgetDialogSaleOrder extends AgentWidgetDialog {
    setup()
    {
        super.setup();

        /** @type {SaleOrder} */
        this.saleOrder = new SaleOrder(this.record);

        this.state.immatriculationValue = this.saleOrder.immatriculation;

        onWillStart(() => {
            this.onWillStart();
        });
    }

    async onWillStart(){
        await super.onWillStart();
        this.init()
    }
}