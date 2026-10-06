/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { onWillStart, onWillUnmount, useEffect, useState } from "@odoo/owl";
import { Dialog } from '@web/core/dialog/dialog';

import {
    asyncWidget,
    AbstractWidgetRecord,
    PART_TYPES,
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

// Libellés X'Glass `pieceElementFilter.tit.filtre.*` (controllers/xglass_lbl.py).
const PIECE_GROUP_TITLES = {
    ELEMENTSIT_PRINCIPAUX: "Pièces principales",
    ELEMENTSIT_COMPLEMENTAIRES: "Pièces complémentaires",
};

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
        this.dialog = useService("dialog");
        /** @type {AbstractWidgetRecord} */
        this.record = new AbstractWidgetRecord(this.props.record);
        this.state = useState({
            ...this.state,
            canConfirm: false,
            writing: false,
            agentsInitialized: false,
            authError: "",
            isReconnecting: false,
            reconnectRequired: false,
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
            // Encarts « AUTRE AM » (R11) : liste et dépliage par véhicule + famille X'Glass.
            autresAm: {},
            autresAmOpen: {},
            baseEurocode: undefined,
            baseEurocodeInput: undefined,
            articlesVsf: [],
            // Base de la dernière recherche VSF aboutie sans article (R24).
            vsfNoResultFor: undefined,
            selectedArticleCodes: {},
            primaryArticleCode: undefined,
            articleProducts: {},
            articleLoadingCodes: {},
            pieceConcernee: undefined,
            showAllCalques: false,
            showAllPieces: false,
        });
        this._restorePending = false;
        this._agentLockReleased = false;
        this._lastSearchedBaseEurocode = undefined;
        this._reconnectPromise = undefined;
        // Immatriculation de la dernière recherche aboutie, rejouée après une reconnexion.
        this._searchedImmatriculation = undefined;
        this.state.immatriculationValue = this.record.immatriculation || "";
        this.restoreSelectionFromRecord();

        onWillStart(() => this.onWillStart());

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
                const restored = this.vehicules.find(vehicule => String(vehicule.id) === this._restoreVehiculeId);
                this.onSelectVehicule((restored || this.vehicules[0]).id);
            }
        }, () => [this.vehicules])

        useEffect(() => {
            if (this.selectedVehicule) {
                const vehiculeId = this.selectedVehicule.id;
                // L1.1 — un seul appel sélectionne le véhicule côté portail X'Glass
                // (session globale) et ramène métadonnées et planche ensemble.
                this.runAsync(() => this.getVehiculeMeta(vehiculeId), "Chargement du véhicule en cours...");
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
                        this.state.selectedCalque = calque;
                        this.state.showAllCalques = false;
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
                // Au montage aucun calque n'est encore choisi : sans ce drapeau, la base
                // Eurocode restaurée était effacée avant d'être affichée (R12).
                this.clearSelectedPiece(this._restorePending);
            }
            else {
                if (!this._restorePending || !this.pieceConcernee) {
                    this.state.pieceConcernee = suggestPieceConcernee(this.selectedCalque.libelle);
                }
                this.state.pieces = [];
                this.clearSelectedPiece(this._restorePending);
                this.runAsync(() => this.getPieces(), "Chargement des pièces en cours...");
            }
        }, () => [this.selectedCalque])

        useEffect(() => {
            if (this.pieces.length === 0) {
                this.state.selectedPiece = undefined;
            }
            else {
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

        // Une ligne « Autres marques AM » choisie sans pièce OE lance aussi la recherche ; une base
        // restaurée seule, non (R12). Dépendre de la présence d'une sélection, pas de l'objet :
        // la pièce AM restaurée après la pièce OE relancerait une recherche déjà en cours.
        useEffect(() => {
            if (this.agentsInitialized && (this.selectedPiece || this.selectedPieceAm) && this.baseEurocode) {
                this.onSearchBaseEurocode();
            }
        }, () => [this.baseEurocode, Boolean(this.selectedPiece || this.selectedPieceAm), this.agentsInitialized])

    }

    get agentsInitialized() {
        return this.state.agentsInitialized;
    }

    get isReconnecting() {
        return this.state.isReconnecting;
    }

    get reconnectRequired() {
        return this.state.reconnectRequired;
    }


    async onWillStart() {
        await this.startAgents();
    }

    async startAgents() {
        // Sans état d'erreur, un refus de portail laissait le spinner « Authentification des
        // agents en cours... » indéfiniment (recette 2026-09-20, portail VSF indisponible).
        this.state.authError = "";
        await this.runAsync(async () => {
            this.setLoadingMessage("Authentification des agents en cours...");
            try {
                await this.auth_agents();
            } catch (error) {
                this.state.authError = error.data?.message || error.message || "Une erreur est survenue";
                throw error;
            }
            await this.init();
        });
    }

    get authError() {
        return this.state.authError;
    }

    async auth_agents() {
        await this.rpc("/rpbm_agent_auth");
        this.state.agentsInitialized = true;
        this.state.reconnectRequired = false;
        this._agentLockReleased = false;
    }

    isSessionExpiredError(error) {
        const errorName = error?.data?.name || "";
        return errorName === "AgentSessionExpiredError"
            || errorName.endsWith(".AgentSessionExpiredError");
    }

    async restorePortalContext() {
        if (!this.selectedVehicule) {
            return;
        }
        // X'Glass garde le véhicule sélectionné côté serveur. Réchauffer cette
        // sélection après le login sans réassigner la planche dans l'état Owl :
        // toutes les données déjà visibles restent ainsi intactes.
        // Traces du 2026-10-02 : dans une session neuve, selectVehicule sans recherche préalable
        // échoue sans erreur (planche vide, pièces AM sans contexte véhicule). Rejouer la recherche
        // faite rend aussi VIN, CNIT et date de MEC à la session ; la page des pièces est inutile.
        await this.rpc("/searchImmatriculation", { immatriculation: this._searchedImmatriculation });
        await this.rpc("/getPlanche", { vehiculeId: this.selectedVehicule.id });
    }

    async reconnectAgents() {
        if (this._reconnectPromise) {
            return this._reconnectPromise;
        }
        this._reconnectPromise = (async () => {
            this.state.isReconnecting = true;
            this.state.reconnectRequired = false;
            this.setLoadingMessage("Reconnexion aux portails en cours...");
            try {
                await this.auth_agents();
                await this.restorePortalContext();
                // Aucune liste « AUTRE AM » obtenue avant ou pendant la reconnexion ne survit ;
                // les encarts se replient pour ne pas rester ouverts sur une liste absente.
                this.state.autresAm = {};
                this.state.autresAmOpen = {};
            } catch (error) {
                this.state.reconnectRequired = true;
                throw error;
            } finally {
                this.state.isReconnecting = false;
            }
        })();
        try {
            return await this._reconnectPromise;
        } finally {
            this._reconnectPromise = undefined;
        }
    }

    async callPortal(route, params = {}) {
        try {
            return await this.rpc(route, params);
        } catch (error) {
            if (!this.isSessionExpiredError(error)) {
                throw error;
            }
        }
        await this.reconnectAgents();
        try {
            return await this.rpc(route, params);
        } catch (error) {
            if (this.isSessionExpiredError(error)) {
                this.state.reconnectRequired = true;
            }
            throw error;
        }
    }

    async onReconnect() {
        await this.runAsync(
            () => this.reconnectAgents(),
            "Reconnexion aux portails en cours..."
        );
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

    /** @returns {Promise<OdooVehicule>} */
    async createOdooVehicule() {
        return await this.rpc("/createVehicule", {
            immatriculation: this.state.immatriculationValue,
            partner_id: this.record.partnerId,
            vehicule_info: this.selectedVehicule,
            vehicule_meta: this.vehiculeMeta,
        });
    }

    async getRecordData() {
        const data = {};
        data[this.record.immatriculationField] = this.immatriculationValue;
        const vehicleMeta = this.vehiculeMeta || (
            this.selectedVehicule
                ? await this.getVehiculeMeta(this.selectedVehicule.id)
                : undefined
        );
        const OdooVehicule = await this.getOdooVehicule();

        if (OdooVehicule) {
            data[this.record.vehiculeField] = [OdooVehicule.id, OdooVehicule.name];
            await this.enrichOdooVehicule(OdooVehicule.id, vehicleMeta);
        }
        else if (this.selectedVehicule) {
            // Il y a un vehicule selectionné mais pas d'OdooVehicule encore créé
            const newOdooVehicule = await this.createOdooVehicule();
            data[this.record.vehiculeField] = [newOdooVehicule.id, newOdooVehicule.name];
        }

        // Marque, modèle, VIN, énergie, détail et date MEC sont dérivés du véhicule côté
        // serveur (compute) et recopiés vers les champs Studio historiques par le module.
        if (this.selectedCalque) {
            data[this.record.categorieXglassField] = this.selectedCalque.libelle;
        }

        if (this.pieceConcernee) {
            data[this.record.pieceConcerneeField] = this.pieceConcernee;
        }

        if (this.record.baseEurocodeField) {
            data[this.record.baseEurocodeField] = this.baseEurocode || "";
        }
        if (this.record.xglassVehicleIdField) {
            data[this.record.xglassVehicleIdField] = this.selectedVehicule ? String(this.selectedVehicule.id) : "";
        }
        // Lot E1.1 : une pièce mémorisée ni retrouvée ni changée par l'utilisateur reste intacte,
        // même si les pièces sont encore en chargement.
        if (this.record.xglassPieceIdField && !this._keepStoredPiece) {
            data[this.record.xglassPieceIdField] = this.selectedPiece ? String(this.selectedPiece.id) : "";
        }
        if (this.record.pieceOeIdField && !this._keepStoredPiece) {
            data[this.record.pieceOeIdField] = this.selectedPiece?.pieceOe?.id ? String(this.selectedPiece.pieceOe.id) : "";
        }
        if (this.record.pieceAmIdField && !this._keepStoredPieceAm) {
            data[this.record.pieceAmIdField] = this.selectedPieceAm?.pieceAm?.id ? String(this.selectedPieceAm.pieceAm.id) : "";
        }
        const primaryArticle = this.getPrimaryArticle();
        if (primaryArticle) {
            if (this.record.fullEurocodeField) {
                data[this.record.fullEurocodeField] = primaryArticle.code;
            }
            if (this.record.vsfDesignationField) {
                data[this.record.vsfDesignationField] = primaryArticle.name;
            }
            if (this.record.vsfStockField) {
                data[this.record.vsfStockField] = Number.parseInt(primaryArticle.stock, 10) || 0;
            }
            if (this.record.constructorReferenceField && primaryArticle.refConstructeur) {
                data[this.record.constructorReferenceField] = primaryArticle.refConstructeur;
            }
        }
        return data;
    }

    /**
     * Reporte les valeurs dans le formulaire, puis les enregistre seulement
     * lorsque l'utilisateur le demande explicitement.
     *
     * @param {boolean} save sauvegarde via le mécanisme natif du formulaire
     * @returns {Promise<boolean>} true si tout a réussi
     */
    async writeRecord(save = false) {
        // Anti-doublon : un double clic arrive avant le rendu qui désactive les boutons.
        if (this.state.writing) {
            return false;
        }
        this.state.writing = true;
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
                // Record.save() persiste sans navigation et applique la validation Odoo
                // habituelle. Pas de { reload: false } : les lignes créées gardaient leur
                // id virtuel, et les retirer ensuite envoyait DELETE 'virtual_…' au serveur
                // (erreur SQL sur sale_order_line, staging 2026-09-28).
                const saved = await this.props.record.save();
                if (!saved) {
                    throw new Error("Le formulaire n'a pas pu être enregistré. Complétez les champs requis puis réessayez.");
                }
            }
            await this.closeAgents();
            done = true;
        }, "Enregistrement en cours...");
        this.state.writing = false;
        return done;
    }

    async confirmRecord(save = false) {
        // close() hors du runAsync : il détruit le composant, or runAsync met à jour l'état
        // (stopLoading) après le callback — fermer ici évite un update sur composant détruit.
        // On ne ferme que si tout a réussi ; sinon la dialog reste ouverte pour réessai.
        if (await this.writeRecord(save)) {
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
        // Le champ peut changer après la recherche : on garde la valeur réellement recherchée.
        const immatriculation = this.immatriculationValue;
        const res = await this.callPortal("/searchImmatriculation", { immatriculation });
        this._searchedImmatriculation = immatriculation;
        this.state.vehicules = res;
    }

    async onSearchImmatriculation() {
        await this.runAsync(async () => {
            await this.searchImmatriculation();
            this.releaseStoredPieces();
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

    /** Clic sur une carte ; l'effet sur `vehicules` appelle onSelectVehicule sans passer par ici. */
    onClickVehicule(vehiculeId) {
        if (vehiculeId !== this.selectedVehiculeId) {
            this.releaseStoredPieces();
        }
        this.onSelectVehicule(vehiculeId);
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
        })
    }

    async enrichOdooVehicule(vehicleId, vehicleMeta = this.vehiculeMeta) {
        if (!vehicleId || !vehicleMeta) {
            return;
        }
        const result = await this.rpc("/enrichVehicule", {
            vehicle_id: vehicleId,
            vehicule_meta: vehicleMeta,
        });
        for (const warning of result?.warnings || []) {
            this.notification.add(warning, { type: "warning" });
        }
    }

    /**
     * @returns {VehiculeMeta|undefined}
     */
    get vehiculeMeta() {
        return this.state.vehiculeMeta;
    }

    /**
     * Sélectionne le véhicule côté portail et charge ses métadonnées et sa planche.
     * @returns {Promise<VehiculeMeta>}
     */
    async getVehiculeMeta(vehiculeId = this.selectedVehicule.id) {
        const { meta, planche } = await this.callPortal("/rpbm_agent/getVehiculeMeta", {
            vehiculeId,
        });
        if (this.selectedVehicule?.id === vehiculeId) {
            this.state.vehiculeMeta = meta;
            this.state.planche = planche;
        }
        return meta;
    }

    /** @returns {Planche} */
    get planche() {
        return this.state.planche;
    }

    /** @returns {Calque[]} */
    get calques() {
        return this.planche.calques;
    }

    get visibleCalques() {
        return this.selectedCalque && !this.state.showAllCalques ? [this.selectedCalque] : this.calques;
    }

    get showAllCalques() {
        return this.state.showAllCalques;
    }

    showOtherCalques() {
        this.state.showAllCalques = true;
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

    get baseEurocodeInput() {
        return this.state.baseEurocodeInput || "";
    }

    get vsfSearchUrl() {
        const baseEurocode = this.baseEurocodeInput;
        return baseEurocode.trim()
            ? `https://client.myvsf.fr/catalogue/vitrage?search=${encodeURIComponent(baseEurocode)}`
            : undefined;
    }

    setBaseEurocode(baseEurocode) {
        this.state.baseEurocode = baseEurocode;
        this.state.baseEurocodeInput = baseEurocode;
    }

    onClickCalque(calqueId) {
        if (calqueId !== this.selectedCalqueId) {
            this.releaseStoredPieces();
        }
        this.state.selectedCalque = this.calques.find(calque => calque.id === calqueId);
        this.state.showAllCalques = false;
        this.state.showAllPieces = false;
        this._restorePending = false;
    }

    get pieces() {
        return this.state.pieces;
    }

    get visiblePieces() {
        if (!this.state.showAllPieces && this.hasRestoredPieceContext && !this.selectedPiece) {
            return [];
        }
        return this.selectedPiece && !this.state.showAllPieces ? [this.selectedPiece] : this.pieces;
    }

    /**
     * Pièces groupées comme sur X'Glass : principales puis complémentaires, et dans chaque groupe
     * par famille (elementSitId), dans l'ordre reçu du portail. Calculé sur toutes les pièces :
     * visiblePieces est vide dans un contexte restauré sans pièce, où les familles restent utiles.
     */
    get pieceGroups() {
        const groups = new Map();
        for (const piece of this.pieces) {
            const key = piece.elementKey || "";
            if (!groups.has(key)) {
                groups.set(key, { key, titre: PIECE_GROUP_TITLES[key] || "Pièces", familles: new Map() });
            }
            const familles = groups.get(key).familles;
            if (!familles.has(piece.elementSitId)) {
                familles.set(piece.elementSitId, {
                    elementSitId: piece.elementSitId,
                    libelle: piece.elementSitLibelle || "",
                    withPiecesAm: piece["element.withPiecesAm"],
                    pieces: [],
                });
            }
            familles.get(piece.elementSitId).pieces.push(piece);
        }
        return [...groups.values()].map(group => ({ ...group, familles: [...group.familles.values()] }));
    }

    /** En mode focalisé, seule la famille de la pièce sélectionnée reste affichée. */
    get visiblePieceGroups() {
        const pieceId = this.state.showAllPieces ? 0 : this.selectedPieceId;
        if (!pieceId) {
            return this.pieceGroups;
        }
        return this.pieceGroups
            .map(group => ({
                ...group,
                familles: group.familles.filter(famille => famille.pieces.some(piece => piece.id === pieceId)),
            }))
            .filter(group => group.familles.length);
    }

    visibleFamillePieces(famille) {
        const visibleIds = new Set(this.visiblePieces.map(piece => piece.id));
        return famille.pieces.filter(piece => visibleIds.has(piece.id));
    }

    get hasRestoredPieceContext() {
        return Boolean(
            this._restorePending
            && (this._restorePieceId || this._restorePieceOeId || this._restorePieceAmId || this._restoreBaseEurocode)
        );
    }

    /** Une ligne « Autres marques AM » suffit à ouvrir la recherche VSF, même sans pièce OE. */
    get showVsfSection() {
        return Boolean(this.selectedPiece || this.selectedPieceAm || this.hasRestoredPieceContext);
    }

    get showAllPieces() {
        return this.state.showAllPieces;
    }

    showOtherPieces() {
        this.state.showAllPieces = true;
    }

    async getPieces() {
        const res = await this.callPortal("/getPieces", {
            plancheId: this.planche.id,
            calqueId: this.selectedCalque.id,
        })
        this.state.pieces = res;
        if (this._restorePieceId || this._restorePieceOeId) {
            const restoredPiece = this.pieces.find(piece =>
                String(piece.id) === this._restorePieceId
                || String(piece.pieceOe?.id || "") === String(this._restorePieceOeId || "")
            );
            if (restoredPiece) {
                this.state.selectedPiece = restoredPiece;
                this.state.showAllPieces = false;
                this._keepStoredPiece = false;
            }
        }
    }

    onSelectPiece(pieceId) {
        this.releaseStoredPieces();
        if (this.selectedPiece?.id === pieceId) {
            this.clearSelectedPiece();
            this.state.showAllPieces = true;
            return;
        }
        this.clearSelectedPiece();
        this.state.selectedPiece = this.pieces.find(piece => piece.id === pieceId);
        this.state.showAllPieces = false;
    }

    /**
     * Réinitialise les données dépendant de la pièce OE sélectionnée pour ne
     * pas afficher ou réutiliser les détails d'une sélection précédente.
     */
    clearSelectedPiece(preserveRestoredBase = false) {
        this.state.selectedPiece = undefined;
        this.state.selectedPieceAm = undefined;
        if (!preserveRestoredBase) {
            this.setBaseEurocode(undefined);
        }
        this.state.articlesVsf = [];
        this.state.vsfNoResultFor = undefined;
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
            await this.getPieceAm(this.selectedPiece);
        }
    }

    async getPieceAm(piece) {
        const res = await this.callPortal("/getPieceAm", {
            element_withPiecesAm: piece['element.withPiecesAm'],
            pieceId: piece.id,
            elementSitId: piece.elementSitId,
        })
        piece.PiecesAM = res;
        if (this._restorePieceAmId) {
            this.state.selectedPieceAm = res.find(meta => String(meta.pieceAm?.id) === this._restorePieceAmId);
            if (this.selectedPieceAm) {
                this._keepStoredPieceAm = false;
            }
            // La base enregistrée prévaut sur celle de la pièce AM restaurée (décision R12
            // du 2026-10-02) ; à défaut (base vide, pièce resélectionnée), on la dérive.
            if (this.selectedPieceAm && !this.baseEurocode) {
                this.setBaseEurocode(this.selectedPieceAm.pieceAm.reference.substring(0, 5));
            }
            this._restorePending = false;
        }
        // La propriété est enrichie en place : réassigner le tableau garantit
        // que OWL rerend aussi les pièces après-marché nouvellement reçues.
        this.state.pieces = [...this.pieces];
        return res;
    }

    /** Clic sur une carte « Équivalence AM » ou une ligne « Autres marques AM ». */
    onSelectPieceAM(metaPieceAM) {
        this.state.selectedPieceAm = metaPieceAM;
        this._keepStoredPieceAm = false;
        // Seul un choix explicite de l'utilisateur dérive la base de la pièce AM.
        this.setBaseEurocode(metaPieceAM.pieceAm.reference.substring(0, 5));
    }

    /**
     * La liste « AUTRE AM » est celle de la famille X'Glass pour le véhicule : planche et
     * famille sont partagées entre véhicules (26881-3464 pour GS600HH et GJ495CP, recette R11).
     */
    autresAmKey(famille) {
        return `${this.selectedVehicule?.id}-${famille.elementSitId}`;
    }

    autresAmFor(famille) {
        return this.state.autresAm[this.autresAmKey(famille)];
    }

    isAutresAmOpen(famille) {
        return Boolean(this.state.autresAmOpen[this.autresAmKey(famille)]);
    }

    async onToggleAutresAm(famille) {
        const key = this.autresAmKey(famille);
        const open = !this.state.autresAmOpen[key];
        this.state.autresAmOpen = { ...this.state.autresAmOpen, [key]: open };
        if (open) {
            await this.runAsync(() => this.loadAutresAm(famille), "Chargement des autres marques AM...");
        }
    }

    /**
     * Sans pieceId, /getPieceAm interroge X'Glass au niveau famille (idElementSit) :
     * c'est l'encart « AUTRE AM » du portail. Un seul appel par véhicule et famille.
     */
    async loadAutresAm(famille) {
        const key = this.autresAmKey(famille);
        if (this.state.autresAm[key]) {
            return;
        }
        this.state.autresAm = { ...this.state.autresAm, [key]: { loading: true } };
        try {
            const entries = await this.callPortal("/getPieceAm", {
                element_withPiecesAm: famille.withPiecesAm,
                elementSitId: famille.elementSitId,
            });
            this.state.autresAm = { ...this.state.autresAm, [key]: { entries: entries || [] } };
        } catch (error) {
            // Sans entrée en cache, replier puis déplier relance l'appel.
            const autresAm = { ...this.state.autresAm };
            delete autresAm[key];
            this.state.autresAm = autresAm;
            throw error;
        }
    }

    onInputBaseEurocode(ev) {
        this.state.baseEurocodeInput = ev.target.value;
    }

    onChangeBaseEurocode(ev) {
        this.setBaseEurocode(ev.target.value);
    }

    restoreSelectionFromRecord() {
        const read = (field) => field ? this.record.recordData[field] : undefined;
        this._restoreVehiculeId = read(this.record.xglassVehicleIdField) || undefined;
        this._restorePieceId = read(this.record.xglassPieceIdField) || undefined;
        this._restorePieceOeId = read(this.record.pieceOeIdField) || undefined;
        this._restorePieceAmId = read(this.record.pieceAmIdField) || undefined;
        this._restoreBaseEurocode = read(this.record.baseEurocodeField) || undefined;
        this._restorePending = Boolean(
            this._restorePieceId || this._restorePieceOeId || this._restorePieceAmId || this._restoreBaseEurocode
        );
        // Lot E1.1 : getRecordData ne réécrit la pièce et la pièce AM mémorisées qu'une fois
        // retrouvées par la restauration, ou remplacées ou retirées par l'utilisateur.
        this._keepStoredPiece = Boolean(this._restorePieceId || this._restorePieceOeId);
        this._keepStoredPieceAm = Boolean(this._restorePieceAmId);
        if (this._restoreBaseEurocode) {
            this.setBaseEurocode(this._restoreBaseEurocode);
        }
    }

    /** Action explicite de l'utilisateur : la sélection affichée remplace les pièces mémorisées. */
    releaseStoredPieces() {
        this._keepStoredPiece = false;
        this._keepStoredPieceAm = false;
    }

    get articlesVsf() {
        return this.state.articlesVsf;
    }

    async searchBaseEurocode() {
        const baseEurocode = (this.baseEurocode || "").trim();
        if (!baseEurocode) {
            this.state.articlesVsf = [];
            this.state.vsfNoResultFor = undefined;
            this.resetVsfSelection();
            this._lastSearchedBaseEurocode = undefined;
            return;
        }
        // Même base déjà cherchée ET résultats affichés : rien à faire. Sans la seconde condition,
        // « Rechercher sur VSF » restait muet après restauration (recette 2026-09-20).
        if (baseEurocode === this._lastSearchedBaseEurocode && this.state.articlesVsf.length) {
            return;
        }
        this._lastSearchedBaseEurocode = baseEurocode;
        this.state.vsfNoResultFor = undefined;
        try {
            const res = await this.callPortal("/searchBaseEurocode", {
                baseEurocode,
            });
            this.state.articlesVsf = res;
            this.state.vsfNoResultFor = res.length ? undefined : baseEurocode;
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
        this.state.primaryArticleCode = undefined;
        this.state.articleProducts = {};
        this.state.articleLoadingCodes = {};
    }

    isArticleSelected(articleCode) {
        return Boolean(this.state.selectedArticleCodes[articleCode]);
    }

    isPrimaryArticle(articleCode) {
        return this.state.primaryArticleCode === articleCode;
    }

    getPrimaryArticle() {
        const articleCode = this.state.primaryArticleCode;
        return articleCode && this.isArticleSelected(articleCode)
            ? this.getArticleByCode(articleCode)
            : undefined;
    }

    setPrimaryArticle(articleCode) {
        if (this.isArticleSelected(articleCode)) {
            this.state.primaryArticleCode = articleCode;
        }
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
            ? `/web#model=product.product&view_type=form&id=${product.id}`
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
        return PART_TYPES;
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
        if (articleCodes.includes(this.state.primaryArticleCode)) {
            this.state.primaryArticleCode = undefined;
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
            const details = await this.callPortal("/getVsfArticleDetails", {
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
            const product = await this.callPortal("/createProduct", {
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

    openImagePreview(images, index) {
        if (images?.length && index >= 0) {
            this.dialog.add(VsfImagePreviewDialog, { images, index });
        }
    }

}
