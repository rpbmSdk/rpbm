/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ArticleComponent extends Component {
    static props = {
        ...asyncWidget.props,
        article: { type: Object },
        selectedArticleId: { type: Number },
    }
    static template = "rpbm_agent.ArticleComponent";

    get style() {
        return this.props.article.id === this.props.selectedArticleId ? "background-color: azure !important;" : "";
    }

    /**
     * @returns {ArticleVsf}
     */
    get article(){
        return this.props.article;
    }
}
