/** @odoo-module **/

import { Component } from "@odoo/owl";

export class PieceComponent extends Component {
    static props = {
        piece: { type: Object },
        selectedPieceId: { type: Number },
    }
    static template = "rpbm_agent.PieceComponent";

    get style() {
        return this.props.piece.id === this.props.selectedPieceId ? "background-color: azure !important;" : "";
    }
}
