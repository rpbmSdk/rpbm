/** @odoo-module **/

import { asyncWidget } from "./utils";

export class ArticleComponent extends asyncWidget {
    static props = {
        ...asyncWidget.props,
        article: { type: Object },
        selectedArticleId: { type: String, optional: true },
    }
    static template = "rpbm_agent.ArticleComponent";

    get style() {
        return this.props.article.code === this.props.selectedArticleId ? "background-color: azure !important;" : "";
    }

    /**
     * @returns {ArticleVsf}
     */
    get article(){
        return this.props.article;
    }
}
