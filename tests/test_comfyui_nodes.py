import importlib.util
import json
from pathlib import Path
import sys
import unittest


REPOSITORY_DIRECTORY = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "comfyui-conversation-tools-test"
SPECIFICATION = importlib.util.spec_from_file_location(
    PACKAGE_NAME,
    REPOSITORY_DIRECTORY / "__init__.py",
    submodule_search_locations=[str(REPOSITORY_DIRECTORY)],
)
PACKAGE = importlib.util.module_from_spec(SPECIFICATION)
sys.modules[PACKAGE_NAME] = PACKAGE
SPECIFICATION.loader.exec_module(PACKAGE)
NODES = sys.modules[f"{PACKAGE_NAME}.nodes"]
HISTORY_CLASS = PACKAGE.NODE_CLASS_MAPPINGS["DMCanvasDrawingHistoryToConversation"]
INTENT_CLASS = PACKAGE.NODE_CLASS_MAPPINGS["DMCanvasIntentInputJSONWithMetadata"]


class ComfyUINodeTests(unittest.TestCase):
    def test_package_exports_all_node_mappings(self):
        self.assertEqual(set(PACKAGE.NODE_CLASS_MAPPINGS), {
            "DMCanvasDrawingHistoryToConversation", "DMCanvasIntentInputJSONWithMetadata",
            "DMCanvasStyleSelector",
        })
        self.assertEqual(set(PACKAGE.NODE_DISPLAY_NAME_MAPPINGS), set(PACKAGE.NODE_CLASS_MAPPINGS))
        self.assertEqual(set(PACKAGE.__all__), {
            "NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY",
        })
        self.assertTrue((REPOSITORY_DIRECTORY / PACKAGE.WEB_DIRECTORY / "external_inputs.js").is_file())

    def test_new_intent_type_does_not_override_legacy_plugin(self):
        self.assertNotIn("DMCanvasIntentInputJSON", PACKAGE.NODE_CLASS_MAPPINGS)
        self.assertEqual(
            PACKAGE.NODE_DISPLAY_NAME_MAPPINGS["DMCanvasIntentInputJSONWithMetadata"],
            "Intent Input JSON",
        )

    def test_comfyui_node_contract(self):
        for node_class in PACKAGE.NODE_CLASS_MAPPINGS.values():
            with self.subTest(node_class=node_class.__name__):
                expected_category = (
                    "DM Canvas/Style" if node_class.__name__ == "StyleSelector"
                    else "DM Canvas/Conversation"
                )
                self.assertEqual(node_class.CATEGORY, expected_category)
                self.assertTrue(callable(getattr(node_class(), node_class.FUNCTION)))
                self.assertEqual(len(node_class.RETURN_TYPES), len(node_class.RETURN_NAMES))
                self.assertTrue(all(value_type == "STRING" for value_type in node_class.RETURN_TYPES))

    def test_history_text_is_a_required_input_socket(self):
        inputs = HISTORY_CLASS.INPUT_TYPES()
        self.assertEqual(set(inputs), {"required"})
        self.assertEqual(set(inputs["required"]), {"text"})
        value_type, options = inputs["required"]["text"]
        self.assertEqual(value_type, "*")
        self.assertEqual(options, {"forceInput": True})

    def test_intent_has_required_conversation_and_optional_metadata(self):
        inputs = INTENT_CLASS.INPUT_TYPES()
        self.assertEqual(set(inputs["required"]), {"conversation"})
        self.assertEqual(set(inputs["optional"]), {"region", "style"})
        for section in inputs.values():
            for value_type, options in section.values():
                self.assertEqual(value_type, "*")
                self.assertEqual(options, {"forceInput": True})

    def test_optional_input_sockets_can_be_connected_independently(self):
        node = INTENT_CLASS()
        conversation = "user:\nDraw a cat"
        with_region = json.loads(node.build_json(conversation, region="[locale=zh-CN]")[0])
        self.assertEqual(with_region["region"], {"locale": "zh-CN"})
        self.assertNotIn("style", with_region)
        with_style = json.loads(node.build_json(conversation, style="style: cartoon")[0])
        self.assertEqual(with_style["style"], "cartoon")
        self.assertNotIn("region", with_style)

    def test_history_example_matches_original_script(self):
        history = (
            REPOSITORY_DIRECTORY / "plugins/drawing-history-to-conversation/examples/history.txt"
        ).read_text(encoding="utf-8")
        original = NODES.HISTORY_SCRIPT.run({"text": history})
        result = getattr(HISTORY_CLASS(), HISTORY_CLASS.FUNCTION)(text=history)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result, (original["conversation"], original["warnings"]))

    def test_history_empty_and_formatted_input_are_preserved(self):
        for text in ("", "\n  \r\n", "\n  user： 1 \r\nUse [图1]  \r\n"):
            with self.subTest(text=text):
                self.assertEqual(HISTORY_CLASS().convert(text), (text, ""))

    def test_history_warnings_are_a_separate_string_output(self):
        history = (
            "[1] 用户 · 2026-01-01 09:00:00\nDraw a cat\n"
            "[2] AI · 2026-01-01 09:00:01\n[图1]\n"
            "[3] AI · 2026-01-01 09:00:02\nGeneration cancelled\n"
            "[4] 用户 · 2026-01-01 09:00:03\nAdd a hat"
        )
        conversation, warnings = HISTORY_CLASS().convert(history)
        self.assertIsInstance(warnings, str)
        self.assertIn("第 3 条", warnings)
        self.assertIn("cancelled", warnings)
        self.assertNotIn("cancelled", conversation)

    def test_history_invalid_input_keeps_original_validation(self):
        for text, error in (
            (None, "必须是文本"),
            ("Draw a cat", "输入须为"),
            ("[1] 用户 · 2026-01-01 09:00:00\nUse [图0]", "正整数"),
        ):
            with self.subTest(text=text):
                with self.assertRaisesRegex(ValueError, error):
                    HISTORY_CLASS().convert(text)

    def test_intent_example_matches_original_script_exactly(self):
        inputs = json.loads((
            REPOSITORY_DIRECTORY / "plugins/intent-input-json/examples/inputs.json"
        ).read_text(encoding="utf-8"))
        original = NODES.INTENT_SCRIPT.run(inputs)
        result = getattr(INTENT_CLASS(), INTENT_CLASS.FUNCTION)(**inputs)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result, (original["json"],))

    def test_empty_optional_metadata_is_omitted(self):
        node = INTENT_CLASS()
        original = node.build_json("user:\n画一只猫")
        for value in (None, "", "\t\n\u00a0"):
            with self.subTest(value=value):
                self.assertEqual(node.build_json("user:\n画一只猫", region=value, style=value), original)
        payload = json.loads(original[0])
        self.assertEqual(payload["history"], [])
        self.assertNotIn("region", payload)
        self.assertNotIn("style", payload)

    def test_metadata_and_json_field_order_match_original(self):
        result = INTENT_CLASS().build_json(
            "user:\nDraw a cat\nai: 1\nuser:\nChange [图1]",
            region="[ locale = zh-Hant-TW ]", style="STYLE： hand drawn\nsoft colors",
        )
        payload = json.loads(result[0])
        self.assertEqual(list(payload), [
            "current_request", "latest_result_id", "history", "style", "region",
        ])
        self.assertEqual(payload["region"], {"locale": "zh-Hant-TW"})
        self.assertEqual(payload["style"], "hand drawn\nsoft colors")

    def test_intent_validation_is_not_silenced(self):
        for inputs, error in (
            ({"conversation": ""}, "最后一条消息"),
            ({"conversation": "user:\nDraw a cat\nstatus: failed"}, "尚未执行"),
            ({"conversation": "user:\nDraw a cat", "region": "zh-CN"}, "Region"),
            ({"conversation": "user:\nDraw a cat", "style": "cartoon"}, "Style"),
        ):
            with self.subTest(inputs=inputs):
                with self.assertRaisesRegex(ValueError, error):
                    INTENT_CLASS().build_json(**inputs)

    def test_both_nodes_execute_through_registered_functions(self):
        history = (
            REPOSITORY_DIRECTORY / "plugins/drawing-history-to-conversation/examples/history.txt"
        ).read_text(encoding="utf-8")
        expected = json.loads((
            REPOSITORY_DIRECTORY / "plugins/intent-input-json/examples/output.json"
        ).read_text(encoding="utf-8"))
        conversation, warnings = getattr(HISTORY_CLASS(), HISTORY_CLASS.FUNCTION)(text=history)
        result = getattr(INTENT_CLASS(), INTENT_CLASS.FUNCTION)(
            conversation=conversation, region="[locale=zh-CN]", style="style: cartoon",
        )
        self.assertEqual(warnings, "")
        self.assertEqual(json.loads(result[0]), expected)

    def test_cancelled_history_keeps_current_request_unmarked(self):
        history = (
            "[1] 用户 · 2026-01-01 09:00:00\nDraw a cat\n"
            "[2] AI · 2026-01-01 09:00:01\nGeneration cancelled\n"
            "[3] 用户 · 2026-01-01 09:00:02\nDraw a dog"
        )
        conversation, warnings = HISTORY_CLASS().convert(history)
        payload = json.loads(INTENT_CLASS().build_json(conversation)[0])
        self.assertEqual(warnings, "")
        self.assertEqual(payload["history"][0]["status"], "cancelled")
        self.assertNotIn("status", payload["current_request"])


if __name__ == "__main__":
    unittest.main()
