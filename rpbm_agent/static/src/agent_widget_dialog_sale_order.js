/** @odoo-module **/

import { AgentWidgetDialog } from "./agent_widget_dialog";
import { AbstractWidgetRecord } from "./utils";
import { onWillStart } from "@odoo/owl";


class SaleOrder extends AbstractWidgetRecord {
    constructor(record) {
        super(record);
        this.immatriculationField = "x_studio_immatriculation_";
        // Le champ Studio de "Pièce concernée" porte un nom différent sur
        // sale.order que sur crm.lead.
        this.pieceConcerneeField = "x_studio_pice_concerne";
        this.fullEurocodeField = "x_studio_eurocode_complet";
        this.vsfDesignationField = "x_studio_vsf_dsignation_1";
        this.vsfStockField = "x_studio_vsf_qt_dispo";
        this.constructorReferenceField = "x_rpbm_vsf_constructor_reference";
    }
}


export class AgentWidgetDialogSaleOrder extends AgentWidgetDialog {
    static template = "rpbm_agent.SaleOrderDialog";

    setup() {
        super.setup();
        this.record = new SaleOrder(this.record);
        this.state.immatriculationValue = this.record.immatriculation;
        this._widgetOrderLinesByArticleCode = new Map();
        onWillStart(() => this.onWillStart());
    }

    async onWillStart() {
        await super.onWillStart();
    }

    getWidgetOrderLine(articleCode) {
        const line = this._widgetOrderLinesByArticleCode.get(articleCode);
        return this.props.record.data.order_line.records.includes(line) ? line : undefined;
    }

    isWidgetArticleInOrder(articleCode) {
        return Boolean(this.getWidgetOrderLine(articleCode));
    }

    isArticleAlreadyInOrder(articleCode) {
        const product = this.getProductForArticle(articleCode);
        if (!product) {
            return false;
        }
        const records = this.props.record.data.order_line.records;
        return records
            .filter((line) => line.data.product_id)
            .some((line) => line.data.product_id[0] === product.id);
    }

    async addArticleToSaleOrder(articleCode) {
        const product = this.getProductForArticle(articleCode);
        const article = this.getArticleByCode(articleCode);
        if (!product || !article || this.isArticleAlreadyInOrder(articleCode)) {
            return;
        }
        const xglassPrice = Number(article.prixVenteRPBM);
        if (!Number.isFinite(xglassPrice)) {
            this.notification.add("Le prix RPBM de l'article VSF est invalide.", { type: "danger" });
            return;
        }
        await this.runAsync(async () => {
            const newLine = await this.props.record.data.order_line.addNewRecord({
                context: { default_product_id: product.id },
            });
            // L'automatisation Studio « Tarif x glass » calcule price_unit à
            // partir de ce champ. Ne jamais renseigner price_unit à la main.
            await newLine.update({
                product_uom_qty: 1,
                x_studio_prix_x_glass: xglassPrice,
            });
            this._widgetOrderLinesByArticleCode.set(articleCode, newLine);
        }, "Ajout de l'article au devis en cours...");
    }

    async removeArticleFromSaleOrder(articleCode) {
        const line = this.getWidgetOrderLine(articleCode);
        if (!line) {
            return;
        }
        await this.runAsync(async () => {
            await this.props.record.data.order_line.delete(line);
            this._widgetOrderLinesByArticleCode.delete(articleCode);
        }, "Retrait de l'article du devis en cours...");
    }
}
