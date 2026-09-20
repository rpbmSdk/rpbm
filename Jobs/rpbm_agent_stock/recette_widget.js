/* Helper de recette du widget rpbm_agent, injecté dans la page Odoo via chrome-devtools
 * (evaluate_script). Chaque étape est déterministe : elle agit sur le DOM, attend un état
 * précis (avec délai maximal) et renvoie un objet {ok, ...} sérialisable en JSON.
 * Usage : injecter ce fichier une fois, puis appeler `window.__recette.<étape>()`.
 */
(() => {
    const TIMEOUT = 90000;
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const text = (el) => (el ? el.textContent.replace(/\s+/g, " ").trim() : "");
    const visible = (el) => Boolean(el && el.offsetParent !== null);
    const all = (selector, root = document) => Array.from(root.querySelectorAll(selector));
    const byText = (selector, needle, root = document) =>
        all(selector, root).find((el) => visible(el) && text(el).includes(needle));
    const modal = () => all(".modal.show, .modal[style*='display: block']").find((m) => text(m).includes("Assistant véhicule et pièces"));
    const section = (title) => {
        const m = modal();
        if (!m) return null;
        const h5 = all("h5", m).find((h) => text(h).startsWith(title) || text(h).includes(title));
        return h5 ? h5.closest("section") : null;
    };
    async function waitFor(predicate, label, timeout = TIMEOUT) {
        const start = Date.now();
        while (Date.now() - start < timeout) {
            try {
                const value = predicate();
                if (value) return value;
            } catch (e) { /* DOM en cours de rendu */ }
            await sleep(250);
        }
        throw new Error(`délai dépassé (${timeout / 1000}s) : ${label}`);
    }
    const loading = () => {
        const m = modal();
        return m && (text(m).includes("en cours...") || text(m).includes("en cours…"));
    };
    const run = async (fn) => {
        try { return { ok: true, ...(await fn()) }; }
        catch (e) { return { ok: false, error: String(e && e.message || e), state: state() }; }
    };
    const notifications = () => all(".o_notification_manager .o_notification").map((n) => text(n)).slice(0, 5);
    const clickEl = (el) => { el.scrollIntoView({ block: "center" }); el.click(); };
    const cardsOf = (sec) => all(".card", sec).filter((c) => !c.closest(".card .card")); // cartes de premier niveau

    function state() {
        const m = modal();
        return {
            modalOpen: Boolean(m),
            sections: m ? all("h5", m).map(text) : [],
            immat: m ? (m.querySelector("#immatriculation") || {}).value : undefined,
            baseEurocode: m ? (m.querySelector("#baseEurocode") || {}).value : undefined,
            pieceConcernee: m ? (m.querySelector("#pieceConcernee") || {}).value : undefined,
            loading: Boolean(loading()),
            notifications: notifications(),
            url: location.href,
        };
    }

    const api = {
        version: "2026-09-21",
        state,

        async openAssistant() {
            return run(async () => {
                const tab = await waitFor(() => byText(".o_notebook .nav-link", "Véhicule (X'Glass)"), "onglet Véhicule (X'Glass)");
                clickEl(tab);
                const button = await waitFor(() => byText("button", "Assistant véhicule"), "bouton Assistant véhicule");
                clickEl(button);
                await waitFor(() => modal() && modal().querySelector("#immatriculation") && !loading(), "ouverture de la dialog et authentification des agents");
                return { immat: modal().querySelector("#immatriculation").value };
            });
        },

        async searchPlate() {
            return run(async () => {
                const m = modal();
                clickEl(byText("button", "Rechercher", m));
                await waitFor(() => !loading() && section("2. Catégorie"), "résultats véhicule et section Catégorie");
                const vehicules = cardsOf(section("1. Véhicule")).map((c) => text(c.querySelector(".card-title")));
                const selected = cardsOf(section("1. Véhicule")).find((c) => (c.querySelector(".card-body") || {}).style && c.querySelector(".card-body").style.backgroundColor);
                const metaText = text(selected || section("1. Véhicule"));
                const grab = (key) => (metaText.match(new RegExp(key + " : ([^ ]+)")) || [])[1] || null;
                return { vehicules, selected: selected ? text(selected.querySelector(".card-title")) : null,
                         meta: { vin: grab("VIN"), cnit: grab("CNIT"), dateMec: grab("Date MeC") },
                         existsInOdoo: metaText.includes("Le véhicule existe en BDD"),
                         driverWarning: metaText.includes("conducteur du véhicule est différent") };
            });
        },

        async selectCalque(label) {
            return run(async () => {
                const sec = section("2. Catégorie");
                let button = byText("button", label, sec);
                if (!button) {
                    const more = byText("button", "Afficher les autres", sec);
                    if (more) { clickEl(more); await sleep(300); }
                    button = await waitFor(() => byText("button", label, section("2. Catégorie")), `calque ${label}`);
                }
                clickEl(button);
                await waitFor(() => !loading() && section("3. Pièce") && cardsOf(section("3. Pièce")).length > 0, "pièces de la catégorie");
                return { pieces: cardsOf(section("3. Pièce")).length, pieceConcernee: modal().querySelector("#pieceConcernee").value,
                         calques: all("button", section("2. Catégorie")).map(text) };
            });
        },

        async selectPiece({ withLabor = true } = {}) {
            return run(async () => {
                const sec = section("3. Pièce");
                const more = byText("button", "Afficher les autres", sec);
                if (more) { clickEl(more); await sleep(300); }
                const cards = cardsOf(section("3. Pièce"));
                const card = (withLabor ? cards.find((c) => c.querySelector("li")) : cards[0]) || cards[0];
                if (!card) throw new Error("aucune pièce affichée");
                clickEl(card.querySelector(".card-body"));
                await waitFor(() => !loading() && byText(".badge", "Pièce sélectionnée", section("3. Pièce")), "pièce sélectionnée et pièces après-marché");
                const box = byText(".badge", "Pièce sélectionnée", section("3. Pièce")).closest(".border");
                return { piece: text(card.querySelector(".card-title")), labor: all("li", card).map(text), piecesAm: all(".card", box).length };
            });
        },

        async selectPieceAm(index = 0) {
            return run(async () => {
                const box = byText(".badge", "Pièce sélectionnée", section("3. Pièce")).closest(".border");
                const cards = all(".card", box);
                if (!cards[index]) throw new Error(`pièce après-marché ${index} absente (${cards.length} disponibles)`);
                clickEl(cards[index].querySelector(".card-body"));
                await waitFor(() => modal().querySelector("#baseEurocode") && modal().querySelector("#baseEurocode").value, "base Eurocode déduite");
                await waitFor(() => !loading(), "recherche VSF terminée");
                const articles = section("Article VSF") ? cardsOf(section("Article VSF")).map((c) => text(c.querySelector(".card-title"))) : [];
                return { base: modal().querySelector("#baseEurocode").value, articles };
            });
        },

        async searchBase(base) {
            return run(async () => {
                const input = modal().querySelector("#baseEurocode");
                input.value = base;
                input.dispatchEvent(new Event("change", { bubbles: true }));
                await sleep(300);
                clickEl(byText("button", "Rechercher sur VSF", modal()));
                await waitFor(() => !loading(), "recherche VSF terminée");
                return { base, articles: cardsOf(section("Article VSF")).map((c) => text(c.querySelector(".card-title"))) };
            });
        },

        async selectArticle({ preferCode } = {}) {
            return run(async () => {
                const sec = section("Article VSF");
                const cards = cardsOf(sec);
                if (!cards.length) throw new Error("aucun article VSF affiché");
                const card = (preferCode && cards.find((c) => text(c.querySelector(".card-title")).startsWith(preferCode))) || cards[0];
                clickEl(card.querySelector(".card-body"));
                await waitFor(() => !loading() && card.querySelector("div[name='article_actions']"), "encart d'actions de l'article");
                const title = text(card.querySelector(".card-title"));
                const prices = text(card).match(/Prix:\s*([\d.,]+)\s*€\s*Coût:\s*([\d.,]+)\s*€/);
                const actions = text(card.querySelector("div[name='article_actions']"));
                return { code: title.split(" ")[0], title, prixVente: prices ? Number(prices[1].replace(",", ".")) : null,
                         prixVenteRPBM: prices ? Number(prices[2].replace(",", ".")) : null,
                         productFound: actions.includes("Produit Odoo trouvé"), actions };
            });
        },

        async setPrimary() {
            return run(async () => {
                const button = byText("div[name='article_actions'] button", "Définir comme article principal", modal());
                if (button) clickEl(button);
                await waitFor(() => byText("div[name='article_actions'] button", "Article principal", modal()), "article principal");
                return { primary: true };
            });
        },

        async createProduct() {
            return run(async () => {
                const box = all("div[name='article_actions']", modal()).find((b) => text(b).includes("Article absent"));
                if (!box) return { created: false, reason: "produit déjà présent" };
                clickEl(byText("button", "Créer le produit", box));
                await waitFor(() => !loading() && text(box).includes("Produit Odoo trouvé"), "création du produit");
                const link = box.querySelector("a[href*='product.product']");
                return { created: true, productUrl: link ? link.getAttribute("href") : null };
            });
        },

        async addToQuote() {
            return run(async () => {
                const box = all("div[name='article_actions']", modal()).find((b) => byText("button", "Ajouter au devis", b));
                if (!box) throw new Error("bouton Ajouter au devis absent");
                clickEl(byText("button", "Ajouter au devis", box));
                await waitFor(() => !loading() && byText("button", "Retirer du devis", box), "ligne ajoutée au devis");
                return { added: true };
            });
        },

        async tickLabor({ max = 2 } = {}) {
            return run(async () => {
                const sec = section("Main d'œuvre");
                if (!sec) throw new Error("section main-d'œuvre absente");
                const items = all(".list-group-item", sec).filter((item) => item.querySelector("input[type=checkbox]") && !item.querySelector("input[type=checkbox]").disabled);
                const ticked = [];
                for (const item of items.slice(0, max)) {
                    const box = item.querySelector("input[type=checkbox]");
                    if (!box.checked) { box.click(); }
                    ticked.push(text(item));
                }
                return { ticked, available: items.length, unavailable: all(".text-warning", sec).map(text) };
            });
        },

        async addLabor() {
            return run(async () => {
                const sec = section("Main d'œuvre");
                clickEl(byText("button", "Ajouter les opérations sélectionnées", sec));
                await waitFor(() => !loading() && byText("button", "Retirer", section("Main d'œuvre")), "lignes de main-d'œuvre ajoutées");
                return { removeButtons: all("button", section("Main d'œuvre")).filter((b) => text(b) === "Retirer").length };
            });
        },

        async confirmAndSave() {
            return run(async () => {
                clickEl(byText(".modal-footer button", "Confirmer et enregistrer", modal()));
                await waitFor(() => !modal(), "fermeture de la dialog");
                await waitFor(() => !document.querySelector(".o_form_status_indicator_buttons:not(.invisible) .o_form_button_save") || true, "formulaire enregistré", 5000);
                return { closed: true, dirty: Boolean(document.querySelector(".o_form_dirty")), notifications: notifications() };
            });
        },

        async cancel() {
            return run(async () => {
                const button = byText(".modal-footer button", "Annuler", modal());
                if (button) clickEl(button);
                await waitFor(() => !modal(), "fermeture de la dialog");
                return { closed: true };
            });
        },

        async newQuotation() {
            return run(async () => {
                clickEl(await waitFor(() => byText("button", "Nouveau devis"), "bouton Nouveau devis"));
                await waitFor(() => document.querySelector("div[name='carrier_id']") && document.querySelector("div[name='order_line']"), "formulaire du devis");
                await sleep(1000);
                const carrier = document.querySelector("div[name='carrier_id'] input") || document.querySelector("div[name='carrier_id']");
                return { carrier: carrier.value !== undefined ? carrier.value : text(carrier),
                         xglassTab: Boolean(byText(".o_notebook .nav-link", "Véhicule (X'Glass)")) };
            });
        },

        async saveForm() {
            return run(async () => {
                const button = document.querySelector(".o_form_button_save");
                if (button && visible(button)) clickEl(button);
                await sleep(1500);
                await waitFor(() => !document.querySelector(".o_form_saving"), "enregistrement");
                return { saved: true, url: location.href };
            });
        },

        async orderLines() {
            return run(async () => {
                const rows = all("div[name='order_line'] tbody tr.o_data_row");
                const cell = (row, name) => text(row.querySelector(`td[name='${name}']`));
                return { lines: rows.map((row) => ({ product: cell(row, "product_template_id") || cell(row, "product_id"), qty: cell(row, "product_uom_qty"), price_unit: cell(row, "price_unit") })) };
            });
        },

        async confirmSale() {
            return run(async () => {
                clickEl(await waitFor(() => document.querySelector("button[name='action_confirm']"), "bouton Confirmer du devis"));
                await waitFor(() => text(document.querySelector(".o_statusbar_status")).includes("Bon de commande") || text(document.querySelector(".o_statusbar_status")).includes("Sales Order"), "statut Bon de commande");
                return { state: text(document.querySelector(".o_statusbar_status .o_arrow_button_current")), name: text(document.querySelector(".o_form_view .oe_title")), notifications: notifications() };
            });
        },
    };
    window.__recette = api;
    return { ok: true, version: api.version };
})();
