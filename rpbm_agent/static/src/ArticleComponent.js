/** @odoo-module **/

import { asyncWidget } from "./utils";

export class ArticleComponent extends asyncWidget {
    static props = {
        ...asyncWidget.props,
        article: { type: Object },
        selected: { type: Boolean, optional: true },
        onOpenImage: { type: Function, optional: true },
    }
    static template = "rpbm_agent.ArticleComponent";

    get style() {
        return this.props.selected ? "background-color: azure !important;" : "";
    }

    /**
     * @returns {ArticleVsf}
     */
    get article(){
        return this.props.article;
    }

    openImage(imageUrl) {
        if (imageUrl && this.props.onOpenImage) {
            this.props.onOpenImage(imageUrl);
        }
    }
}
