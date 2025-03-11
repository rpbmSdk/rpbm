/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useState, Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

import { AgentWidgetDialog } from "./agent_widget_dialog";

export class AgentWidget extends Component{

    static template = "rpbm_agent.AgentWidget";

    setup(){
        super.setup();
        this.dialog = useService("dialog");

        this.state = useState({
            agents: [],
        });
    }

    onOpenWindow(){
        this.dialog.add(AgentWidgetDialog, {
            title: "Agents",
            size: "large",
            buttons: [
                {text: "Close", close: true},
            ],
        });
    }
}

export const agentWidget = {
    component: AgentWidget,
}

registry.category("view_widgets").add("rpbm_agent_widget", agentWidget);