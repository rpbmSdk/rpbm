/** @odoo-module **/

import { asyncWidget } from "./utils";

export class ArticleComponent extends asyncWidget {
    static props = {
        ...asyncWidget.props,
        article: { type: Object },
        selected: { type: Boolean, optional: true },
        onOpenImage: { type: Function, optional: true },
        slots: { type: Object, optional: true },
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

    openImage(event, imageUrl) {
        event.stopPropagation();
        if (
            event.button ||
            event.ctrlKey ||
            event.metaKey ||
            event.shiftKey ||
            event.altKey ||
            !imageUrl ||
            !this.props.onOpenImage
        ) {
            return;
        }
        event.preventDefault();
        const images = (this.props.article.images || [])
            .map((image) => image.fullUrl)
            .filter(Boolean);
        this.props.onOpenImage(images, images.indexOf(imageUrl));
    }

    stopImagePropagation(event) {
        event.stopPropagation();
    }
}
