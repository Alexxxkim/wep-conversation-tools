import re


STYLE_INPUTS = ("cutout", "emoji", "retro", "cartoon", "empty")
STYLE_BRANCHES = {
    "cutout": "cutout",
    "3d emoji": "emoji",
    "3demoji": "emoji",
    "retro game": "retro",
    "retrogame": "retro",
    "cartoon": "cartoon",
    "": "empty",
}


def selected_input(style):
    if not isinstance(style, str):
        raise ValueError("Style 必须是文本。")
    value = style.strip()
    field = re.fullmatch(r"style\s*[:：]\s*(.*)", value, re.IGNORECASE | re.DOTALL)
    if field:
        value = field.group(1).strip()
    normalized = " ".join(value.split()).casefold()
    if normalized not in STYLE_BRANCHES:
        raise ValueError("不支持的 Style；可选 Cutout、3D Emoji、Retro Game、Cartoon 或空文本。")
    return STYLE_BRANCHES[normalized]


class StyleSelector:
    CATEGORY = "DM Canvas/Style"
    FUNCTION = "select"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("out",)
    DESCRIPTION = "Select one of five PE text inputs by style, combining a Switch and Merge."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "style": ("STRING", {
                    "default": "", "multiline": False, "dynamicPrompts": False,
                }),
            },
            "optional": {
                name: ("STRING", {
                    "default": "", "multiline": True, "dynamicPrompts": False,
                    "lazy": True,
                })
                for name in STYLE_INPUTS
            },
        }

    def check_lazy_status(self, style, **prompts):
        name = selected_input(style)
        if name in prompts and prompts[name] is None:
            return [name]
        return []

    def select(self, style, cutout="", emoji="", retro="", cartoon="", empty=""):
        name = selected_input(style)
        prompts = {
            "cutout": cutout, "emoji": emoji, "retro": retro,
            "cartoon": cartoon, "empty": empty,
        }
        prompt = prompts[name]
        if not isinstance(prompt, str):
            raise ValueError(f"选中的 {name} 输入必须是文本。")
        return (prompt,)
