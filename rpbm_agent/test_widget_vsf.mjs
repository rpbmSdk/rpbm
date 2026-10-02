import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";

const source = (await readFile(new URL("./static/src/agent_widget_dialog.js", import.meta.url), "utf8"))
    .replace(/^import[\s\S]*?;\n/gm, "")
    .replace("export class AgentWidgetDialog", "class AgentWidgetDialog");
const emptyComponent = class {};
const context = {
    asyncWidget: emptyComponent,
    Dialog: emptyComponent,
    VehiculeComponent: emptyComponent,
    CalqueComponent: emptyComponent,
    PieceComponent: emptyComponent,
    PieceAMComponent: emptyComponent,
    ArticleComponent: emptyComponent,
    VsfImagePreviewDialog: emptyComponent,
};
vm.runInNewContext(`${source}\nthis.AgentWidgetDialog = AgentWidgetDialog;`, context);

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

const articleSource = (await readFile(new URL("./static/src/ArticleComponent.js", import.meta.url), "utf8"))
    .replace(/^import[\s\S]*?;\n/gm, "")
    .replace("export class ArticleComponent", "class ArticleComponent");
vm.runInNewContext(`${articleSource}\nthis.ArticleComponent = ArticleComponent;`, context);

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
