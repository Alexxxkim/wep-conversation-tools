import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";

const defaults = {
    cutout: ["cutout"], emoji: ["3d emoji", "3demoji"],
    retro: ["retro game", "retrogame"], cartoon: ["cartoon"], empty: ["none", ""],
};
const answers = [];
const alerts = [];
let extension;
const app = {
    registerExtension(value) { extension = value; },
    extensionManager: { dialog: {
        async prompt() { return answers.shift(); },
        async alert(value) { alerts.push(value); },
    } },
    canvas: { prompt(title, value, callback) { callback(answers.shift()); } },
    ui: { dialog: { show(message) { alerts.push({ message }); } } },
};
const context = vm.createContext({ app, structuredClone });
const source = await readFile(new URL("../web/external_inputs.js", import.meta.url), "utf8");
const module = new vm.SourceTextModule(source, { context });
await module.link(async () => new vm.SourceTextModule("export const app = globalThis.app;", { context }));
await module.evaluate();

class BaseNode {
    constructor(fields) {
        this.properties = {};
        this.inputs = fields.map((name) => ({ name, type: "*", link: null }));
        this.widgets = [];
        this.onNodeCreated();
    }
    configure(serializedNode) {
        this.properties = structuredClone(serializedNode.properties ?? {});
        this.inputs = structuredClone(serializedNode.inputs ?? []);
        this.onConfigure();
    }
    addInput(name, type, options = {}) { this.inputs.push({ name, type, link: null, ...options }); }
    removeInput(index) { this.inputs.splice(index, 1); }
    addWidget(type, name, value, callback, options) {
        const widget = { type, name, value, callback, options };
        this.widgets.push(widget);
        return widget;
    }
    computeSize() { return [300, 80 + this.inputs.length * 20 + this.widgets.length * 30]; }
    setSize(size) { this.size = size; }
    setDirtyCanvas() {}
}

class SelectorNode extends BaseNode {
    constructor() { super(["style", ...Object.keys(defaults)]); }
}
class HistoryNode extends BaseNode {
    constructor() { super(["text"]); }
}
class IntentNode extends BaseNode {
    constructor() { super(["conversation", "region", "style"]); }
}
extension.beforeRegisterNodeDef(SelectorNode, {
    name: "DMCanvasStyleSelector",
    input: { required: { style: ["*", { forceInput: true, dmcanvas_style_names: defaults }] } },
});
extension.beforeRegisterNodeDef(HistoryNode, { name: "DMCanvasDrawingHistoryToConversation" });
extension.beforeRegisterNodeDef(IntentNode, { name: "DMCanvasIntentInputJSONWithMetadata" });

const configuration = (node) => JSON.parse(JSON.stringify(node.properties.dmcanvas_style_names));
const add = async (node, name) => { answers.push(name); await node.widgets.find((widget) => widget.type === "button").callback(); };
const menu = (node) => { const options = []; node.getExtraMenuOptions(null, options); return options; };
const node = new SelectorNode();
assert.deepEqual(node.inputs.map((input) => input.name), ["style", ...Object.keys(defaults)]);
assert.deepEqual(node.inputs.slice(1).map((input) => input.label), ["cutout", "3d emoji", "retro game", "cartoon", "none"]);
assert.ok(node.inputs.every((input) => input.type === "*" && !input.widget));
assert.equal(node.widgets.length, 1);
assert.equal(node.widgets[0].type, "button");
assert.equal(node.widgets[0].options.serialize, false);
assert.deepEqual(configuration(node), defaults);

await add(node, "水彩");
assert.deepEqual(configuration(node).style_1, ["水彩"]);
assert.equal(node.inputs.at(-1).label, "水彩");
for (let index = 2; index <= 8; index += 1) await add(node, `Custom ${index}`);
assert.equal(Object.keys(configuration(node)).length, 13);

const connectedInput = node.inputs.find((input) => input.name === "cartoon");
connectedInput.link = 123;
answers.push("油画");
await menu(node)[1].submenu.options.find((entry) => entry.content === "cartoon").callback();
assert.deepEqual(configuration(node).cartoon, ["油画"]);
assert.equal(connectedInput.label, "油画");
assert.equal(connectedInput.link, 123);

const beforeDuplicate = configuration(node);
await add(node, " 水彩 ");
assert.deepEqual(configuration(node), beforeDuplicate);
assert.equal(alerts.at(-1).title, "名称重复");
await add(node, null);
assert.deepEqual(configuration(node), beforeDuplicate);

const reloaded = new SelectorNode();
reloaded.configure({ inputs: node.inputs, properties: node.properties, widgets_values: [] });
assert.deepEqual(configuration(reloaded), configuration(node));
assert.equal(reloaded.inputs.find((input) => input.name === "cartoon").link, 123);
assert.equal(reloaded.inputs.find((input) => input.name === "style_1").label, "水彩");
assert.equal(reloaded.widgets.length, 1);

menu(node)[2].submenu.options.find((entry) => entry.content === "水彩").callback();
assert.equal(configuration(node).style_1, undefined);
assert.equal(node.inputs.some((input) => input.name === "style_1"), false);
await add(node, "铅笔");
assert.deepEqual(configuration(node).style_1, ["铅笔"]);

while (Object.keys(configuration(node)).length < 64) await add(node, `Remaining ${node.inputs.length}`);
const fullConfig = configuration(node);
await node.widgets[0].callback();
assert.deepEqual(configuration(node), fullConfig);
assert.equal(alerts.at(-1).title, "风格接口已满");

const legacy = new SelectorNode();
legacy.widgets.push({ name: "style", value: "cartoon" }, { name: "style_names", value: JSON.stringify(defaults) });
for (let index = 1; index <= 59; index += 1) {
    legacy.addInput(`style_${index}`, "STRING", { widget: { name: `style_${index}` } });
    legacy.widgets.push({ name: `style_${index}`, value: index === 1 ? "Keep this legacy text" : "" });
}
legacy.configure({
    inputs: legacy.inputs,
    properties: {},
    widgets_values: ["cartoon", JSON.stringify(defaults), "", "", "123", "", ""],
});
assert.deepEqual(legacy.inputs.map((input) => input.name), ["style", ...Object.keys(defaults)]);
assert.equal(legacy.widgets.length, 1);
assert.equal(legacy.properties.dmcanvas_legacy_inputs.style, "cartoon");
assert.equal(legacy.properties.dmcanvas_legacy_inputs.style_1, "Keep this legacy text");
assert.equal(legacy.properties.dmcanvas_legacy_widgets[4], "123");

const legacyCustom = new SelectorNode();
const customNames = { ...defaults, style_1: ["水彩"] };
legacyCustom.configure({
    inputs: [...legacy.inputs, { name: "style_1", type: "STRING", link: 456 }],
    properties: {}, widgets_values: [JSON.stringify(customNames)],
});
assert.deepEqual(configuration(legacyCustom), customNames);
assert.equal(legacyCustom.inputs.at(-1).link, 456);
assert.equal(legacyCustom.inputs.at(-1).type, "*");

for (const [NodeClass, fields, values] of [
    [HistoryNode, ["text"], ["Original history"]],
    [IntentNode, ["conversation", "region", "style"], ["user: test", "[locale=zh-CN]", "style: cartoon"]],
]) {
    const textNode = new NodeClass();
    assert.deepEqual(textNode.inputs.map((input) => input.name), fields);
    assert.equal(textNode.widgets.length, 0);
    textNode.widgets = fields.map((name, index) => ({ name, value: values[index] }));
    textNode.configure({
        inputs: [{ name: fields[0], type: "STRING", link: 789, widget: { name: fields[0] } }],
        properties: {}, widgets_values: values,
    });
    assert.deepEqual(textNode.inputs.map((input) => input.name), fields);
    assert.equal(textNode.inputs[0].link, 789);
    assert.ok(textNode.inputs.every((input) => input.type === "*" && !input.widget));
    assert.equal(textNode.widgets.length, 0);
    assert.deepEqual(textNode.properties.dmcanvas_legacy_inputs, Object.fromEntries(fields.map((name, index) => [name, values[index]])));
}

app.extensionManager = undefined;
const fallback = new SelectorNode();
await add(fallback, "Legacy dialog style");
assert.deepEqual(configuration(fallback).style_1, ["Legacy dialog style"]);
await add(fallback, "cartoon");
assert.match(alerts.at(-1).message, /名称重复/);
console.log("Frontend checks passed: sockets on all nodes, five defaults only, add/rename/remove, save/reload, legacy text backups and dialogs, and 64-style limit.");
