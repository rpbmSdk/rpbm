import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";

const load = async (name) => (await readFile(new URL(`./static/src/${name}`, import.meta.url), "utf8"))
    .replace(/^import[\s\S]*?;\n/gm, "")
    .replace(/^export /gm, "");
const emptyComponent = class {};
// Crochets Owl simulés : setup() réel (utils.js compris), effets rejoués à la main.
const effects = [];
const rpcCalls = [];
const mountedHooks = [];
const context = {
    Component: class { setup() {} },
    standardWidgetProps: {},
    useState: (state) => state,
    useService: (name) => name === "rpc"
        ? async (route, params) => { rpcCalls.push({ route, params }); return []; }
        : { add() {} },
    useEffect: (fn, deps) => effects.push({ fn, deps }),
    onWillStart() {},
    onWillUnmount() {},
    onMounted: (fn) => mountedHooks.push(fn),
    // status() d'Owl : un test pose testStatus = "destroyed" pour simuler la fermeture du dialog.
    status: (component) => component.testStatus || "mounted",
    FormController: class { setup() {} },
    // Comme le patch d'Odoo : `super` dans l'extension appelle la méthode d'origine.
    patch(target, extension) {
        Object.setPrototypeOf(extension, Object.create(Object.getPrototypeOf(target), Object.getOwnPropertyDescriptors(target)));
        Object.defineProperties(target, Object.getOwnPropertyDescriptors(extension));
    },
    Dialog: emptyComponent,
    VehiculeComponent: emptyComponent,
    CalqueComponent: emptyComponent,
    PieceComponent: emptyComponent,
    PieceAMComponent: emptyComponent,
    ArticleComponent: emptyComponent,
    VsfImagePreviewDialog: emptyComponent,
};
const dialogSources = ["utils.js", "agent_widget_dialog.js", "agent_widget_dialog_sale_order.js", "agent_widget_dialog_crm_lead.js"];
vm.runInNewContext(
    `${(await Promise.all(dialogSources.map(load))).join("\n")}
    Object.assign(this, { AgentWidgetDialog, AgentWidgetDialogSaleOrder, AgentWidgetDialogCrmLead });`,
    context,
);

const dialog = Object.create(context.AgentWidgetDialog.prototype);
dialog.state = { baseEurocode: "6108A", baseEurocodeInput: "6108A" };

dialog.onInputBaseEurocode({ target: { value: "6108 A+&B" } });
assert.equal(dialog.baseEurocode, "6108A");
assert.equal(dialog.vsfSearchUrl, "https://client.myvsf.fr/catalogue/vitrage?search=6108%20A%2B%26B");

dialog.onInputBaseEurocode({ target: { value: "  " } });
assert.equal(dialog.vsfSearchUrl, undefined);

dialog.setBaseEurocode("6574A");
assert.equal(dialog.baseEurocode, "6574A");
assert.equal(dialog.baseEurocodeInput, "6574A");

dialog.record = {
    baseEurocodeField: "rpbm_eurocode_base",
    pieceAmIdField: "rpbm_piece_am_id",
    recordData: { rpbm_eurocode_base: "6108A", rpbm_piece_am_id: "3365069" },
};
dialog.state = { baseEurocode: undefined, baseEurocodeInput: undefined, selectedPieceAm: undefined, pieces: [] };
dialog.restoreSelectionFromRecord();
dialog.callPortal = async () => [{ pieceAm: { id: 3365069, reference: "6574AGABCHM" } }];
await dialog.getPieceAm({});
assert.equal(dialog.baseEurocode, "6108A");
assert.equal(dialog.vsfSearchUrl, "https://client.myvsf.fr/catalogue/vitrage?search=6108A");

dialog.onSelectPieceAM({ pieceAm: { reference: "6574AGABCHM" } });
assert.equal(dialog.baseEurocode, "6574A");
assert.equal(dialog.vsfSearchUrl, "https://client.myvsf.fr/catalogue/vitrage?search=6574A");

// Lot D, build A : groupes X'Glass, « Autres marques AM » par famille, VSF sans pièce OE.
// Les objets créés dans le contexte vm n'ont pas les prototypes de ce module : comparer en JSON.
const plain = (value) => JSON.parse(JSON.stringify(value));
const xglassPiece = (id, elementKey, elementSitId, elementSitLibelle) => ({
    id, elementKey, elementSitId, elementSitLibelle, "element.withPiecesAm": true, pieceOe: { id },
});
const outline = (groups) => plain(groups).map(({ titre, familles }) => [
    titre, familles.map(({ elementSitId, libelle, pieces }) => [elementSitId, libelle, pieces.map(({ id }) => id)]),
]);

const grouped = Object.create(context.AgentWidgetDialog.prototype);
grouped.state = {
    showAllPieces: false,
    pieces: [
        xglassPiece(1, "ELEMENTSIT_PRINCIPAUX", 3464, "PARE-BRISE"),
        xglassPiece(2, "ELEMENTSIT_PRINCIPAUX", 3464, "PARE-BRISE"),
        xglassPiece(3, "ELEMENTSIT_COMPLEMENTAIRES", 6930, "CALE"),
        xglassPiece(4, "ELEMENTSIT_COMPLEMENTAIRES", 2958, "JT"),
        xglassPiece(5, "ELEMENTSIT_COMPLEMENTAIRES", 6930, "CALE"),
    ],
};
const allGroups = [
    ["Pièces principales", [[3464, "PARE-BRISE", [1, 2]]]],
    ["Pièces complémentaires", [[6930, "CALE", [3, 5]], [2958, "JT", [4]]]],
];
assert.deepEqual(outline(grouped.pieceGroups), allGroups);
assert.deepEqual(outline(grouped.visiblePieceGroups), allGroups);

// Mode focalisé : la seule famille de la pièce sélectionnée, avec sa seule carte.
grouped.state.selectedPiece = grouped.state.pieces[3];
assert.deepEqual(outline(grouped.visiblePieceGroups), [["Pièces complémentaires", [[2958, "JT", [4]]]]]);
assert.deepEqual(plain(grouped.visibleFamillePieces(grouped.pieceGroups[1].familles[1])).map(({ id }) => id), [4]);
grouped.showOtherPieces();
assert.deepEqual(outline(grouped.visiblePieceGroups), allGroups);

// Contexte restauré sans pièce (SO7750) : toutes les familles, aucune carte, section VSF visible.
Object.assign(grouped.state, { showAllPieces: false, selectedPiece: undefined, selectedPieceAm: undefined });
Object.assign(grouped, { _restorePending: true, _restoreBaseEurocode: "7310A" });
assert.deepEqual(outline(grouped.visiblePieceGroups), allGroups);
assert.equal(grouped.pieceGroups.every(({ familles }) => familles.every(f => !grouped.visibleFamillePieces(f).length)), true);
assert.equal(grouped.showVsfSection, true);

// Groupes absents et elementKey manquant.
grouped.state.pieces = [xglassPiece(6, "ELEMENTSIT_COMPLEMENTAIRES", 4212, "RETROVISEUR")];
assert.deepEqual(outline(grouped.pieceGroups), [["Pièces complémentaires", [[4212, "RETROVISEUR", [6]]]]]);
grouped.state.pieces = [{ id: 7, elementSitId: 99, pieceOe: { id: 7 } }];
assert.deepEqual(outline(grouped.pieceGroups), [["Pièces", [[99, "", [7]]]]]);
grouped.state.pieces = [];
assert.deepEqual(outline(grouped.pieceGroups), []);

// Encarts « Autres marques AM » : un appel par véhicule et famille, dépliage indépendant.
const portalCalls = [];
const am = Object.create(context.AgentWidgetDialog.prototype);
am.state = { autresAm: {}, autresAmOpen: {}, selectedVehicule: { id: 471612 } };
am.runAsync = fn => fn();
am.callPortal = async (route, params) => {
    portalCalls.push([route, params]);
    return [{ pieceAm: { id: 3365069, reference: "6108AGNSMVZ1B" } }];
};
const pareBrise = { elementSitId: 3464, withPiecesAm: true };
const cale = { elementSitId: 6930, withPiecesAm: false };
assert.equal(am.isAutresAmOpen(pareBrise), false);
await am.onToggleAutresAm(pareBrise);
assert.equal(am.isAutresAmOpen(pareBrise), true);
assert.equal(am.isAutresAmOpen(cale), false);
assert.equal(am.autresAmFor(pareBrise).entries.length, 1);
assert.equal(am.autresAmFor(cale), undefined);
await am.onToggleAutresAm(pareBrise);
assert.equal(am.isAutresAmOpen(pareBrise), false);
await am.onToggleAutresAm(pareBrise);
assert.deepEqual(plain(portalCalls), [["/getPieceAm", { element_withPiecesAm: true, elementSitId: 3464 }]]);
am.clearSelectedPiece();
assert.equal(am.isAutresAmOpen(pareBrise), true, "désélectionner une pièce ne replie plus les encarts");

// Régression 261002.2 : même planche et famille pour GS600HH et GJ495CP, listes distinctes.
am.state.selectedVehicule = { id: 471613 };
assert.equal(am.autresAmFor(pareBrise), undefined);
assert.equal(am.isAutresAmOpen(pareBrise), false);
await am.onToggleAutresAm(pareBrise);
assert.equal(portalCalls.length, 2);

am.callPortal = async () => { throw new Error("X'Glass indisponible"); };
await assert.rejects(am.loadAutresAm(cale), /indisponible/);
assert.equal(am.autresAmFor(cale), undefined, "une erreur ne laisse pas d'entrée en cache");

am.auth_agents = async () => {};
am.restorePortalContext = async () => {};
await am.reconnectAgents();
assert.deepEqual(plain(am.state.autresAm), {});
assert.deepEqual(plain(am.state.autresAmOpen), {});

// Recherche VSF automatique : setup() réel, effet VSF rejoué comme Owl (deps comparées par ===).
const mount = (data, Dialog = context.AgentWidgetDialog) => {
    effects.length = 0;
    rpcCalls.length = 0;
    const widget = new Dialog();
    widget.props = { record: { data }, close() {} };
    widget.setup();
    // Service rpc non protégé (this.env.services.rpc) : le même que celui du widget.
    widget.env = { services: { rpc: (route, params) => widget.rpc(route, params) } };
    widget.state.agentsInitialized = true;
    return widget;
};
const runEffect = (effect) => {
    const deps = effect.deps();
    if (!effect.previous || deps.some((dep, index) => dep !== effect.previous[index])) {
        effect.previous = deps;
        effect.fn(...deps);
    }
};
const runVsfEffect = () => runEffect(effects.at(-1));
// Deuxième effet de setup(), après canConfirm.
const runVehiculesEffect = () => runEffect(effects[1]);
const vsfSearches = async () => {
    await new Promise(resolve => setImmediate(resolve));
    return plain(rpcCalls.filter(({ route }) => route === "/searchBaseEurocode").map(({ params }) => params));
};

// R12 : une base restaurée seule s'affiche sans lancer de recherche.
const restored = mount({ rpbm_eurocode_base: "7310A" });
runVsfEffect();
assert.equal(restored.baseEurocode, "7310A");
assert.equal(restored.showVsfSection, true);
assert.deepEqual(await vsfSearches(), []);

// Ligne « Autres marques AM » sans pièce OE : base posée, section VSF visible, une recherche.
const noPiece = mount({});
runVsfEffect();
assert.equal(noPiece.showVsfSection, false);
noPiece.onSelectPieceAM({ pieceAm: { id: 3365069, reference: "6108AGNSMVZ1B" } });
runVsfEffect();
assert.equal(noPiece.baseEurocode, "6108A");
assert.equal(noPiece.showVsfSection, true);
assert.deepEqual(await vsfSearches(), [{ baseEurocode: "6108A" }]);
noPiece.onSelectPieceAM({ pieceAm: { id: 3365070, reference: "6108AGNSMVZ" } });
runVsfEffect();
assert.deepEqual(await vsfSearches(), [{ baseEurocode: "6108A" }], "même base : pas de nouvelle recherche");

// Restauration pièce OE puis pièce AM : la seconde sélection ne relance pas la recherche en cours.
const both = mount({ rpbm_eurocode_base: "6108A", rpbm_xglass_piece_id: "1", rpbm_piece_am_id: "3365069" });
runVsfEffect();
both.state.selectedPiece = { id: 1 };
runVsfEffect();
both.state.selectedPieceAm = { pieceAm: { id: 3365069, reference: "6108AGNSMVZ1B" } };
runVsfEffect();
assert.deepEqual(await vsfSearches(), [{ baseEurocode: "6108A" }]);

// Lot E1 : véhicule X'Glass mémorisé s'il figure dans la liste, sinon le premier.
const memorized = mount({ rpbm_xglass_vehicle_id: "2" });
memorized.state.vehicules = [{ id: 1 }, { id: 2 }];
runVehiculesEffect();
assert.equal(memorized.selectedVehicule.id, 2);
memorized.state.vehiculeMeta = {};
memorized.getOdooVehicule = async () => ({ id: 5, name: "GS600HH" });
assert.equal((await memorized.getRecordData()).rpbm_xglass_vehicle_id, "2");

const unknownVehicle = mount({ rpbm_xglass_vehicle_id: "9" });
unknownVehicle.state.vehicules = [{ id: 1 }, { id: 2 }];
runVehiculesEffect();
assert.equal(unknownVehicle.selectedVehicule.id, 1);

const noVehicle = mount({ rpbm_xglass_vehicle_id: "2" });
noVehicle.state.selectedVehicule = { id: 2 };
runVehiculesEffect();
assert.equal(noVehicle.selectedVehicule, undefined);

// L'opportunité s'arrête à la base Eurocode : même pièce AM et même base, aucune recherche VSF.
for (const [Dialog, searches] of [
    [context.AgentWidgetDialog, [{ baseEurocode: "6108A" }]],
    [context.AgentWidgetDialogCrmLead, []],
]) {
    const widget = mount({ rpbm_eurocode_base: "6108A" }, Dialog);
    runVsfEffect();
    widget.state.selectedPieceAm = { pieceAm: { id: 3365069, reference: "6108AGNSMVZ1B" } };
    runVsfEffect();
    assert.deepEqual(await vsfSearches(), searches, Dialog.name);
}

// « Créer un devis » sur l'opportunité 42 : chaque étape est journalisée dans events.
const crmFor = (events, recordOverrides = {}) => {
    const widget = mount({ partner_id: [7, "Client de test"], type: "opportunity" }, context.AgentWidgetDialogCrmLead);
    Object.assign(widget.props.record, {
        resId: 42,
        context: { lang: "fr_FR" },
        async update() { events.push("update"); },
        async save() { events.push("save"); return true; },
    }, recordOverrides);
    widget.props.close = () => events.push("close");
    widget.rpc = async (route) => { events.push(route); return []; };
    widget.action = { async doActionButton() { events.push("doActionButton"); } };
    return widget;
};
// Montage simulé d'un FormController : patch appliqué, puis crochets onMounted.
const openedDialogs = [];
const mountForm = (resModel, root) => {
    mountedHooks.length = 0;
    const controller = new context.FormController();
    Object.assign(controller, {
        props: { resModel },
        model: { root },
        dialogService: { add: (Dialog, props) => openedDialogs.push([Dialog, props]) },
    });
    controller.setup();
    mountedHooks.forEach(hook => hook());
};
const quotation = (opportunity_id, isNew = true) => ({ isNew, data: { opportunity_id } });
const newQuotation = quotation([42, "Opportunité de recette"]);

// Double clic : une seule écriture, puis fermeture, action native et dialog du devis.
const events = [];
let actionParams;
const crm = crmFor(events);
crm.action.doActionButton = async (params) => {
    events.push("doActionButton");
    actionParams = params;
    mountForm("crm.lead", newQuotation);
    mountForm("sale.order", quotation(false));
    mountForm("sale.order", quotation([42, "Opportunité de recette"], false));
    mountForm("sale.order", quotation([43, "Autre opportunité"]));
    assert.equal(openedDialogs.length, 0);
    mountForm("sale.order", newQuotation);
    mountForm("sale.order", newQuotation);
};
await Promise.all([crm.onCreateQuotation(), crm.onCreateQuotation()]);
assert.deepEqual(events, ["update", "save", "/rpbm_agent_close", "close", "doActionButton"]);
assert.deepEqual(plain(actionParams), {
    type: "object", name: "action_sale_quotations_new", resModel: "crm.lead", resId: 42, context: { lang: "fr_FR" },
});
assert.equal(actionParams.context, crm.props.record.context);
assert.equal(openedDialogs.length, 1, "un seul dialog, au premier montage du devis");
assert.equal(openedDialogs[0][0], context.AgentWidgetDialogSaleOrder);
assert.equal(openedDialogs[0][1].record, newQuotation);
assert.equal(crm.state.writing, false);
mountForm("sale.order", newQuotation);
mountForm("sale.order", quotation(false));
assert.equal(openedDialogs.length, 1, "drapeau à usage unique ; sans drapeau, un devis sans opportunité n'ouvre rien");

// Formulaire non enregistrable : ni fermeture ni action, boutons réactivés.
const refusedEvents = [];
const refused = crmFor(refusedEvents, { async save() { refusedEvents.push("save"); return false; } });
await refused.onCreateQuotation();
assert.deepEqual(refusedEvents, ["update", "save"]);
assert.equal(refused.state.writing, false);

// Action refusée par le serveur : l'erreur remonte et le drapeau est vidé.
const rejected = crmFor([]);
rejected.action.doActionButton = async () => { throw new Error("Accès refusé"); };
await assert.rejects(rejected.onCreateQuotation(), /Accès refusé/);
mountForm("sale.order", newQuotation);
assert.equal(openedDialogs.length, 1, "un rejet vide le drapeau");

// Lot E1.1 : pièce et pièce AM mémorisées réécrites seulement si retrouvées, ou changées par l'utilisateur.
const STORED_PIECES = { rpbm_xglass_piece_id: "11", rpbm_piece_oe_id: "21", rpbm_piece_am_id: "3365069" };
const CLEARED_PIECES = { rpbm_xglass_piece_id: "", rpbm_piece_oe_id: "", rpbm_piece_am_id: "" };
const pieceWrites = async (widget) => {
    const data = await widget.getRecordData();
    return Object.fromEntries(Object.keys(STORED_PIECES).filter(key => key in data).map(key => [key, data[key]]));
};
const oePiece = (id) => ({ id, pieceOe: { id: id + 10 } });
const calques = [{ id: 2, libelle: "PARE-BRISE" }, { id: 3, libelle: "GLACE AR" }];
const mountStored = (data = {}) => {
    const widget = mount({ ...STORED_PIECES, ...data });
    Object.assign(widget.state, { planche: { id: 1, calques }, selectedCalque: calques[0] });
    return widget;
};
const keptFlags = (widget) => [widget._keepStoredPiece, widget._keepStoredPieceAm];

// Confirmation avant le chargement des pièces, puis pièce introuvable : rien n'est écrit.
const early = mountStored();
runVehiculesEffect();
assert.deepEqual(await pieceWrites(early), {}, "confirmation avant le chargement des pièces");
early.callPortal = async () => [oePiece(12)];
await early.getPieces();
early.clearSelectedPiece(true);
assert.deepEqual(await pieceWrites(early), {}, "pièce introuvable et effets automatiques : valeurs conservées");

// Pièce retrouvée : écrite ; pièce AM absente des équivalences (« Autres marques AM ») : conservée.
const found = mountStored();
found.callPortal = async () => [oePiece(11), oePiece(12)];
await found.getPieces();
assert.deepEqual(await pieceWrites(found), { rpbm_xglass_piece_id: "11", rpbm_piece_oe_id: "21" });
found.callPortal = async () => [{ pieceAm: { id: 3365070, reference: "6108AGNSMVZ" } }];
await found.getPieceAm(found.selectedPiece);
assert.deepEqual(await pieceWrites(found), { rpbm_xglass_piece_id: "11", rpbm_piece_oe_id: "21" });
found.callPortal = async () => [{ pieceAm: { id: 3365069, reference: "6108AGNSMVZ1B" } }];
await found.getPieceAm(found.selectedPiece);
assert.equal((await pieceWrites(found)).rpbm_piece_am_id, "3365069", "pièce AM retrouvée : écrite");

// Autre pièce choisie, puis désélectionnée.
const chosen = mountStored();
chosen.state.pieces = [oePiece(11), oePiece(12)];
chosen.onSelectPiece(12);
assert.deepEqual(await pieceWrites(chosen), { rpbm_xglass_piece_id: "12", rpbm_piece_oe_id: "22", rpbm_piece_am_id: "" });
chosen.onSelectPiece(12);
assert.deepEqual(await pieceWrites(chosen), CLEARED_PIECES, "désélection");

// Catégorie : un clic sur celle affichée ne change rien, une autre vide la sélection.
const calque = mountStored();
calque.onClickCalque(2);
assert.deepEqual(await pieceWrites(calque), {}, "même catégorie");
calque.onClickCalque(3);
assert.deepEqual(await pieceWrites(calque), CLEARED_PIECES);

// Pièce AM choisie : seule la pièce AM est écrite.
const amChosen = mountStored();
amChosen.onSelectPieceAM({ pieceAm: { id: 3365070, reference: "6108AGNSMVZ" } });
assert.deepEqual(await pieceWrites(amChosen), { rpbm_piece_am_id: "3365070" });

// Véhicule : l'effet automatique et un clic sur le véhicule affiché ne libèrent rien, un autre véhicule si.
const vehicle = mountStored();
vehicle.state.vehicules = [{ id: 1 }, { id: 2 }];
runVehiculesEffect();
vehicle.onClickVehicule(1);
assert.deepEqual(keptFlags(vehicle), [true, true]);
vehicle.onClickVehicule(2);
assert.equal(vehicle.selectedVehicule.id, 2);
assert.deepEqual(keptFlags(vehicle), [false, false]);

// Immatriculation : la recherche de l'ouverture ne libère rien, celle de l'utilisateur si.
const search = mountStored({ rpbm_license_plate: "GS600HH" });
await search.init();
assert.deepEqual(keptFlags(search), [true, true]);
await search.onSearchImmatriculation();
assert.deepEqual(keptFlags(search), [false, false]);

// R24 : une recherche VSF sans article retient la base cherchée ; un résultat ou une erreur l'efface.
const noResult = mount({});
const searchVsf = (base, callPortal) => {
    noResult.callPortal = callPortal;
    noResult.setBaseEurocode(base);
    return noResult.searchBaseEurocode();
};
assert.equal(noResult.state.vsfNoResultFor, undefined);
await searchVsf("9999Z", async () => []);
assert.equal(noResult.state.vsfNoResultFor, "9999Z");
await searchVsf("6108A", async () => [{ code: "6108AGABCHM" }]);
assert.equal(noResult.state.vsfNoResultFor, undefined);
await searchVsf("9999Z", async () => []);
await assert.rejects(searchVsf("61-08A", async () => { throw new Error("portail VSF inaccessible"); }), /inaccessible/);
assert.equal(noResult.state.vsfNoResultFor, undefined, "une erreur ne laisse pas l'ancien message");
await searchVsf("9999Z", async () => []);
noResult.clearSelectedPiece();
assert.equal(noResult.state.vsfNoResultFor, undefined);

// R28 : l'objet renvoyé par addNewRecord n'est pas toujours celui conservé dans records (SO7763).
const deletedLines = [];
const orderLines = {
    records: [{ data: { product_id: [3420, "Présent à l'ouverture"] } }],
    async addNewRecord({ context }) {
        const line = { data: { product_id: [context.default_product_id, "Pare-brise A"] }, async update() {} };
        this.records.push(line);
        return line;
    },
    async delete(line) {
        deletedLines.push(line);
        this.records = this.records.filter(record => record !== line);
    },
};
const quote = mount({ order_line: orderLines }, context.AgentWidgetDialogSaleOrder);
quote.state.articlesVsf = [{ code: "6108AGABCHM", prixVenteRPBM: 80 }, { code: "6574AXSH", prixVenteRPBM: 5 }];
quote.state.articleProducts = { "6108AGABCHM": { id: 9001 }, "6574AXSH": { id: 3420 } };
await quote.addArticleToSaleOrder("6108AGABCHM");
const replacement = { data: { product_id: [9001, "Pare-brise A"] } };
orderLines.records = orderLines.records.map(line => line.data.product_id[0] === 9001 ? replacement : line);
assert.equal(quote.isWidgetArticleInOrder("6108AGABCHM"), true, "« Retirer du devis » après remplacement");
await quote.removeArticleFromSaleOrder("6108AGABCHM");
assert.equal(deletedLines.length, 1);
assert.equal(deletedLines[0], replacement, "la ligne supprimée est celle de records");
assert.equal(quote.isWidgetArticleInOrder("6108AGABCHM"), false);
assert.equal(quote.isArticleAlreadyInOrder("6108AGABCHM"), false);
// Produit présent à l'ouverture : « Article déjà présent », ajout bloqué.
assert.equal(quote.isWidgetArticleInOrder("6574AXSH"), false);
assert.equal(quote.isArticleAlreadyInOrder("6574AXSH"), true);
await quote.addArticleToSaleOrder("6574AXSH");
assert.equal(orderLines.records.length, 1);

// Lot E2 : le devis s'ouvre sans X'Glass (mount() force agentsInitialized, remis à faux ici).
const routes = () => plain(rpcCalls.map(({ route }) => route));
const vsfOnly = (data) => {
    const widget = mount({ order_line: { records: [] }, ...data }, context.AgentWidgetDialogSaleOrder);
    widget.state.agentsInitialized = false;
    return widget;
};
// Cinquième effet de setup(), sur le calque.
const runCalqueEffect = () => runEffect(effects[4]);

// Ouverture avec une base : une recherche, ni authentification ni fermeture des portails.
const opened = vsfOnly({ rpbm_eurocode_base: "6108A" });
await opened.onWillStart();
runVsfEffect();
assert.deepEqual(await vsfSearches(), [{ baseEurocode: "6108A" }]);
await opened.onDiscard();
assert.deepEqual(routes(), ["/searchBaseEurocode"]);

// Sans catégorie X'Glass : base et article principal seulement, sans appel véhicule ; plaque et
// identifiants X'Glass mémorisés restent intacts.
const vsfWrite = vsfOnly({ ...STORED_PIECES, rpbm_eurocode_base: "6108A", rpbm_license_plate: "GS600HH", rpbm_xglass_vehicle_id: "2" });
Object.assign(vsfWrite.state, {
    selectedVehicule: { id: 2 },
    articlesVsf: [{ code: "6108AGABCHM", name: "Pare-brise A", stock: "2", refConstructeur: "OE-A" }],
    selectedArticleCodes: { "6108AGABCHM": true },
    primaryArticleCode: "6108AGABCHM",
});
assert.deepEqual(plain(await vsfWrite.getRecordData()), {
    rpbm_eurocode_base: "6108A",
    rpbm_eurocode: "6108AGABCHM",
    rpbm_vsf_designation: "Pare-brise A",
    rpbm_vsf_stock: 2,
    rpbm_constructor_reference: "OE-A",
});
assert.deepEqual(routes(), []);

// Véhicule et catégorie choisis : écriture complète, libellé de la pièce compris.
const fullWrite = mount({ ...STORED_PIECES, rpbm_eurocode_base: "6108A", order_line: { records: [] } }, context.AgentWidgetDialogSaleOrder);
Object.assign(fullWrite.state, { selectedVehicule: { id: 2 }, vehiculeMeta: {}, planche: { id: 1, calques }, selectedCalque: calques[0] });
fullWrite.getOdooVehicule = async () => ({ id: 5, name: "PEUGEOT/208/GS600HH" });
fullWrite.callPortal = async () => [{ id: 11, pieceOe: { id: 21, libelle: "Pare-brise athermique", referenceClean: "6108AGNSMVZ1B" } }];
assert.equal("rpbm_xglass_piece_label" in await fullWrite.getRecordData(), false, "pièce pas encore retrouvée : libellé conservé");
await fullWrite.getPieces();
const fullData = plain(await fullWrite.getRecordData());
assert.deepEqual(
    [fullData.rpbm_vehicle_id, fullData.rpbm_xglass_category, fullData.rpbm_xglass_vehicle_id, fullData.rpbm_xglass_piece_id, fullData.rpbm_eurocode_base],
    [[5, "PEUGEOT/208/GS600HH"], "PARE-BRISE", "2", "11", "6108A"],
);
assert.equal(fullData.rpbm_xglass_piece_label, "Pare-brise athermique — réf. 6108AGNSMVZ1B");
fullWrite.state.selectedPiece = undefined;
fullWrite.state.selectedPieceAm = { pieceAm: { id: 3365070, reference: "6108AGNSMVZ", fournisseur: { libelle: "PILKINGTON" } } };
assert.equal(fullWrite.xglassPieceLabel, "AM 6108AGNSMVZ (PILKINGTON)");
fullWrite.state.selectedPieceAm = undefined;
assert.equal(fullWrite.xglassPieceLabel, "");

// Restauration du calque : la pièce est vidée, le tableau et la sélection VSF restent.
const keptVsf = mount({ rpbm_eurocode_base: "6108A" });
Object.assign(keptVsf.state, {
    articlesVsf: [{ code: "6108AGABCHM" }],
    selectedArticleCodes: { "6108AGABCHM": true },
    primaryArticleCode: "6108AGABCHM",
    selectedPiece: { id: 11 },
    selectedPieceAm: { pieceAm: { id: 3365069 } },
});
keptVsf._lastSearchedBaseEurocode = "6108A";
keptVsf.clearSelectedPiece(true);
assert.deepEqual(
    plain([keptVsf.selectedPiece, keptVsf.selectedPieceAm, keptVsf.baseEurocode, keptVsf.articlesVsf, keptVsf.state.selectedArticleCodes, keptVsf.state.primaryArticleCode, keptVsf._lastSearchedBaseEurocode]),
    plain([undefined, undefined, "6108A", [{ code: "6108AGABCHM" }], { "6108AGABCHM": true }, "6108AGABCHM", "6108A"]),
);

// « Charger X'Glass » : agentsInitialized passe à vrai sans relancer la recherche.
const loading = vsfOnly({ rpbm_eurocode_base: "6108A" });
loading.rpc = async (route, params) => {
    rpcCalls.push({ route, params });
    return route === "/searchBaseEurocode" ? [{ code: "6108AGABCHM" }] : [];
};
runVsfEffect();
assert.deepEqual(await vsfSearches(), [{ baseEurocode: "6108A" }]);
loading.state.agentsInitialized = true;
runVsfEffect();
assert.deepEqual(await vsfSearches(), [{ baseEurocode: "6108A" }]);

// La pièce concernée enregistrée survit à la restauration du calque (suggestion : pare-brise).
const partType = vsfOnly({ rpbm_part_type: "rear_window", rpbm_eurocode_base: "6108A" });
partType.state.planche = { id: 1, calques };
runCalqueEffect();
partType.state.selectedCalque = calques[0];
runCalqueEffect();
assert.equal(partType.pieceConcernee, "rear_window");

// Recherche périmée (base modifiée pendant la recherche) : ni sa réponse tardive ni son échec
// n'écrasent la recherche en cours.
const stale = mount({});
const pending = {};
stale.callPortal = (route, { baseEurocode }) => new Promise((resolve, reject) => { pending[baseEurocode] = { resolve, reject }; });
const staleSearch = (base) => { stale.setBaseEurocode(base); return stale.searchBaseEurocode(); };
const late = staleSearch("6108A");
const current = staleSearch("6574A");
pending["6574A"].resolve([{ code: "6574AGACIMVZ" }]);
await current;
pending["6108A"].resolve([{ code: "6108AGABCHM" }]);
await late;
assert.deepEqual(plain(stale.articlesVsf), [{ code: "6574AGACIMVZ" }], "réponse tardive ignorée");
const failed = staleSearch("7310A");
const next = staleSearch("6108A");
pending["7310A"].reject(new Error("portail VSF inaccessible"));
await assert.rejects(failed, /inaccessible/);
pending["6108A"].resolve([{ code: "6108AGABCHM" }]);
await next;
assert.deepEqual(plain(stale.articlesVsf), [{ code: "6108AGABCHM" }], "échec périmé sans effet sur la recherche en cours");

// Revue E2, A : devis avec une catégorie mais ni base ni pièce. Base saisie, article principal choisi,
// puis « Charger X'Glass » et la vraie chaîne (véhicule, planche, calque de la catégorie) : rien n'est perdu.
const settleEffects = async () => {
    for (let round = 0; round < 6; round++) {
        effects.forEach(runEffect);
        await new Promise(resolve => setImmediate(resolve));
    }
};
const chain = vsfOnly({ rpbm_xglass_category: "PARE-BRISE", rpbm_part_type: "rear_window", rpbm_license_plate: "GS600HH" });
chain.rpc = async (route, params) => {
    rpcCalls.push({ route, params });
    return {
        "/searchBaseEurocode": [{ code: "7310AGABCHM" }],
        "/searchImmatriculation": [{ id: 471612 }],
        "/rpbm_agent/getVehiculeMeta": { meta: {}, planche: { id: 26881, calques } },
    }[route] || [];
};
await settleEffects();
chain.onChangeBaseEurocode({ target: { value: "7310A" } });
await settleEffects();
Object.assign(chain.state, { selectedArticleCodes: { "7310AGABCHM": true }, primaryArticleCode: "7310AGABCHM" });
await chain.startAgents();
await settleEffects();
assert.equal(chain.selectedCalque?.libelle, "PARE-BRISE", "la chaîne a restauré la catégorie");
assert.deepEqual(routes().filter(route => route === "/getPieces"), ["/getPieces"]);
assert.deepEqual(
    plain([chain.baseEurocode, chain.articlesVsf, chain.state.selectedArticleCodes, chain.getPrimaryArticle()?.code, chain.pieceConcernee]),
    ["7310A", [{ code: "7310AGABCHM" }], { "7310AGABCHM": true }, "7310AGABCHM", "rear_window"],
);
assert.deepEqual(await vsfSearches(), [{ baseEurocode: "7310A" }]);

// Revue E2, B : seule une pièce « Autres marques AM » mémorisée, non retrouvée : son libellé reste
// (opportunité, et devis après « Charger X'Glass »).
for (const Dialog of [context.AgentWidgetDialogCrmLead, context.AgentWidgetDialogSaleOrder]) {
    const amOnly = mount({ rpbm_piece_am_id: "3365069", rpbm_xglass_piece_label: "AM 6108AGNSMVZ (PILKINGTON)", order_line: { records: [] } }, Dialog);
    Object.assign(amOnly.state, { selectedVehicule: { id: 2 }, vehiculeMeta: {}, selectedCalque: calques[0] });
    amOnly.getOdooVehicule = async () => ({ id: 5, name: "PEUGEOT/208/GS600HH" });
    assert.equal("rpbm_xglass_piece_label" in await amOnly.getRecordData(), false, Dialog.name);
}

// Revue E2, C : une base sans résultat n'est pas recherchée de nouveau par les effets ; le bouton la relance (R24).
const noArticle = vsfOnly({ rpbm_eurocode_base: "9999Z" });
runVsfEffect();
assert.deepEqual(await vsfSearches(), [{ baseEurocode: "9999Z" }]);
noArticle.state.agentsInitialized = true;
runVsfEffect();
noArticle.state.selectedPiece = { id: 11 };
runVsfEffect();
assert.deepEqual(await vsfSearches(), [{ baseEurocode: "9999Z" }], "ni X'Glass chargé ni pièce restaurée ne la relancent");
noArticle.onSearchBaseEurocode(true);
assert.deepEqual(await vsfSearches(), [{ baseEurocode: "9999Z" }, { baseEurocode: "9999Z" }], "le bouton la relance");

// Revue E2, D : deux « Charger X'Glass » rapprochés ne font qu'une authentification.
const twice = vsfOnly({ rpbm_eurocode_base: "6108A" });
const firstLoad = twice.startAgents();
assert.equal(twice.state.xglassLoading, true);
await Promise.all([firstLoad, twice.startAgents()]);
assert.deepEqual(routes().filter(route => route === "/rpbm_agent_auth"), ["/rpbm_agent_auth"]);
assert.equal(twice.state.xglassLoading, false);

// Revue E2 : dialog fermé pendant « Charger X'Glass ». Le verrou pris entre-temps est rendu par un seul
// /rpbm_agent_close, sans autre appel ni état modifié après la destruction.
const closing = vsfOnly({ rpbm_eurocode_base: "6108A", rpbm_license_plate: "GS600HH" });
let resolveAuth;
const authResponse = new Promise(resolve => { resolveAuth = resolve; });
const served = [];
const serve = (route) => { served.push(route); return route === "/rpbm_agent_auth" ? authResponse : Promise.resolve([]); };
closing.env = { services: { rpc: serve } };
// rpc de useService : comme _protectMethod d'Odoo, il ne résout plus après la destruction.
closing.rpc = (route) => serve(route).then(result => closing.testStatus === "destroyed" ? new Promise(() => {}) : result);
closing.startAgents();
await closing.onDiscard();
closing.testStatus = "destroyed";
const stateAtDestroy = JSON.stringify(closing.state);
resolveAuth([]);
await new Promise(resolve => setImmediate(resolve));
assert.deepEqual(served, ["/rpbm_agent_auth", "/rpbm_agent_close"]);
assert.equal(JSON.stringify(closing.state), stateAtDestroy);

vm.runInNewContext(`${await load("ArticleComponent.js")}\nthis.ArticleComponent = ArticleComponent;`, context);

const openedImages = [];
const article = Object.create(context.ArticleComponent.prototype);
article.props = {
    article: {
        images: [
            { thumbnailUrl: "sm-1", fullUrl: "xlg-1" },
            { thumbnailUrl: "sm-2", fullUrl: "xlg-2" },
        ],
    },
    onOpenImage: (...args) => openedImages.push(args),
};
const click = (overrides = {}) => ({
    button: 0,
    ctrlKey: false,
    metaKey: false,
    shiftKey: false,
    altKey: false,
    stopped: 0,
    prevented: 0,
    stopPropagation() { this.stopped += 1; },
    preventDefault() { this.prevented += 1; },
    ...overrides,
});
const simpleClick = click();
article.openImage(simpleClick, "xlg-2");
assert.deepEqual(openedImages, [[ ["xlg-1", "xlg-2"], 1 ]]);
assert.equal(simpleClick.stopped, 1);
assert.equal(simpleClick.prevented, 1);

const ctrlClick = click({ ctrlKey: true });
article.openImage(ctrlClick, "xlg-2");
assert.equal(openedImages.length, 1);
assert.equal(ctrlClick.stopped, 1);
assert.equal(ctrlClick.prevented, 0);

const middleClick = click({ button: 1 });
article.stopImagePropagation(middleClick);
assert.equal(middleClick.stopped, 1);
assert.equal(middleClick.prevented, 0);

const hotkeys = [];
const previewContext = {
    Component: emptyComponent,
    Dialog: emptyComponent,
    useState: (state) => state,
    useHotkey: (key, callback, options) => hotkeys.push({ key, callback, options }),
};
const previewSource = (await readFile(new URL("./static/src/VsfImagePreviewDialog.js", import.meta.url), "utf8"))
    .replace(/^import[\s\S]*?;\n/gm, "")
    .replace("export class VsfImagePreviewDialog", "class VsfImagePreviewDialog");
vm.runInNewContext(`${previewSource}\nthis.VsfImagePreviewDialog = VsfImagePreviewDialog;`, previewContext);

const preview = Object.create(previewContext.VsfImagePreviewDialog.prototype);
preview.props = { images: ["xlg-1", "xlg-2"], index: 0 };
preview.setup();
assert.deepEqual(hotkeys.map(({ key, options }) => [key, options.allowRepeat]), [
    ["arrowleft", true],
    ["arrowright", true],
]);
hotkeys[1].callback();
assert.equal(preview.imageUrl, "xlg-2");
hotkeys[1].callback();
assert.equal(preview.imageUrl, "xlg-1");
hotkeys[0].callback();
assert.equal(preview.imageUrl, "xlg-2");

const singlePreview = Object.create(previewContext.VsfImagePreviewDialog.prototype);
singlePreview.props = { images: ["xlg-unique"], index: 0 };
singlePreview.setup();
singlePreview.move(1);
assert.equal(singlePreview.imageUrl, "xlg-unique");
