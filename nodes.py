import importlib.util
import json
from pathlib import Path

from .style_selector import StyleSelector


PLUGIN_DIRECTORY = Path(__file__).resolve().parent / "plugins"
CATEGORY = "DM Canvas/Conversation"


def load_script(directory, name):
    specification = importlib.util.spec_from_file_location(
        f"dmcanvas_{name}", PLUGIN_DIRECTORY / directory / f"{name}.py"
    )
    script = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(script)
    return script


HISTORY_SCRIPT = load_script("drawing-history-to-conversation", "drawing_history_to_conversation")
INTENT_SCRIPT = load_script("intent-input-json", "intent_input_json")


class DrawingHistoryToConversation:
    CATEGORY = CATEGORY
    FUNCTION = "convert"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("conversation", "warnings")
    DESCRIPTION = "Convert drawing history to Conversation text; report orphan status events as warnings."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
            },
        }

    def convert(self, text):
        conversation, warnings = HISTORY_SCRIPT.normalize_input(text)
        return conversation, "\n".join(warnings)


class IntentInputJSON:
    CATEGORY = CATEGORY
    FUNCTION = "build_json"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("json",)
    DESCRIPTION = "Convert Conversation and optional Region / Style text to structured intent JSON."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "conversation": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "region": ("STRING", {"forceInput": True}),
                "style": ("STRING", {"forceInput": True}),
            },
        }

    def build_json(self, conversation, region="", style=""):
        payload = INTENT_SCRIPT.parse_conversation(conversation)
        parsed_style = INTENT_SCRIPT.parse_style(style)
        if parsed_style is not None:
            payload["style"] = parsed_style
        parsed_region = INTENT_SCRIPT.parse_region(region)
        if parsed_region is not None:
            payload["region"] = parsed_region
        return (json.dumps(payload, ensure_ascii=False, indent=2),)


NODE_CLASS_MAPPINGS = {
    "DMCanvasDrawingHistoryToConversation": DrawingHistoryToConversation,
    "DMCanvasIntentInputJSONWithMetadata": IntentInputJSON,
    "DMCanvasStyleSelector": StyleSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DMCanvasDrawingHistoryToConversation": "Drawing History to Conversation · 绘画历史转换",
    "DMCanvasIntentInputJSONWithMetadata": "Intent Input JSON",
    "DMCanvasStyleSelector": "Style Selector · 风格选择器",
}


__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
