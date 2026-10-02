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
