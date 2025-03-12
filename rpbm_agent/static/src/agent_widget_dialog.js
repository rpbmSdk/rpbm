/** @odoo-module **/


import { useService } from "@web/core/utils/hooks";
import { useState, Component } from "@odoo/owl";
import { Dialog } from '@web/core/dialog/dialog';
import { onWillStart, useRef,useEffect } from "@odoo/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";


export class VehiculeComponent extends Component{
    static props = {
        vehicule: {type: Object},
        selectedVehiculeId: {type: Number},
        // onSelectVehicule: {type: Function},
    }
    static template = "rpbm_agent.VehiculeComponent";

    get style (){
        return this.props.vehicule.id === this.props.selectedVehiculeId ? "background-color: azure !important;" : "";
    }
}


export class CalqueComponent extends Component{
    static props = {
        calque: {type: Object},
        selectedCalqueId: {type: Number},
        // onClickCalque: {type: Function},
    }
    static template = "rpbm_agent.CalqueComponent";

    get class (){
        let className = "btn ";
        className += this.props.calque.id === this.props.selectedCalqueId ? "btn-primary" : "btn-outline-primary";
        return className;
    }
}

export class PieceComponent extends Component{
    static props = {
        piece: {type: Object},
        selectedPieceId: {type: Number},
    }
    static template = "rpbm_agent.PieceComponent";

    get style (){
        return this.props.piece.id === this.props.selectedPieceId ? "background-color: azure !important;" : "";
    }
}


export class AgentWidgetDialog extends Component{
    static components = { 
        Dialog,
        VehiculeComponent,
        CalqueComponent,
        PieceComponent,
     }
    // static props = {
    //     ...standardWidgetProps,
    //     close: {type: Function, optional: true},
    // }
    static template = "rpbm_agent.AgentWidgetDialog";

    setup(){
        super.setup();
        this.rpc = useService("rpc");
        this.orm = useService("orm");
        this.record = this.props.record;
        this.state = useState({
            loading: false,
            immatriculationValue:"",
            vehicules: [],
            selectedVehicule: undefined,
            selectedVehiculeId: 0,
            planche:undefined,
            calques: [],
            selectedCalque: undefined,
            pieces:[],
            selectedPiece: undefined,
        });

        onWillStart(async ()=>{
            this.toogleLoading();
            try{
                await this.rpc("/rpbm_agent_auth")
            }
            catch(e){
                console.error(e);
                await this.rpc("/rpbm_agent_auth")
            }
            this.toogleLoading();
        })

        // useEffect(()=>{
        //     console.log("useEffect selectedVehicule changed ", this.selectedVehicule);
        //     if(this.selectedVehicule){
        //         // const planche = this.getPlanche();
        //         // this.state.planche = planche;
        //         // this.
        //         this.getPlanche();
        //     }
        //     else{
        //         this.state.planche = undefined;
        //     }
        // },()=>[this.selectedVehicule]);

        // useEffect(()=>{
        //     console.log("useEffect planche changed ", this.planche);
        //     if(this.planche){
        //         this.state.selectedCalque = this.planche.calques[0];
        //     }
        //     else{
        //         this.state.selectedCalque = undefined;
        //         // this.state.pieces = [];
        //     }
        // },()=>[this.planche]);

        // useEffect(()=>{
        //     console.log("useEffect selectedCalque changed ", this.selectedCalque);
        //     if(this.selectedCalque){
        //         // this.state.pieces = this.selectedCalque.pieces;
        //         this.getPieces();
        //     }
        //     else{
        //         this.state.pieces = [];
        //     }
        // },()=>[this.selectedCalque]);

        // useEffect(()=>{
        //     console.log("useEffect pieces changed ", this.pieces);
        //     if(this.pieces.length > 0){
        //         this.state.selectedPiece = this.pieces[0];
        //     }
        //     else{
        //         this.state.selectedPiece = undefined;
        //     }
        // }, ()=>[this.pieces]);


    }

    toogleLoading(){
        this.state.loading = !this.state.loading;
    }

    async close(){
        await this.rpc("/rpbm_agent_close")
    }

    async onConfirm(){
        await this.close();
        // this.props.close();
    }

    async onDiscard(){
        await this.close();
        // this.props.close();
    }

    get immatriculationValue(){
        return this.state.immatriculationValue;
    }

    onChangeImmatriculation(ev){
        this.state.immatriculationValue = ev.target.value;
        console.log(this.immatriculationValue);
    }

    async onSearchImmatriculation(){
        this.toogleLoading();
        const res = await this.rpc("/searchImmatriculation",{
            immatriculation: this.immatriculationValue,
        })
        console.log(res);
        this.state.vehicules = res;
        this.toogleLoading();

    }

    get vehicules(){
        return this.state.vehicules;
    }

    get selectedVehicule(){
        return this.state.selectedVehicule;
    }

    get selectedVehiculeId(){
        return this.selectedVehicule ? this.selectedVehicule.id : 0;
    }

    onSelectVehicule(vehiculeId){
        // this.state.selectedVehiculeId = vehiculeId;
        this.state.selectedVehicule = this.vehicules.find(vehicule => vehicule.id === vehiculeId);
        console.log(this.state.selectedVehicule);
    }

    async getPlanche(){
        const res = await this.rpc("/getPlanche",{
            vehiculeId: this.selectedVehicule.id,
        })
        console.log(res);
        this.state.planche = res;
        return res;
    }

    get planche(){
        return this.state.planche;
    }

    get calques(){
        return this.planche.calques;
    }

    get selectedCalque(){
        return this.state.selectedCalque;
    }

    get selectedCalqueId(){
        return this.selectedCalque ? this.selectedCalque.id : 0;
    }

    onChangeCalque(ev){
        const calqueId = parseInt(ev.target.value);
        this.state.selectedCalque = this.calques.find(calque => calque.id === calqueId);
        console.log(this.selectedCalque);
    }
    onClickCalque(calqueId){
        this.state.selectedCalque = this.calques.find(calque => calque.id === calqueId);
        console.log(this.selectedCalque);
    }

    get pieces(){
        return this.state.pieces;
    }

    async getPieces(){
        const res = await this.rpc("/getPieces",{
            plancheId: this.planche.id,
            calqueId: this.selectedCalque.id,
        })
        console.log(res);
        this.state.pieces = res;
        // return res;
    }

    onSelectPiece(pieceId){
        this.state.selectedPiece = this.pieces.find(vehicule => vehicule.id === pieceId);
        console.log(this.state.selectedPiece);
    }

    get selectedPiece(){
        return this.state.selectedPiece;
    }

    get selectedPieceId(){
        return this.selectedPiece ? this.selectedPiece.id : 0;
    }

}