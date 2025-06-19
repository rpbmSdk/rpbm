/** @odoo-module **/

import { WebClient } from "@web/webclient/webclient";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";

patch(WebClient.prototype, "clean_tab_name.WebClient", {
    setup() {
        super.setup();
        this.title.setParts({ zopenerp: '' });
    }
});