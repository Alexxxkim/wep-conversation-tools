import json
import re


DEFAULT_STYLE_NAMES = {
    "cutout": ["cutout"],
    "emoji": ["3d emoji", "3demoji"],
    "retro": ["retro game", "retrogame"],
    "cartoon": ["cartoon"],
    "empty": ["none", ""],
}
STYLE_INPUTS = tuple(DEFAULT_STYLE_NAMES)
MAX_STYLES = 64
DEFAULT_STYLE_CONFIG = json.dumps(DEFAULT_STYLE_NAMES, ensure_ascii=False)
STYLE_PROPERTY = "dmcanvas_style_names"


def is_style_input(name):
    return isinstance(name, str) and (name in STYLE_INPUTS or re.fullmatch(r"style_[1-9][0-9]*", name) is not None)


class StyleInputs(dict):
    def __contains__(self, name):
        return is_style_input(name)

    def __getitem__(self, name):
        if not is_style_input(name):
            raise KeyError(name)
        return "*", {"forceInput": True, "lazy": True}


def normalize_name(value):
    return " ".join(value.split()).casefold()


def parse_style_names(style_names):
    if not isinstance(style_names, str):
        raise ValueError("风格配置必须是 JSON 文本。")
    try:
        names = json.loads(style_names)
    except json.JSONDecodeError as error:
        raise ValueError("风格配置不是合法 JSON。") from error
    if not isinstance(names, dict):
        raise ValueError("风格配置必须是接口到名称的映射。")
    if len(names) > MAX_STYLES:
        raise ValueError(f"每个选择器最多支持 {MAX_STYLES} 个风格。")
    seen = set()
    for input_name, aliases in names.items():
        if not is_style_input(input_name):
            raise ValueError(f"无效的风格接口：{input_name}。")
        if not isinstance(aliases, list) or not aliases or not all(isinstance(alias, str) for alias in aliases):
            raise ValueError(f"{input_name} 的风格名称必须是非空文本列表。")
        normalized = {normalize_name(alias) for alias in aliases}
        if seen.intersection(normalized):
            raise ValueError("风格名称重复；请使用不同名称。")
        seen.update(normalized)
    return names


def workflow_style_names(extra_pnginfo, unique_id, fallback=DEFAULT_STYLE_CONFIG):
    if not isinstance(extra_pnginfo, dict) or unique_id is None:
        return fallback
    workflow = extra_pnginfo.get("workflow")
    if not isinstance(workflow, dict) or not isinstance(workflow.get("nodes"), list):
        return fallback
    for node in workflow["nodes"]:
        if not isinstance(node, dict) or str(node.get("id")) != str(unique_id):
            continue
        properties = node.get("properties", {})
        if not isinstance(properties, dict) or STYLE_PROPERTY not in properties:
            return fallback
        return json.dumps(properties[STYLE_PROPERTY], ensure_ascii=False)
    return fallback


def selected_input(style, style_names=DEFAULT_STYLE_CONFIG):
    if not isinstance(style, str):
        raise ValueError("Style 必须是文本。")
    value = style.strip()
    field = re.fullmatch(r"style\s*[:：]\s*(.*)", value, re.IGNORECASE | re.DOTALL)
    if field:
        value = field.group(1).strip()
    normalized = normalize_name(value)
    for input_name, aliases in parse_style_names(style_names).items():
        if normalized in {normalize_name(alias) for alias in aliases}:
            return input_name
    raise ValueError("不支持的 Style；请添加或修改对应的风格名称。")


class StyleSelector:
    CATEGORY = "DM Canvas/Style"
    FUNCTION = "select"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("out",)
    DESCRIPTION = "Route external text sockets by editable style names. Only five style sockets exist by default; add styles with the button."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "style": ("*", {
                    "forceInput": True, "dmcanvas_style_names": DEFAULT_STYLE_NAMES,
                }),
            },
            "optional": StyleInputs({
                name: ("*", {"forceInput": True, "lazy": True})
                for name in STYLE_INPUTS
            }),
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    @classmethod
    def VALIDATE_INPUTS(cls, style_names=DEFAULT_STYLE_CONFIG):
        try:
            parse_style_names(style_names)
        except ValueError as error:
            return str(error)
        return True

    @classmethod
    def IS_CHANGED(cls):
        return float("nan")

    def check_lazy_status(self, style, style_names=DEFAULT_STYLE_CONFIG, extra_pnginfo=None, unique_id=None, **prompts):
        configuration = workflow_style_names(extra_pnginfo, unique_id, style_names)
        name = selected_input(style, configuration)
        if name in prompts and prompts[name] is None:
            return [name]
        return []

    def select(self, style, style_names=DEFAULT_STYLE_CONFIG, extra_pnginfo=None, unique_id=None, **prompts):
        configuration = workflow_style_names(extra_pnginfo, unique_id, style_names)
        name = selected_input(style, configuration)
        prompt = prompts.get(name, "")
        if not isinstance(prompt, str):
            raise ValueError(f"选中的 {name} 输入必须是文本。")
        return (prompt,)
