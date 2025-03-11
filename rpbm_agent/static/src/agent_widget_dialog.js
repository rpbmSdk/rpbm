/** @odoo-module **/


import { useService } from "@web/core/utils/hooks";
import { useState, Component } from "@odoo/owl";
import { Dialog } from '@web/core/dialog/dialog';


export class AgentWidgetDialog extends Component{
    static components = { Dialog }
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
        });


    }

    toogleLoading(){
        this.state.loading = !this.state.loading;
    }

    onConfirm(){
        this.props.close();
    }

    onDiscard(){
        this.props.close();
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

    onSelectVehicule(vehiculeId){
        this.state.selectedVehicule = this.vehicules.find(vehicule => vehicule.id === vehiculeId);
        console.log(this.state.selectedVehicule);
    }

}