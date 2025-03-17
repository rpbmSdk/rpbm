/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useState, Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

import { AgentWidgetDialog } from "./agent_widget_dialog";
import { AgentWidgetDialogCrmLead } from "./agent_widget_dialog_crm_lead";

export class AgentWidget extends Component {

    static template = "rpbm_agent.AgentWidget";

    setup() {
        super.setup();
        this.dialog = useService("dialog");
    }

    onOpenWindow() {
        const props = {
            // title: "Agent Widget",
            // size: "lg",
            record: this.props.record,
        };
        switch (this.props.record.resModel) {
            case "crm.lead":
                this.dialog.add(AgentWidgetDialogCrmLead, props);
                break;
            default:
                this.dialog.add(AgentWidgetDialog, props);
        }
        
    }
}

export const agentWidget = {
    component: AgentWidget,
}

registry.category("view_widgets").add("rpbm_agent_widget", agentWidget);