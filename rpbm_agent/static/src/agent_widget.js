/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

import { AgentWidgetDialogCrmLead } from "./agent_widget_dialog_crm_lead";
import { AgentWidgetDialogSaleOrder } from "./agent_widget_dialog_sale_order";

// Le widget n'est placé que par views/crm_lead_views.xml et views/sale_order_views.xml.
const DIALOG_BY_MODEL = {
    "crm.lead": AgentWidgetDialogCrmLead,
    "sale.order": AgentWidgetDialogSaleOrder,
};

export class AgentWidget extends Component {

    static props = {
        record: { type: Object },
        readonly: { type: Boolean, optional: true },
    };
    static template = "rpbm_agent.AgentWidget";

    setup() {
        super.setup();
        this.dialog = useService("dialog");
    }

    onOpenWindow() {
        const dialogClass = DIALOG_BY_MODEL[this.props.record.resModel];
        if (dialogClass) {
            this.dialog.add(dialogClass, { record: this.props.record });
        }
    }
}

export const agentWidget = {
    component: AgentWidget,
}

registry.category("view_widgets").add("rpbm_agent_widget", agentWidget);
