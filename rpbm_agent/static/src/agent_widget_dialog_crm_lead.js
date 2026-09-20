/** @odoo-module **/

import { AbstractWidgetRecord } from "./utils";
import { AgentWidgetDialog } from "./agent_widget_dialog";

class CrmLead extends AbstractWidgetRecord{
    constructor(record) {
        super(record);
        this.immatriculationField = 'x_studio_field_NVioD'
        this.baseEurocodeField = 'x_studio_field_ORIyy'
        this.xglassPieceIdField = 'x_rpbm_xglass_piece_id'
        this.pieceOeIdField = 'x_rpbm_piece_oe_id'
        this.pieceAmIdField = 'x_rpbm_piece_am_id'
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
        this.restoreSelectionFromRecord();
    }
}
