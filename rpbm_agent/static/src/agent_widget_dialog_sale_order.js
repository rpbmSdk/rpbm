/** @odoo-module **/

import { status } from "@odoo/owl";

import { AgentWidgetDialog } from "./agent_widget_dialog";
import { PART_TYPES } from "./utils";


// Lot E2 « VSF d'abord, X'Glass à la demande » : le dialog s'ouvre sans authentification sur
// l'encart « Dossier » et la recherche VSF ; « Charger X'Glass » (startAgents) lance la chaîne X'Glass.
export class AgentWidgetDialogSaleOrder extends AgentWidgetDialog {
    static template = "rpbm_agent.SaleOrderDialog";

    setup() {
        super.setup();
        // Code article → produit des lignes ajoutées par le widget pendant ce dialog.
        this._widgetProductIdsByArticleCode = new Map();
        this.state.selectedLaborOperationKeys = {};
        // La pièce concernée enregistrée n'est pas remplacée par la suggestion du calque restauré.
        this.state.pieceConcernee = this.record.pieceConcernee;
        this.state.xglassLoading = false;
    }

    async onWillStart() {}

    /**
     * « Charger X'Glass ». Un seul chargement à la fois : isLoading, partagé avec les autres
     * chargements, peut retomber pendant l'authentification. La catégorie que la chaîne restaure
     * est une restauration : l'effet du calque garde alors la base, le tableau VSF, la sélection
     * et la pièce concernée enregistrée, même sans base ni pièce mémorisées.
     */
    startAgents() {
        if (!this._startAgentsPromise) {
            this._restorePending = true;
            this.state.xglassLoading = true;
            this._startAgentsPromise = super.startAgents().finally(() => {
                this._startAgentsPromise = undefined;
                this.state.xglassLoading = false;
            });
        }
        return this._startAgentsPromise;
    }

    /**
     * Service rpc non protégé : celui de useService ne résout plus après la destruction du dialog,
     * qui garderait alors le verrou X'Glass pris pendant l'authentification (fermé avant sa réponse).
     */
    async auth_agents() {
        const rpc = this.env.services.rpc;
        await rpc("/rpbm_agent_auth");
        if (status(this) === "destroyed") {
            // Le verrou est rendu ; la promesse sans fin arrête la chaîne sans toucher à l'état.
            await rpc("/rpbm_agent_close").catch((error) => console.warn("Impossible de libérer la session portail", error));
            return new Promise(() => {});
        }
        this.state.agentsInitialized = true;
        this.state.reconnectRequired = false;
        this._agentLockReleased = false;
    }

    get showAgentGate() {
        return false;
    }

    get showVsfSection() {
        return true;
    }

    /** Au montage puis à chaque modification de la base, X'Glass chargé ou non. */
    shouldSearchVsf() {
        return Boolean(this.baseEurocode);
    }

    canConfirm() {
        return true;
    }

    async getRecordData() {
        // Sans véhicule et catégorie X'Glass, seules la base et l'article principal sont écrits :
        // les identifiants X'Glass mémorisés ne sont jamais effacés.
        return this.selectedVehicule && this.selectedCalque ? super.getRecordData() : this.getVsfRecordData();
    }

    /** Champs du dossier, lus en direct dans le formulaire, pour l'encart affiché sans X'Glass. */
    get recordSummary() {
        const data = this.props.record.data;
        const record = this.record;
        // Le nom Fleet porte déjà la plaque (« Marque/Modèle/Plaque ») ; sans véhicule, la plaque seule.
        const vehicule = data[record.vehiculeField]?.[1] || data[record.immatriculationField];
        const article = [data[record.fullEurocodeField], data[record.vsfDesignationField]].filter(Boolean).join(" — ");
        return [
            ["Véhicule", vehicule],
            ["Catégorie", data[record.categorieXglassField]],
            ["Pièce concernée", PART_TYPES.find(([key]) => key === data[record.pieceConcerneeField])?.[1]],
            ["Pièce X'Glass", data[record.xglassPieceLabelField]],
            ["Article principal", article],
        ].map(([label, value]) => [label, value || "—"]);
    }

    get laborOperations() {
        return this.selectedPiece?.laborOperations || [];
    }

    isLaborOperationInOrder(operation) {
        // Recherche par clé : l'objet renvoyé par addNewRecord n'est pas toujours celui conservé
        // dans records (recette 2026-09-20 : « Retirer » absent, 4 lignes T2 ajoutées à la suite).
        return this.props.record.data.order_line.records.some(
            (line) => line.data.rpbm_labor_operation_key === operation.key
        );
    }

    _laborLine(operation) {
        return this.props.record.data.order_line.records.find(
            (line) => line.data.rpbm_labor_operation_key === operation.key
        );
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
                    rpbm_labor_operation_key: operation.key,
                });
            }
            this.state.selectedLaborOperationKeys = {};
        }, "Ajout des opérations de main-d'œuvre au devis en cours...");
    }

    async removeLaborOperation(operation) {
        const line = this._laborLine(operation);
        if (!line) {
            return;
        }
        await this.runAsync(async () => {
            await this.props.record.data.order_line.delete(line);
        }, "Retrait de l'opération de main-d'œuvre du devis en cours...");
    }

    getWidgetOrderLine(articleCode) {
        // Recherche par produit, comme pour la main-d'œuvre : l'objet renvoyé par addNewRecord
        // n'est pas toujours celui conservé dans records (recette 2026-10-05, SO7763).
        const productId = this._widgetProductIdsByArticleCode.get(articleCode);
        return productId && this.props.record.data.order_line.records.find(
            (line) => line.data.product_id?.[0] === productId
        );
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
            // Le module recopie ce prix vers x_studio_prix_x_glass, d'où l'automatisation
            // Studio « Tarif x glass » dérive price_unit. Ne jamais renseigner price_unit ici.
            await newLine.update({
                product_uom_qty: 1,
                rpbm_xglass_price: xglassPrice,
            });
            this._widgetProductIdsByArticleCode.set(articleCode, product.id);
        }, "Ajout de l'article au devis en cours...");
    }

    async removeArticleFromSaleOrder(articleCode) {
        const line = this.getWidgetOrderLine(articleCode);
        if (!line) {
            return;
        }
        await this.runAsync(async () => {
            await this.props.record.data.order_line.delete(line);
            this._widgetProductIdsByArticleCode.delete(articleCode);
        }, "Retrait de l'article du devis en cours...");
    }
}
