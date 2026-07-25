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
import { PieceAMComponent } from "./PieceAMComponent";

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
        this.orm = useService("orm");
        /** @type {AbstractWidgetRecord} */
        this.record = new AbstractWidgetRecord(this.props.record);
        this.state = useState({
            ...this.state,
            canConfim: false,
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

        useEffect(() => {
            this.state.canConfim = this.canConfirm();
        }, () => [this.selectedVehicule, this.planche, this.selectedCalque, this.baseEurocode])

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
            }
            else {
                this.getPieces();
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
                    if (piece) {
                        this.onSelectPiece(piece.id);
                    }
                    else {
                        this.state.selectedPiece = undefined;
                    }
                }
            }
        }, () => [this.pieces])

        useEffect(() => {
            this.getSelectedPieceAm();
        }, () => [this.selectedPiece])

        useEffect(() => {
            if (this.selectedPieceAm) {
                const basePieceAm = this.selectedPieceAm.pieceAm;
                const reference = basePieceAm.reference
                this.state.baseEurocode = reference.substring(0, 5);
            }
            else {
                this.state.pieceAm = undefined;
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
        // this.toogleLoading();
        this.runAsync(async () => {
            this.setLoadingMessage("Authentification des agents en cours...");
            await this.auth_agents();
            await this.init();
        })
    }

    async auth_agents() {
        await this.rpc("/rpbm_agent_auth")
        this.state.agentsInitialized = true;
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
                // if (this.record.categorieXglass) {
                //         const calque = this.calques.find(calque => calque.libelle === this.record.categorieXglass);
                //         if (calque) {
                //             this.onClickCalque(calque.id);
                //         }
                //     }
            }
        })
    }

    // toogleLoading() {
    //     this.state.loading = !this.state.loading;
    // }

    async closeAgents() {
        await this.rpc("/rpbm_agent_close")
    }

    async createOdooVehicule() {
        const res = await this.rpc("/createVehicule", {
            immatriculation: this.state.immatriculationValue,
            partner_id: this.record.partnerId,
            vehicule_info: this.selectedVehicule,
            vehicule_meta: this.vehiculeMeta,
        })
        console.log(res);
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

    /** @returns {MetaPieceAM|undefined} */
    get selectedPieceAm() {
        return this.state.selectedPieceAm;
    }

    get selectedPieceAMId() {
        return this.selectedPieceAm ? this.selectedPieceAm.pieceAm.id : 0;
    }

    canConfirm() {
        if (!this.selectedVehicule) {
            return false;
        }
        return true;
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
     * @returns {VehiculeMeta|undefined}
     */
    get vehiculeMeta() {
        return this.state.vehiculeMeta;
    }

    async getVehiculeMeta(vehiculeId = this.selectedVehicule.id) {
        const res = await this.rpc("/rbm_agent/getVehiculeMeta", {
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
        // console.log(this.selectedCalque);
    }
    onClickCalque(calqueId) {
        this.state.selectedCalque = this.calques.find(calque => calque.id === calqueId);
        // console.log(this.selectedCalque);
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
        // console.log(res);
        this.state.pieces = res;
        // return res;
    }

    onSelectPiece(pieceId) {
        this.state.selectedPiece = this.pieces.find(piece => piece.id === pieceId);
        // console.log(this.state.selectedPiece);
        // this.getSelectedPieceAm();
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
        // this.state.pi
        piece.PiecesAM = res;
        return res;
        console.log(res);
        if (res.length > 0) {
            const basePieceAm = res[0].pieceAm;
            const reference = basePieceAm.reference;
            this.state.baseEurocode = reference.substring(0, 5);
            this.onSearchBaseEurocode();
        }
        // this.state.piecesAm = res;
    }

    onSelectPieceAM(pieceAmId) {
        if (this.selectedPiece && this.selectedPiece.PiecesAM) {
            this.state.selectedPieceAm = this.selectedPiece.PiecesAM.find(metaPieceAM => metaPieceAM.pieceAm.id === pieceAmId);
            console.log(this.state.selectedPieceAm);
        }
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
