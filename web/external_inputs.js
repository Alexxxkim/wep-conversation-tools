import { app } from "../../scripts/app.js";

const SELECTOR = "DMCanvasStyleSelector";
const STYLE_PROPERTY = "dmcanvas_style_names";
const BACKUP_PROPERTY = "dmcanvas_legacy_inputs";
const MAX_STYLES = 64;
const ADD_BUTTON = "+ 新增风格接口";
const NODE_INPUTS = {
    DMCanvasDrawingHistoryToConversation: ["text"],
    DMCanvasIntentInputJSONWithMetadata: ["conversation", "region", "style"],
};

function normalizeName(value) {
    return value.trim().replace(/\s+/g, " ").toLowerCase();
}

function readNames(node, defaults) {
    return node.properties?.[STYLE_PROPERTY] ?? structuredClone(defaults);
}

function styleLabel(aliases) {
    return aliases[0].trim() || "（空风格）";
}

function resizeNode(node) {
    const size = node.computeSize();
    size[0] = Math.max(360, node.size?.[0] ?? 0, size[0]);
    node.setSize(size);
    node.setDirtyCanvas?.(true, true);
}

function ensureSocket(node, name, optional = false, label) {
    let input = node.inputs?.find((entry) => entry.name === name);
    if (!input) {
        node.addInput(name, "STRING", optional ? { shape: 7 } : {});
        input = node.inputs.find((entry) => entry.name === name);
    }
    input.type = "STRING";
    delete input.widget;
    if (label !== undefined) input.label = label;
}

function removeTextWidgets(node, names) {
    node.properties ??= {};
    for (let index = (node.widgets?.length ?? 0) - 1; index >= 0; index -= 1) {
        const widget = node.widgets[index];
        if (!names.includes(widget.name) && !/^style_[1-9][0-9]*$/.test(widget.name)) continue;
        if (widget.value !== undefined && widget.value !== null && widget.value !== "") {
            node.properties[BACKUP_PROPERTY] ??= {};
            node.properties[BACKUP_PROPERTY][widget.name] = widget.value;
        }
        widget.onRemove?.();
        node.widgets.splice(index, 1);
    }
}

function updateStyles(node, names, defaults) {
    node.properties ??= {};
    node.properties[STYLE_PROPERTY] = names;
    removeTextWidgets(node, ["style", "style_names", ...Object.keys(defaults), ...Object.keys(names)]);
    for (let index = (node.inputs?.length ?? 0) - 1; index >= 0; index -= 1) {
        const name = node.inputs[index].name;
        if (name === "style_names" || (name !== "style" && !Object.hasOwn(names, name))) {
            node.removeInput(index);
        }
    }
    ensureSocket(node, "style");
    for (const [name, aliases] of Object.entries(names)) {
        ensureSocket(node, name, true, styleLabel(aliases));
    }
    resizeNode(node);
}

function duplicateName(names, value, exceptInput) {
    const normalized = normalizeName(value);
    return Object.entries(names).some(([name, aliases]) =>
        name !== exceptInput && aliases.some((alias) => normalizeName(alias) === normalized),
    );
}

async function askName(title, defaultValue) {
    if (app.extensionManager?.dialog?.prompt) {
        return app.extensionManager.dialog.prompt({ title, message: "输入风格名称；留空表示空风格。", defaultValue });
    }
    return new Promise((resolve) => app.canvas.prompt(title, defaultValue, resolve));
}

async function showAlert(title, message) {
    if (app.extensionManager?.dialog?.alert) {
        await app.extensionManager.dialog.alert({ title, message });
    } else {
        app.ui.dialog.show(`${title}：${message}`);
    }
}

async function addStyle(node, defaults) {
    const names = readNames(node, defaults);
    if (Object.keys(names).length >= MAX_STYLES) {
        await showAlert("风格接口已满", "每个选择器最多支持 64 个风格；可以删除不需要的风格。");
        return;
    }
    const value = await askName("新增风格接口", "新风格");
    if (value == null) return;
    if (duplicateName(names, value)) {
        await showAlert("名称重复", "请使用不同的风格名称。");
        return;
    }
    let index = 1;
    while (Object.hasOwn(names, `style_${index}`)) index += 1;
    names[`style_${index}`] = [value.trim()];
    updateStyles(node, names, defaults);
}

async function renameStyle(node, name, defaults) {
    const names = readNames(node, defaults);
    const value = await askName("修改风格名称", names[name][0]);
    if (value == null) return;
    if (duplicateName(names, value, name)) {
        await showAlert("名称重复", "请使用不同的风格名称。");
        return;
    }
    names[name] = [value.trim()];
    updateStyles(node, names, defaults);
}

function removeStyle(node, name, defaults) {
    const names = readNames(node, defaults);
    delete names[name];
    updateStyles(node, names, defaults);
}

function legacyConfiguration(serializedNode, fields, defaults) {
    const properties = { ...serializedNode.properties };
    const values = serializedNode.widgets_values;
    if (!Array.isArray(values) || !values.length) return { ...serializedNode, properties };
    properties.dmcanvas_legacy_widgets = values.slice();
    if (defaults && !properties[STYLE_PROPERTY]) {
        for (const value of values.slice(0, 2)) {
            if (typeof value !== "string") continue;
            try {
                const names = JSON.parse(value);
                if (names && !Array.isArray(names) && typeof names === "object" &&
                    Object.entries(names).every(([name, aliases]) =>
                        (Object.hasOwn(defaults, name) || /^style_[1-9][0-9]*$/.test(name)) &&
                        Array.isArray(aliases) && aliases.length && aliases.every((alias) => typeof alias === "string"),
                    )) {
                    properties[STYLE_PROPERTY] = names;
                    return { ...serializedNode, properties };
                }
            } catch {}
        }
    }
    properties[BACKUP_PROPERTY] = { ...properties[BACKUP_PROPERTY] };
    fields.forEach((name, index) => {
        if (values[index] !== undefined && values[index] !== null && values[index] !== "") {
            properties[BACKUP_PROPERTY][name] = values[index];
        }
    });
    return { ...serializedNode, properties };
}

app.registerExtension({
    name: "DMCanvas.ExternalTextSockets",
    beforeRegisterNodeDef(nodeType, nodeData) {
        const selector = nodeData.name === SELECTOR;
        const fields = selector ? ["style", "style_names", "cutout", "emoji", "retro", "cartoon", "empty"] : NODE_INPUTS[nodeData.name];
        if (!fields) return;
        const defaults = selector ? nodeData.input.required.style[1].dmcanvas_style_names : undefined;
        const restore = (node) => {
            if (selector) {
                updateStyles(node, readNames(node, defaults), defaults);
            } else {
                removeTextWidgets(node, fields);
                fields.forEach((name, index) => ensureSocket(node, name, index > 0));
                resizeNode(node);
            }
        };
        const configure = nodeType.prototype.configure;
        nodeType.prototype.configure = function (serializedNode) {
            return configure?.call(this, legacyConfiguration(serializedNode, fields, defaults));
        };
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);
            restore(this);
            if (selector) {
                this.addWidget("button", ADD_BUTTON, null, () => addStyle(this, defaults), { serialize: false });
                resizeNode(this);
            }
            return result;
        };
        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            const result = onConfigure?.apply(this, arguments);
            restore(this);
            return result;
        };
        if (!selector) return;
        const getExtraMenuOptions = nodeType.prototype.getExtraMenuOptions;
        nodeType.prototype.getExtraMenuOptions = function (_, options) {
            const result = getExtraMenuOptions?.apply(this, arguments);
            const entries = Object.entries(readNames(this, defaults));
            options.push(
                { content: ADD_BUTTON, callback: () => addStyle(this, defaults) },
                { content: "修改风格名称", submenu: { options: entries.map(([name, aliases]) => ({
                    content: styleLabel(aliases), callback: () => renameStyle(this, name, defaults),
                })) } },
                { content: "删除风格接口（断开该接口连线）", submenu: { options: entries.map(([name, aliases]) => ({
                    content: styleLabel(aliases), callback: () => removeStyle(this, name, defaults),
                })) } },
            );
            return result;
        };
    },
});
