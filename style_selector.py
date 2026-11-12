import json
import re


DEFAULT_STYLE_NAMES = {
    "cutout": ["cutout"],
    "emoji": ["3d emoji", "3demoji"],
    "retro": ["retro game", "retrogame"],
    "cartoon": ["cartoon"],
    "empty": ["none", ""],
}
STYLE_INPUTS = tuple(DEFAULT_STYLE_NAMES) + tuple(f"style_{index}" for index in range(1, 60))
DEFAULT_STYLE_CONFIG = json.dumps(DEFAULT_STYLE_NAMES, ensure_ascii=False)


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
    seen = set()
    for input_name, aliases in names.items():
        if input_name not in STYLE_INPUTS:
            raise ValueError(f"无效的风格接口：{input_name}。")
        if not isinstance(aliases, list) or not aliases or not all(isinstance(alias, str) for alias in aliases):
            raise ValueError(f"{input_name} 的风格名称必须是非空文本列表。")
        normalized = {normalize_name(alias) for alias in aliases}
        if seen.intersection(normalized):
            raise ValueError("风格名称重复；请使用不同名称。")
        seen.update(normalized)
    return names


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
    DESCRIPTION = "Route external STRING inputs by editable style names. Add styles with the button; rename or remove them in the node menu."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "style": ("STRING", {"forceInput": True}),
                "style_names": ("STRING", {
                    "default": DEFAULT_STYLE_CONFIG, "dynamicPrompts": False,
                    "socketless": True,
                }),
            },
            "optional": {
                name: ("STRING", {
                    "forceInput": True, "lazy": True,
                })
                for name in STYLE_INPUTS
            },
        }

    @classmethod
    def VALIDATE_INPUTS(cls, style_names=DEFAULT_STYLE_CONFIG):
        try:
            parse_style_names(style_names)
        except ValueError as error:
            return str(error)
        return True

    def check_lazy_status(self, style, style_names=DEFAULT_STYLE_CONFIG, **prompts):
        name = selected_input(style, style_names)
        if name in prompts and prompts[name] is None:
            return [name]
        return []

    def select(self, style, style_names=DEFAULT_STYLE_CONFIG, **prompts):
        name = selected_input(style, style_names)
        prompt = prompts.get(name, "")
        if not isinstance(prompt, str):
            raise ValueError(f"选中的 {name} 输入必须是文本。")
        return (prompt,)
