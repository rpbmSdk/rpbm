/** @odoo-module **/

import { AbstractRecord, AgentWidgetDialog, ArticleComponent } from "./agent_widget_dialog";
import { onWillStart } from "@odoo/owl";
import { useState, Component } from "@odoo/owl";


class SaleOrderLine extends AbstractRecord {
    constructor(record) {
        super(record);
    }

    // get immatriculation(){
    //     return this.recordData[this.immatriculationField];
    // }

    // get calque(){
    //     return this.recordData[this.calqueField];
    // }

    get productId() {
        return this.recordData.product_id;
    }
}

class SaleOrder extends AbstractRecord {
    constructor(record) {
        super(record);
        this.immatriculationField = 'x_studio_immatriculation_'
        this.calqueField = 'x_studio_field_eENQz'
    }

    get immatriculation() {
        return this.recordData[this.immatriculationField];
    }

    get OrderlLines() {
        return this.recordData.order_line;
    }
}

export class SaleOrderArticleComponent extends ArticleComponent {
    static template = "rpbm_agent.SaleOrderArticleComponent";
    setup() {
        super.setup();
        this.state = useState({
            ...this.state,
            // quantity: 1,
            // exists: false,
            product: undefined,
            // productId: undefined,
            isInOrder: false,
        })
        /** @type {SaleOrder} */
        this.saleOrder = new SaleOrder(this.record);
        onWillStart(async () => {
            await this.onWillStart();
        })

    }

    /**
     * @returns {boolean}
     */
    get productExists() {
        return Boolean(this.product)
    }

    /**
     * @returns {Product|undefined}
     */
    get product() {
        return this.state.product;
    }

    get productOdooUrl() {
        return `/web#id=${this.product.id}&view_type=form&model=product.product&action=product.product_template_action`
    }

    async onWillStart() {
        // await super.onWillStart();
        await this.doesProductExists();
        // this.state.exists = this.existsInOrder();
    }

    async doesProductExists() {
        const res = await this.rpc("/doesProductExists", {
            productCode: this.article.code
        })
        this.state.product = res ? res : undefined;
    }

    async createProduct() {
        const res = await this.rpc("/createProduct", {
            articleVsfInfo: this.article
        })
        await this.doesProductExists();
    }

    /**
     * @returns {boolean}
     */
    get existsInOrder() {
        return this.record.data.order_line.resIds.includes(this.product.id)
    }

    async addToSaleOrder(){
        await this.record.data.order_line.addNewRecord({
            product_id:this.product.id
        })
    }

}

export class AgentWidgetDialogSaleOrder extends AgentWidgetDialog {

    static template = "rpbm_agent.SaleOrderDialog";

    static components = {
        ...AgentWidgetDialog.components,
        SaleOrderArticleComponent
    };

    setup() {
        super.setup();
        this.state = useState({
            ...this.state,
        })

        /** @type {SaleOrder} */
        this.saleOrder = new SaleOrder(this.record);

        this.state.immatriculationValue = this.saleOrder.immatriculation;

        onWillStart(() => {
            this.onWillStart();
        });
    }

    async onWillStart() {
        await super.onWillStart();
        await this.init()
    }

    async onConfirm() {
        await super.onConfirm();


    }
}