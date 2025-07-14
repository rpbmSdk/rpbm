/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { useState, Component } from "@odoo/owl";
import { Dialog } from '@web/core/dialog/dialog';
import { onWillStart, useRef, useEffect } from "@odoo/owl";

import { asyncWidget, AbstractWidgetRecord } from "./utils";
import { VehiculeComponent } from "./VehiculeComponent";
import { CalqueComponent } from "./CalqueComponent";
import { PieceComponent } from "./PieceComponent";
import { ArticleComponent } from "./ArticleComponent";


/**
 * @typedef {import('./types').Vehicule}
 * @typedef {import('./types').Planche}
 * @typedef {import('./types').Calque}
 * @typedef {import('./types').OdooVehicule}
 * @typedef 
 */

export class AgentWidgetDialog extends asyncWidget {
    static components = {
        Dialog,
        VehiculeComponent,
        CalqueComponent,
        PieceComponent,
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
        this.orm = useService("orm");
        /** @type {AbstractWidgetRecord} */
        this.record = new AbstractWidgetRecord(this.props.record);
        this.state = useState({
            ...this.state,
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
            selectedArticleVsf: undefined,
        });

    }

    get agentsInitialized() {
        return this.state.agentsInitialized;
    }


    async onWillStart() {
        // this.toogleLoading();
        this.runAsync(async () => {
            this.setLoadingMessage("Authentification des agents en cours...");
            await this.auth_agents();
            this.state.agentsInitialized = true;
            await this.init();
        })
        // this.toogleLoading();
    }

    async auth_agents() {
        await this.rpc("/rpbm_agent_auth")
    }

    async loadFromRecord() {
        if (this.state.immatriculationValue) {
            await this.onSearchImmatriculation()
            if (this.vehicules.length > 0) {
                this.onSelectVehicule(this.vehicules[0].id)
                await this.getPlanche()
                // this.calques.forEach(calque => console.log(calque.libelle))
            }
        }
    }

    async init() {
        // console.log("override me");
        this.runAsync(async () => {
            if (this.state.immatriculationValue) {
                await this.searchImmatriculation()
                if (this.vehicules.length > 0) {
                    this.onSelectVehicule(this.vehicules[0].id)
                    await this.getPlanche()
                    if (this.record.categorieXglass) {
                        const calque = this.calques.find(calque => calque.libelle === this.record.categorieXglass);
                        if (calque) {
                            this.onClickCalque(calque.id);
                        }
                    }
                    this.calques.forEach(calque => console.log(calque.libelle))
                }
            }
        })
    }

    // toogleLoading() {
    //     this.state.loading = !this.state.loading;
    // }

    async closeAgents() {
        await this.rpc("/rpbm_agent_close")
    }

    async onConfirm() {
        await this.closeAgents();

        const data = {};
        data[this.record.immatriculationField] = this.immatriculationValue;
        const OdooVehicule = await this.getOdooVehicule();
        if (OdooVehicule) {
            data[this.record.vehiculeField] = OdooVehicule.id;
        }

        if (this.selectedCalque) {
            data[this.record.categorieXglassField] = this.selectedCalque.libelle;
        }

        if (this.baseEurocode) {
            data[this.record.baseEurocodeField] = this.baseEurocode;
        }
        this.props.record.update(data);
        this.props.close();
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
        console.log(this.immatriculationValue);
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
        console.log(res);
        this.state.vehicules = res;
    }

    async onSearchImmatriculation() {
        this.runAsync(async () => {
            await this.searchImmatriculation();
        })
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

    onSelectVehicule(vehiculeId) {
        this.state.selectedVehicule = this.vehicules.find(vehicule => vehicule.id === vehiculeId);
        console.log(this.state.selectedVehicule);
    }

    /**
     * @returns {Promise<OdooVehicule|boolean>}
     */
    async getOdooVehicule() {
        console.log("getOdooVehicule");
        if (!this.selectedVehicule) {
            return false;
        }
        return await this.rpc("/getOdooVehicule", {
            immatriculation: this.immatriculationValue,
            // vehicule: this.selectedVehicule,
        })
    }

    /**
     * @returns {VehiculeMeta}
     * */
    get vehiculeMeta() {
        return this.state.vehiculeMeta;
    }

    async getVehiculeMeta() {
        const res = await this.rpc("/rbm_agent/getVehiculeMeta", {
            vehiculeId: this.selectedVehicule.id,
        })
        console.log(res);
        this.state.vehiculeMeta = res;
        return res;
    }



    async getPlanche() {
        await this.getVehiculeMeta();
        const res = await this.rpc("/getPlanche", {
            vehiculeId: this.selectedVehicule.id,
        })
        console.log(res);
        this.state.planche = res;
        this.calques.forEach(calque => console.log(calque.libelle))
        return res;
    }

    onGetPlanche() {
        this.runAsync(async () => {
            this.setLoadingMessage("Chargement de la planche en cours...");
            await this.getPlanche();
        })
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

    onChangeCalque(ev) {
        const calqueId = parseInt(ev.target.value);
        this.state.selectedCalque = this.calques.find(calque => calque.id === calqueId);
        console.log(this.selectedCalque);
    }
    onClickCalque(calqueId) {
        this.state.selectedCalque = this.calques.find(calque => calque.id === calqueId);
        console.log(this.selectedCalque);
        this.getPieces();
    }

    get pieces() {
        return this.state.pieces;
    }

    async getPieces() {
        const res = await this.rpc("/getPieces", {
            plancheId: this.planche.id,
            calqueId: this.selectedCalque.id,
        })
        console.log(res);
        this.state.pieces = res;
        // return res;
    }

    onSelectPiece(pieceId) {
        this.state.selectedPiece = this.pieces.find(vehicule => vehicule.id === pieceId);
        console.log(this.state.selectedPiece);
        this.getPieceAm();
    }

    get selectedPiece() {
        return this.state.selectedPiece;
    }

    get selectedPieceId() {
        return this.selectedPiece ? this.selectedPiece.id : 0;
    }

    async getPieceAm() {
        const res = await this.rpc("/getPieceAm", {
            element_withPiecesAm: this.selectedPiece['element.withPiecesAm'],
            pieceId: this.selectedPiece.id,
            elementSitId: this.selectedPiece.elementSitId,
        })
        console.log(res);
        if (res.length > 0) {
            const basePieceAm = res[0].pieceAm;
            const reference = basePieceAm.reference;
            this.state.baseEurocode = reference.substring(0, 5);
            this.onSearchBaseEurocode();
        }
        // this.state.piecesAm = res;
    }

    onChangeBaseEurocode(ev) {
        this.state.baseEurocode = ev.target.value;
        console.log(this.baseEurocode);
    }

    get baseEurocode() {
        return this.state.baseEurocode
    }

    get articlesVsf() {
        return this.state.articlesVsf;
    }

    async onSearchBaseEurocode() {
        const res = await this.rpc("/searchBaseEurocode", {
            baseEurocode: this.baseEurocode,
        })
        console.log(res);
        this.state.articlesVsf = res;
        // if (this.articlesVsf.length > 0) {
        //     const baseEurocode = this.articlesVsf[0].baseEurocode;
        // }
        // this.state.piecesAm = res;
    }

    get selectedArticleVsf() {
        return this.state.selectedArticleVsf;
    }

    onClickArticleVsf(articleId) {
        this.state.selectedArticleVsf = this.articlesVsf.find(article => article.id === articleId);
        console.log(this.selectedArticleVsf);
    }

    get selectedArticleId() {
        return this.selectedArticleVsf ? this.selectedArticleVsf.id : 0;
    }

}