/** @odoo-module **/


import { useService } from "@web/core/utils/hooks";
import { useState, Component } from "@odoo/owl";
import { Dialog } from '@web/core/dialog/dialog';


export class AgentWidgetDialog extends Component{
    static components = { Dialog }
    static template = "rpbm_agent.AgentWidgetDialog";

    setup(){
        super.setup();
        this.rpc = useService("rpc");
        this.orm = useService("orm");
        this.record = this.props.record;
        this.state = useState({
        });


    }

    onConfirm(){
        this.props.close();
    }

    onDiscard(){
        this.props.close();
    }
}