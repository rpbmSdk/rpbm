/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";

import { asyncWidget } from "./utils";
import { onWillStart, useRef, useEffect } from "@odoo/owl";

export class VehiculeComponent extends asyncWidget {
    static props = {
        ...asyncWidget.props,
        immatriculation: { type: String, optional: true },
        vehicule: { type: Object },
        selectedVehiculeId: { type: Number },
        // vehiculeMeta: { type: Object, optional: true },
        // onSelectVehicule: {type: Function},
    }
    static template = "rpbm_agent.VehiculeComponent";

    setup() {
        super.setup();
        this.state = useState({
            ...this.state,
            vehiculeExists: false,
            vehiculeId: undefined,
            vehiculeMeta: undefined
        });
        onWillStart(() => {
            // this.runAsync(this.getOdooVehicule());
            this.getVehiculeMeta();
            this.getOdooVehicule()
        })
    }

    /**
     * @returns {boolean}
     * */
    get vehiculeExists() {
        return this.state.vehiculeExists;
    }

    get vehiculeId() {
        return this.state.vehiculeId;
    }

    get vehiculeOdooUrl() {
        return `/web#menu_id=684&action=929&model=fleet.vehicle&view_type=form&id=${this.vehiculeId}`;
    }

    /**
     * @returns {VehiculeMeta}
     * */
    get vehiculeMeta() {
        return this.state.vehiculeMeta;
    }

    async getVehiculeMeta() {
        const res = await this.rpc("/rbm_agent/getVehiculeMeta", {
            vehiculeId: this.props.vehicule.id,
        })
        console.log(res);
        this.state.vehiculeMeta = res;
        return res;
    }


    getOdooVehicule() {
        console.log("getOdooVehicule");
        this.runAsync(async () => {
            const res = await this.rpc("/getOdooVehicule", {
                immatriculation: this.props.immatriculation,
                // vehicule: this.props.vehicule,
            })
            this.state.vehiculeExists = Boolean(res);
            if (this.vehiculeExists) {
                this.state.vehiculeId = res.id;
            }
        })
    }

    onClickCreateVehicule() {
        console.log("onClickCreateVehicule");
        this.runAsync(async () => {
            const vehiculeId = await this.rpc("/createVehicule", {
                immatriculation: this.props.immatriculation,
                partner_id: this.record.partnerId,
                vehicule_info: this.props.vehicule,
                vehicule_meta: this.vehiculeMeta,
            })
            this.state.vehiculeId = vehiculeId;
            this.state.vehiculeExists = true;
            // await this.getOdooVehicule();
        })
    }

    get style() {
        return this.props.vehicule.id === this.props.selectedVehiculeId ? "background-color: azure !important;" : "";
    }
}