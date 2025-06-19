/** @odoo-module **/

import { Component } from "@odoo/owl";

export class CalqueComponent extends Component {
    static props = {
        calque: { type: Object },
        selectedCalqueId: { type: Number },
        // onClickCalque: {type: Function},
    }
    static template = "rpbm_agent.CalqueComponent";

    get class() {
        let className = "btn ";
        className += this.props.calque.id === this.props.selectedCalqueId ? "btn-primary" : "btn-outline-primary";
        return className;
    }
}