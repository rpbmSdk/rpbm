/** @odoo-module **/

import { onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

import { AgentWidgetDialog } from "./agent_widget_dialog";
import { AgentWidgetDialogSaleOrder } from "./agent_widget_dialog_sale_order";

// Opportunité du devis ouvert par « Créer un devis ». En mémoire et à usage unique : une clé de
// contexte serait recopiée dans les actions suivantes par doActionButton (CTX_KEY_REGEX).
let pendingOpportunityId;

export class AgentWidgetDialogCrmLead extends AgentWidgetDialog {
    static template = "rpbm_agent.CrmLeadDialog";

    setup() {
        super.setup();
        this.action = useService("action");
    }

    // L'opportunité s'arrête à la base Eurocode (lot E) : l'article VSF se choisit sur le devis.
    onSearchBaseEurocode() {}

    async onCreateQuotation() {
        const record = this.props.record;
        if (!(await this.writeRecord(true))) {
            return;
        }
        this.props.close();
        pendingOpportunityId = record.resId;
        try {
            // Comme le bouton natif « Nouveau devis » : doActionButton fournit active_id au domaine de l'action.
            await this.action.doActionButton({
                type: "object",
                name: "action_sale_quotations_new",
                resModel: "crm.lead",
                resId: record.resId,
                context: record.context,
            });
        } finally {
            pendingOpportunityId = undefined;
        }
    }
}

// Le formulaire du devis est monté avant que doActionButton ne se résolve.
patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        if (this.props.resModel !== "sale.order") {
            return;
        }
        onMounted(() => {
            const root = this.model.root;
            if (pendingOpportunityId && root.isNew && root.data.opportunity_id?.[0] === pendingOpportunityId) {
                pendingOpportunityId = undefined;
                this.dialogService.add(AgentWidgetDialogSaleOrder, { record: root });
            }
        });
    },
});
