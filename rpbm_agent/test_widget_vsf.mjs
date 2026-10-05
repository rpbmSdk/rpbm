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
