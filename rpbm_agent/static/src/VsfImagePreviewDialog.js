/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useHotkey } from "@web/core/hotkeys/hotkey_hook";

export class VsfImagePreviewDialog extends Component {
    static components = { Dialog };
    static props = {
        images: { type: Array },
        index: { type: Number },
        close: { type: Function, optional: true },
    };
    static template = "rpbm_agent.VsfImagePreviewDialog";

    setup() {
        this.state = useState({ index: this.props.index });
        useHotkey("arrowleft", () => this.move(-1), { allowRepeat: true });
        useHotkey("arrowright", () => this.move(1), { allowRepeat: true });
    }

    get imageUrl() {
        return this.props.images[this.state.index];
    }

    get imageAlt() {
        return `Image article VSF ${this.state.index + 1} sur ${this.props.images.length}`;
    }

    move(step) {
        const { length } = this.props.images;
        if (length > 1) {
            this.state.index = (this.state.index + step + length) % length;
        }
    }
}
