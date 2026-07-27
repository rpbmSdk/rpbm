/** @odoo-module **/

import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class VsfImagePreviewDialog extends Component {
    static components = { Dialog };
    static props = {
        imageUrl: { type: String },
        close: { type: Function, optional: true },
    };
    static template = "rpbm_agent.VsfImagePreviewDialog";
}
