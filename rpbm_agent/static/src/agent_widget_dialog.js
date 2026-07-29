/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { Dialog } from '@web/core/dialog/dialog';
import { onWillUnmount, useEffect } from "@odoo/owl";

import {
    asyncWidget,
    AbstractWidgetRecord,
    PIECE_CONCERNEE_OPTIONS,
    suggestPieceConcernee,
} from "./utils";
import { VehiculeComponent } from "./VehiculeComponent";
import { CalqueComponent } from "./CalqueComponent";
import { PieceComponent } from "./PieceComponent";
import { ArticleComponent } from "./ArticleComponent";
import { PieceAMComponent } from "./PieceAMComponent";
import { VsfImagePreviewDialog } from "./VsfImagePreviewDialog";

/**
 * @typedef {import('./types').Vehicule}
 * @typedef {import('./types').Planche}
 * @typedef {import('./types').Calque}
 * @typedef {import('./types').OdooVehicule}
 * @typedef {import('./PieceAMComponent').MetaPieceAM}
 */

export class AgentWidgetDialog extends asyncWidget {
    static components = {
        Dialog,
        VehiculeComponent,
        CalqueComponent,
        PieceComponent,
        PieceAMComponent,
        ArticleComponent
    }
    static props = {
        ...asyncWidget.props,
        close: { type: Function, optional: true },
    }
    static template = "rpbm_agent.AgentWidgetDialog";

    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.dialog = useService("dialog");
        /** @type {AbstractWidgetRecord} */
        this.record = new AbstractWidgetRecord(this.props.record);
        this.state = useState({
            ...this.state,
            canConfirm: false,
            agentsInitialized: false,
            // loading: false,
            immatriculationValue: "",
            vehicules: [],
            selectedVehicule: undefined,
            selectedVehiculeId: 0,
            vehiculeMeta: undefined,
            planche: undefined,
            calques: [],
            selectedCalque: undefined,
            pieces: [],
            selectedPiece: undefined,
            piecesAm: [],
            selectedPieceAm: undefined,
            baseEurocode: undefined,
            articlesVsf: [],
            selectedArticleCodes: {},
            articleProducts: {},
            articleLoadingCodes: {},
            pieceConcernee: undefined,
        });
        this._agentLockReleased = false;
        this._lastSearchedBaseEurocode = undefined;

        // La croix de la dialog et Échap contournent onDiscard(). Le crochet de
        // cycle de vie garantit que le verrou X'Glass est libéré quel que soit
        // le moyen employé pour fermer la fenêtre.
        onWillUnmount(() => {
            this.closeAgents().catch((error) => {
                console.warn("Impossible de libérer la session portail", error);
            });
        });

        useEffect(() => {
            this.state.canConfirm = this.canConfirm();
        }, () => [this.selectedVehicule, this.selectedCalque])

        useEffect(() => {
            if (this.vehicules.length === 0) {
                this.state.selectedVehicule = undefined;
            }
            else {
                this.onSelectVehicule(this.vehicules[0].id);
            }
        }, () => [this.vehicules])

        useEffect(() => {
            if (this.selectedVehicule) {
                const vehiculeId = this.selectedVehicule.id;
                this.runAsync(async () => {
                    // L1.1 — getVehiculeMeta() sélectionne un véhicule côté portail X'Glass.
                    // La session portail est globale : sérialiser cette sélection avec le
                    // chargement de la planche évite qu'une autre carte véhicule ne remplace
                    // l'état entre les deux appels.
                    await this.getVehiculeMeta(vehiculeId);
                    if (this.selectedVehicule?.id === vehiculeId) {
                        await this.getPlanche(vehiculeId);
                    }
                }, "Chargement du véhicule en cours...");
            }
            else {
                this.state.vehiculeMeta = undefined;
                this.state.planche = undefined;
            }
        }, () => [this.selectedVehicule])

        useEffect(() => {
            if (!this.planche) {
                this.state.calques = [];
            }
            else {
                // La planche a changé, on reset le calque sélectionné
                if (this.record.categorieXglass) {
                    const calque = this.calques.find(calque => calque.libelle === this.record.categorieXglass);
                    if (calque) {
                        this.onClickCalque(calque.id);
                    }
                }
                else {
                    this.state.selectedCalque = undefined;
                }
            }
        }, () => [this.planche])

        useEffect(() => {
            if (!this.selectedCalque) {
                this.state.pieces = [];
                this.clearSelectedPiece();
            }
            else {
                this.state.pieceConcernee = suggestPieceConcernee(this.selectedCalque.libelle);
                this.state.pieces = [];
                this.clearSelectedPiece();
                this.runAsync(() => this.getPieces(), "Chargement des pièces en cours...");
            }
        }, () => [this.selectedCalque])

        useEffect(() => {
            if (this.pieces.length === 0) {
                this.state.selectedPiece = undefined;
            }
            else {
                // this.onSelectPiece(this.pieces[0].id);
                if (this.selectedPiece) {
                    const piece = this.pieces.find(piece => piece.id === this.selectedPiece.id);
                    this.state.selectedPiece = piece;
                }
            }
        }, () => [this.pieces])

        useEffect(() => {
            if (this.selectedPiece) {
                this.runAsync(() => this.getSelectedPieceAm(), "Chargement des pièces compatibles en cours...");
            }
        }, () => [this.selectedPiece])

        useEffect(() => {
            if (this.selectedPieceAm) {
                const basePieceAm = this.selectedPieceAm.pieceAm;
                const reference = basePieceAm.reference
                this.state.baseEurocode = reference.substring(0, 5);
            }
            else {
                this.state.baseEurocode = undefined;
            }
        }, () => [this.selectedPieceAm])

        useEffect(() => {
            if (this.baseEurocode) {
                this.onSearchBaseEurocode();
            }
            // else {
            //     this.state.baseEurocode = undefined;
            // }
        }, () => [this.baseEurocode])

    }

    get agentsInitialized() {
        return this.state.agentsInitialized;
    }


    async onWillStart() {
        await this.runAsync(async () => {
            this.setLoadingMessage("Authentification des agents en cours...");
            await this.auth_agents();
            await this.init();
        });
    }

    async auth_agents() {
        await this.rpc("/rpbm_agent_auth")
        this.state.agentsInitialized = true;
    }

    async init() {
        if (this.state.immatriculationValue) {
            await this.searchImmatriculation();
        }
    }

    async closeAgents() {
        if (!this.agentsInitialized || this._agentLockReleased) {
            return;
        }
        this._agentLockReleased = true;
        try {
            await this.rpc("/rpbm_agent_close")
        }
        catch (error) {
            // Un nouvel essai reste possible depuis onWillUnmount ou le bouton
            // Annuler si la requête de fermeture a échoué.
            this._agentLockReleased = false;
            throw error;
        }
    }

    async createOdooVehicule() {
        const res = await this.rpc("/createVehicule", {
            immatriculation: this.state.immatriculationValue,
            partner_id: this.record.partnerId,
            vehicule_info: this.selectedVehicule,
            vehicule_meta: this.vehiculeMeta,
        })
        if (res) {
            return await this.getOdooVehicule();
        }
        return res;
    }

    async getRecordData() {
        const data = {};
        data[this.record.immatriculationField] = this.immatriculationValue;
        const OdooVehicule = await this.getOdooVehicule();

        if (OdooVehicule) {
            data[this.record.vehiculeField] = [OdooVehicule.id, OdooVehicule.name];
        }
        else if (this.selectedVehicule) {
            // Il y a un vehicule selectionné mais pas d'OdooVehicule encore créé
            const newOdooVehicule = await this.createOdooVehicule();
            data[this.record.vehiculeField] = [newOdooVehicule.id, newOdooVehicule.name];
        }

        if (this.selectedCalque) {
            data[this.record.categorieXglassField] = this.selectedCalque.libelle;
        }

        if (this.pieceConcernee) {
            data[this.record.pieceConcerneeField] = this.pieceConcernee;
        }

        if (this.baseEurocode) {
            data[this.record.baseEurocodeField] = this.baseEurocode;
        }
        return data;
    }

    /**
     * Reporte les valeurs dans le formulaire, puis les enregistre seulement
     * lorsque l'utilisateur le demande explicitement.
     *
     * @param {boolean} save sauvegarde via le mécanisme natif du formulaire
     */
    async confirmRecord(save = false) {
        // L1.0 — créer le véhicule / écrire les champs AVANT de fermer la session portail.
        // closeAgents() relâche le verrou de concurrence (les routes sont décorées
        // @_touch_agent_lock) ET déconnecte X'Glass ; or getRecordData() → createVehicule a
        // besoin des deux (le verrou, et la session vivante pour télécharger l'image véhicule).
        // L'ancien ordre (close puis write) faisait échouer createVehicule à chaque fois.
        // runAsync gère l'erreur (notification) : si getRecordData échoue, on NE ferme PAS —
        // la dialog reste ouverte pour réessai, le verrou est conservé.
        let done = false;
        await this.runAsync(async () => {
            const data = await this.getRecordData();
            await this.props.record.update(data);
            if (save) {
                // Record.save({ reload: false }) persiste sans navigation ni
                // rechargement du formulaire. Il applique la validation Odoo
                // habituelle, y compris les éventuels champs requis hors widget.
                const saved = await this.props.record.save({ reload: false });
                if (!saved) {
                    throw new Error("Le formulaire n'a pas pu être enregistré. Complétez les champs requis puis réessayez.");
                }
            }
            await this.closeAgents();
            done = true;
        }, "Enregistrement en cours...");
        // close() hors du runAsync : il détruit le composant, or runAsync met à jour l'état
        // (stopLoading) après le callback — fermer ici évite un update sur composant détruit.
        // On ne ferme que si tout a réussi ; sinon la dialog reste ouverte pour réessai.
        if (done) {
            this.props.close();
        }
    }

    async onConfirm() {
        await this.confirmRecord();
    }

    async onConfirmAndSave() {
        await this.confirmRecord(true);
    }

    async onDiscard() {
        await this.closeAgents();
        this.props.close();
    }

    get immatriculationValue() {
        return this.state.immatriculationValue;
    }

    onChangeImmatriculation(ev) {
        this.state.immatriculationValue = ev.target.value;
    }

    async searchImmatriculation() {
        this.setLoadingMessage("Recherche de l'immatriculation en cours...");
        if (!this.immatriculationValue) {
            this.state.vehicules = [];
            return;
        }
        const res = await this.rpc("/searchImmatriculation", {
            immatriculation: this.immatriculationValue,
        })
        this.state.vehicules = res;
    }

    async onSearchImmatriculation() {
        await this.runAsync(async () => {
            await this.searchImmatriculation();
        });
    }

    /**
     * @returns {Vehicule[]}
     */
    get vehicules() {
        return this.state.vehicules;
    }

    /**
     * @returns {Vehicule|undefined}
     */
    get selectedVehicule() {
        return this.state.selectedVehicule;
    }

    get selectedVehiculeId() {
        return this.selectedVehicule ? this.selectedVehicule.id : 0;
    }

    /** @returns {MetaPieceAM|undefined} */
    get selectedPieceAm() {
        return this.state.selectedPieceAm;
    }

    get selectedPieceAMId() {
        return this.selectedPieceAm ? this.selectedPieceAm.pieceAm.id : 0;
    }

    canConfirm() {
        return Boolean(this.selectedVehicule && this.selectedCalque);
    }

    onSelectVehicule(vehiculeId) {
        this.state.selectedVehicule = this.vehicules.find(vehicule => vehicule.id === vehiculeId);
    }

    /**
     * @returns {Promise<OdooVehicule|boolean>}
     */
    async getOdooVehicule() {
        if (!this.selectedVehicule) {
            return false;
        }
        return await this.rpc("/getOdooVehicule", {
            immatriculation: this.immatriculationValue,
            // vehicule: this.selectedVehicule,
        })
    }

    /**
     * @returns {VehiculeMeta|undefined}
     */
    get vehiculeMeta() {
        return this.state.vehiculeMeta;
    }

    async getVehiculeMeta(vehiculeId = this.selectedVehicule.id) {
        const res = await this.rpc("/rpbm_agent/getVehiculeMeta", {
            vehiculeId,
        });
        if (this.selectedVehicule?.id === vehiculeId) {
            this.state.vehiculeMeta = res;
        }
        return res;
    }



    async getPlanche(vehiculeId = this.selectedVehicule.id) {
        const res = await this.rpc("/getPlanche", {
            vehiculeId,
        })
        if (this.selectedVehicule?.id === vehiculeId) {
            this.state.planche = res;
        }
        return res;
    }

    /** @returns {Planche} */
    get planche() {
        return this.state.planche;
    }

    /** @returns {Calque[]} */
    get calques() {
        return this.planche.calques;
    }

    /** @returns {Calque|undefined} */
    get selectedCalque() {
        return this.state.selectedCalque;
    }

    /** @returns {number} */
    get selectedCalqueId() {
        return this.selectedCalque ? this.selectedCalque.id : 0;
    }

    /**
     * @returns {string} */
    get baseEurocode() {
        return this.state.baseEurocode;
    }

    onClickCalque(calqueId) {
        this.state.selectedCalque = this.calques.find(calque => calque.id === calqueId);
    }

    get pieces() {
        return this.state.pieces;
    }

    async getPieces() {
        const res = await this.rpc("/getPieces", {
            plancheId: this.planche.id,
            calqueId: this.selectedCalque.id,
        })
        this.state.pieces = res;
    }

    onSelectPiece(pieceId) {
        if (this.selectedPiece?.id === pieceId) {
            this.clearSelectedPiece();
            return;
        }
        this.clearSelectedPiece();
        this.state.selectedPiece = this.pieces.find(piece => piece.id === pieceId);
    }

    /**
     * Réinitialise les données dépendant de la pièce OE sélectionnée pour ne
     * pas afficher ou réutiliser les détails d'une sélection précédente.
     */
    clearSelectedPiece() {
        this.state.selectedPiece = undefined;
        this.state.selectedPieceAm = undefined;
        this.state.baseEurocode = undefined;
        this.state.articlesVsf = [];
        this.resetVsfSelection();
        this._lastSearchedBaseEurocode = undefined;
    }

    get selectedPiece() {
        return this.state.selectedPiece;
    }

    get selectedPieceId() {
        return this.selectedPiece ? this.selectedPiece.id : 0;
    }

    async getSelectedPieceAm() {
        if (this.selectedPiece) {
            const res = await this.getPieceAm(this.selectedPiece);
            // if (res.length > 0) {
            //     const basePieceAm = res[0].pieceAm;
            //     const reference = basePieceAm.reference;
            //     this.state.baseEurocode = reference.substring(0, 5);
            //     this.onSearchBaseEurocode();
            // }
        }
    }

    async getPieceAm(piece) {
        const res = await this.rpc("/getPieceAm", {
            element_withPiecesAm: piece['element.withPiecesAm'],
            pieceId: piece.id,
            elementSitId: piece.elementSitId,
        })
        piece.PiecesAM = res;
        // La propriété est enrichie en place : réassigner le tableau garantit
        // que OWL rerend aussi les pièces après-marché nouvellement reçues.
        this.state.pieces = [...this.pieces];
        return res;
    }

    onSelectPieceAM(pieceAmId) {
        if (this.selectedPiece && this.selectedPiece.PiecesAM) {
            this.state.selectedPieceAm = this.selectedPiece.PiecesAM.find(metaPieceAM => metaPieceAM.pieceAm.id === pieceAmId);
        }
    }

    onChangeBaseEurocode(ev) {
        this.state.baseEurocode = ev.target.value;
    }

    get articlesVsf() {
        return this.state.articlesVsf;
    }

    async searchBaseEurocode() {
        const baseEurocode = (this.baseEurocode || "").trim();
        if (!baseEurocode) {
            this.state.articlesVsf = [];
            this.resetVsfSelection();
            this._lastSearchedBaseEurocode = undefined;
            return;
        }
        if (baseEurocode === this._lastSearchedBaseEurocode) {
            return;
        }
        this._lastSearchedBaseEurocode = baseEurocode;
        try {
            const res = await this.rpc("/searchBaseEurocode", {
                baseEurocode,
            });
            this.state.articlesVsf = res;
            this.resetVsfSelection();
        } catch (error) {
            this._lastSearchedBaseEurocode = undefined;
            throw error;
        }
    }

    onSearchBaseEurocode() {
        this.runAsync(() => this.searchBaseEurocode(), "Recherche des articles VSF en cours...");
    }

    resetVsfSelection() {
        this.state.selectedArticleCodes = {};
        this.state.articleProducts = {};
        this.state.articleLoadingCodes = {};
    }

    isArticleSelected(articleCode) {
        return Boolean(this.state.selectedArticleCodes[articleCode]);
    }

    isArticleLoading(articleCode) {
        return Boolean(this.state.articleLoadingCodes[articleCode]);
    }

    getArticleByCode(articleCode) {
        for (const article of this.articlesVsf) {
            if (article.code === articleCode) {
                return article;
            }
            const suggestion = (article.suggestedArticles || []).find(
                candidate => candidate.code === articleCode
            );
            if (suggestion) {
                return suggestion;
            }
        }
        return undefined;
    }

    replaceArticle(articleCode, details) {
        this.state.articlesVsf = this.articlesVsf.map((article) => {
            if (article.code === articleCode) {
                return details;
            }
            const suggestions = article.suggestedArticles || [];
            if (!suggestions.some(candidate => candidate.code === articleCode)) {
                return article;
            }
            return {
                ...article,
                suggestedArticles: suggestions.map((candidate) =>
                    candidate.code === articleCode ? details : candidate
                ),
            };
        });
    }

    getProductForArticle(articleCode) {
        return this.state.articleProducts[articleCode];
    }

    productOdooUrl(product) {
        return product
            ? `/web#id=${product.id}&view_type=form&model=product.product&action=product.product_template_action`
            : undefined;
    }

    productMatchLabel(product) {
        const labels = {
            reference_interne: "référence interne",
            eurocode: "eurocode",
            nom: "nom",
            créé: "créé à l'instant",
        };
        return labels[product?.matched_by] || "correspondance confirmée";
    }

    get pieceConcerneeOptions() {
        return PIECE_CONCERNEE_OPTIONS;
    }

    get pieceConcernee() {
        return this.state.pieceConcernee;
    }

    onChangePieceConcernee(event) {
        this.state.pieceConcernee = event.target.value;
    }

    async onClickArticleVsf(articleCode) {
        await this.toggleVsfArticle(articleCode);
    }

    async onClickSuggestedArticle(articleCode, parentArticleCode) {
        await this.toggleVsfArticle(articleCode, parentArticleCode);
    }

    deselectArticles(articleCodes) {
        const selectedArticleCodes = { ...this.state.selectedArticleCodes };
        const articleProducts = { ...this.state.articleProducts };
        const articleLoadingCodes = { ...this.state.articleLoadingCodes };
        for (const code of articleCodes) {
            delete selectedArticleCodes[code];
            delete articleProducts[code];
            delete articleLoadingCodes[code];
        }
        this.state.selectedArticleCodes = selectedArticleCodes;
        this.state.articleProducts = articleProducts;
        this.state.articleLoadingCodes = articleLoadingCodes;
    }

    async toggleVsfArticle(articleCode, parentArticleCode = undefined) {
        const article = this.getArticleByCode(articleCode);
        if (!article?.code) {
            return;
        }
        if (this.isArticleSelected(articleCode)) {
            const codesToDeselect = [articleCode];
            if (!parentArticleCode) {
                codesToDeselect.push(
                    ...(article.suggestedArticles || []).map(suggestion => suggestion.code)
                );
            }
            this.deselectArticles(codesToDeselect);
            return;
        }
        this.state.selectedArticleCodes = {
            ...this.state.selectedArticleCodes,
            [articleCode]: true,
        };
        if (article.detailsLoaded) {
            await this.findProductForArticle(article);
        } else {
            await this.loadArticleDetails(article, !parentArticleCode);
        }
    }

    async loadArticleDetails(article, enrichSuggestions) {
        const articleCode = article.code;
        this.state.articleLoadingCodes = {
            ...this.state.articleLoadingCodes,
            [articleCode]: true,
        };
        await this.runAsync(async () => {
            const details = await this.rpc("/getVsfArticleDetails", {
                articleVsfInfo: article,
                enrichSuggestions,
            });
            if (!this.isArticleSelected(articleCode)) {
                return;
            }
            this.replaceArticle(articleCode, details);
            await this.findProductForArticle(details);
        }, "Chargement de la fiche article VSF en cours...");
        const loadingCodes = { ...this.state.articleLoadingCodes };
        delete loadingCodes[articleCode];
        this.state.articleLoadingCodes = loadingCodes;
    }

    async findProductForArticle(article) {
        if (!article?.code) {
            return;
        }
        const product = await this.rpc("/doesProductExists", {
            articleVsfInfo: article,
        });
        if (this.isArticleSelected(article.code)) {
            this.state.articleProducts = {
                ...this.state.articleProducts,
                [article.code]: product || undefined,
            };
        }
    }

    async createProductForArticle(articleCode) {
        const article = this.getArticleByCode(articleCode);
        if (!article) {
            return;
        }
        await this.runAsync(async () => {
            const product = await this.rpc("/createProduct", {
                articleVsfInfo: article,
            });
            if (this.isArticleSelected(articleCode)) {
                this.state.articleProducts = {
                    ...this.state.articleProducts,
                    [articleCode]: product,
                };
            }
        }, "Création du produit en cours...");
    }

    openImagePreview(imageUrl) {
        if (imageUrl) {
            this.dialog.add(VsfImagePreviewDialog, { imageUrl });
        }
    }

}
