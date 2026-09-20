/** @odoo-module **/

import { AgentWidgetDialog } from "./agent_widget_dialog";
import { AbstractWidgetRecord } from "./utils";


class SaleOrder extends AbstractWidgetRecord {
    constructor(record) {
        super(record);
        this.immatriculationField = "x_studio_immatriculation_";
        // Le champ Studio de "Pièce concernée" porte un nom différent sur
        // sale.order que sur crm.lead.
        this.pieceConcerneeField = "x_studio_pice_concerne";
        this.fullEurocodeField = "x_studio_eurocode_complet";
        this.xglassPieceIdField = "x_rpbm_xglass_piece_id";
        this.pieceOeIdField = "x_rpbm_piece_oe_id";
        this.pieceAmIdField = "x_rpbm_piece_am_id";
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
        this.restoreSelectionFromRecord();
        this._widgetOrderLinesByArticleCode = new Map();
        this._widgetLaborLinesByKey = new Map();
        this.state.selectedLaborOperationKeys = {};
        this._restoreLaborLines();
    }

    _restoreLaborLines() {
        for (const line of this.props.record.data.order_line.records) {
            const key = line.data.x_rpbm_labor_operation_key;
            if (key) {
                this._widgetLaborLinesByKey.set(key, line);
            }
        }
    }

    get laborOperations() {
        return this.selectedPiece?.laborOperations || [];
    }

    isLaborOperationInOrder(operation) {
        const line = this._widgetLaborLinesByKey.get(operation.key);
        return Boolean(line && this.props.record.data.order_line.records.includes(line));
    }

    isLaborOperationSelected(operation) {
        return Boolean(this.state.selectedLaborOperationKeys[operation.key]);
    }

    toggleLaborOperation(operation) {
        if (operation.unavailableReason || this.isLaborOperationInOrder(operation)) {
            return;
        }
        this.state.selectedLaborOperationKeys = {
            ...this.state.selectedLaborOperationKeys,
            [operation.key]: !this.isLaborOperationSelected(operation),
        };
    }

    async addSelectedLaborOperations() {
        const operations = this.laborOperations.filter(operation =>
            this.isLaborOperationSelected(operation) && !operation.unavailableReason && !this.isLaborOperationInOrder(operation)
        );
        if (!operations.length) {
            return;
        }
        await this.runAsync(async () => {
            for (const operation of operations) {
                const newLine = await this.props.record.data.order_line.addNewRecord({
                    context: { default_product_id: operation.productId },
                });
                await newLine.update({
                    product_uom_qty: operation.duration,
                    x_rpbm_labor_operation_key: operation.key,
                });
                this._widgetLaborLinesByKey.set(operation.key, newLine);
            }
            this.state.selectedLaborOperationKeys = {};
        }, "Ajout des opérations de main-d'œuvre au devis en cours...");
    }

    async removeLaborOperation(operation) {
        const line = this._widgetLaborLinesByKey.get(operation.key);
        if (!line) {
            return;
        }
        await this.runAsync(async () => {
            await this.props.record.data.order_line.delete(line);
            this._widgetLaborLinesByKey.delete(operation.key);
        }, "Retrait de l'opération de main-d'œuvre du devis en cours...");
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
