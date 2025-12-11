/** @odoo-module **/

import { WebClient } from "@web/webclient/webclient";
import { patch } from "@web/core/utils/patch";

patch(WebClient.prototype, {
    setup() {
        var self = this;
        super.setup();
        const app_system_name = '';
        // zopenerp is easy to grep
        this.title.setParts({ zopenerp: app_system_name });

    }
});