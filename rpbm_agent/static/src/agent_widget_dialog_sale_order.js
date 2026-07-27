/** @odoo-module **/

import { AgentWidgetDialog } from "./agent_widget_dialog";
import { AbstractWidgetRecord } from "./utils";
import { onWillStart } from "@odoo/owl";


class SaleOrder extends AbstractWidgetRecord {
    constructor(record) {
        super(record);
        this.immatriculationField = "x_studio_immatriculation_";
    }
}


export class AgentWidgetDialogSaleOrder extends AgentWidgetDialog {
    static template = "rpbm_agent.SaleOrderDialog";

    setup() {
        super.setup();
        this.record = new SaleOrder(this.record);
        this.state.immatriculationValue = this.record.immatriculation;
        onWillStart(() => this.onWillStart());
    }

    async onWillStart() {
        await super.onWillStart();
    }

    get selectedProductInOrder() {
        if (!this.selectedProduct) {
            return false;
        }
        const records = this.props.record.data.order_line.records;
        return records
            .filter((line) => line.data.product_id)
            .some((line) => line.data.product_id[0] === this.selectedProduct.id);
    }

    async addSelectedProductToSaleOrder() {
        if (!this.selectedProduct || !this.selectedArticleVsf) {
            return;
        }
        const xglassPrice = Number(this.selectedArticleVsf.prixVenteRPBM);
        if (!Number.isFinite(xglassPrice)) {
            this.notification.add("Le prix RPBM de l'article VSF est invalide.", { type: "danger" });
            return;
        }
        await this.runAsync(async () => {
            const newLine = await this.props.record.data.order_line.addNewRecord({
                context: { default_product_id: this.selectedProduct.id },
            });
            // L'automatisation Studio « Tarif x glass » calcule price_unit à
            // partir de ce champ. Ne jamais renseigner price_unit à la main.
            await newLine.update({
                product_uom_qty: 1,
                x_studio_prix_x_glass: xglassPrice,
            });
        }, "Ajout de l'article au devis en cours...");
    }
}
