import importlib.util
import json
from pathlib import Path
import sys
import unittest


REPOSITORY_DIRECTORY = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "comfyui-style-selector-test"
SPECIFICATION = importlib.util.spec_from_file_location(
    PACKAGE_NAME,
    REPOSITORY_DIRECTORY / "__init__.py",
    submodule_search_locations=[str(REPOSITORY_DIRECTORY)],
)
PACKAGE = importlib.util.module_from_spec(SPECIFICATION)
sys.modules[PACKAGE_NAME] = PACKAGE
SPECIFICATION.loader.exec_module(PACKAGE)
STYLE_CLASS = PACKAGE.NODE_CLASS_MAPPINGS["DMCanvasStyleSelector"]
BRANCHES = {
    "Cutout": "cutout", "3D Emoji": "emoji", "Retro Game": "retro",
    "Cartoon": "cartoon", "": "empty",
}


class StyleSelectorTests(unittest.TestCase):
    def setUp(self):
        self.node = STYLE_CLASS()
        self.prompts = {name: f"Example {name} PE" for name in BRANCHES.values()}

    def test_registered_interface_replaces_switch_and_merge(self):
        self.assertEqual(STYLE_CLASS.CATEGORY, "DM Canvas/Style")
        self.assertEqual(STYLE_CLASS.FUNCTION, "select")
        self.assertEqual(STYLE_CLASS.RETURN_TYPES, ("STRING",))
        self.assertEqual(STYLE_CLASS.RETURN_NAMES, ("out",))
        self.assertEqual(
            PACKAGE.NODE_DISPLAY_NAME_MAPPINGS["DMCanvasStyleSelector"],
            "Style Selector · 风格选择器",
        )

    def test_required_style_and_five_optional_inputs_match_screenshot(self):
        inputs = STYLE_CLASS.INPUT_TYPES()
        self.assertEqual(list(inputs["required"]), ["style"])
        self.assertEqual(list(inputs["optional"]), ["cutout", "emoji", "retro", "cartoon", "empty"])
        value_type, options = inputs["required"]["style"]
        self.assertEqual(value_type, "STRING")
        self.assertFalse(options.get("lazy", False))
        self.assertFalse(options["multiline"])

    def test_pe_inputs_are_lazy_text_widgets_without_dynamic_prompts(self):
        inputs = STYLE_CLASS.INPUT_TYPES()
        for name, (value_type, options) in inputs["optional"].items():
            with self.subTest(name=name):
                self.assertEqual(value_type, "STRING")
                self.assertEqual(options["default"], "")
                self.assertTrue(options["multiline"])
                self.assertTrue(options["lazy"])
                self.assertFalse(options["dynamicPrompts"])
        self.assertFalse(inputs["required"]["style"][1]["dynamicPrompts"])

    def test_each_case_selects_only_its_associated_text(self):
        for style, name in BRANCHES.items():
            with self.subTest(style=style):
                self.assertEqual(self.node.select(style, **self.prompts), (self.prompts[name],))

    def test_style_case_and_whitespace_are_normalized(self):
        for style, name in (
            ("cutout", "cutout"), (" CUTOUT\n", "cutout"),
            ("3d emoji", "emoji"), ("3DEmoji", "emoji"),
            ("3D\t Emoji", "emoji"), ("retro game", "retro"),
            ("retrogame", "retro"), ("Retro   Game", "retro"),
            ("cArToOn", "cartoon"),
        ):
            with self.subTest(style=style):
                self.assertEqual(self.node.select(style, **self.prompts), (self.prompts[name],))

    def test_style_field_prefix_is_supported(self):
        for style, name in (
            ("style: cartoon", "cartoon"), ("STYLE： 3D Emoji", "emoji"),
            (" style :\nRetro Game\n", "retro"),
        ):
            with self.subTest(style=style):
                self.assertEqual(self.node.select(style, **self.prompts), (self.prompts[name],))

    def test_only_empty_style_selects_empty_branch(self):
        for style in ("", " ", "\t\n\r\u00a0", "style:", "style： "):
            with self.subTest(style=style):
                self.assertEqual(self.node.select(style, **self.prompts), (self.prompts["empty"],))

    def test_selected_text_is_preserved_byte_for_byte(self):
        prompt = "\n  Example 中文 PE {name}\r\nstyle: unchanged\t\n"
        self.assertEqual(self.node.select("Cartoon", cartoon=prompt), (prompt,))

    def test_empty_or_unconnected_selected_input_does_not_use_fallback(self):
        self.assertEqual(self.node.select("Cartoon", empty="Fallback"), ("",))
        self.assertEqual(self.node.select("", cartoon="Other"), ("",))
        self.assertEqual(self.node.select("Cutout", cutout=" "), (" ",))

    def test_unselected_input_values_are_not_validated_or_converted(self):
        self.assertEqual(self.node.select(
            "Cartoon", cutout=object(), emoji=None, retro=42,
            cartoon="Selected", empty={"unused": True},
        ), ("Selected",))

    def test_invalid_style_types_raise_without_coercion(self):
        for style in (None, 0, False, [], {"style": "cartoon"}):
            with self.subTest(style=style):
                with self.assertRaisesRegex(ValueError, "Style 必须是文本"):
                    self.node.select(style, **self.prompts)

    def test_unknown_style_does_not_silently_select_default(self):
        for style in ("Goofy", "watercolor", "none", "null", "cartoon, cutout", '{"style":"cartoon"}'):
            with self.subTest(style=style):
                with self.assertRaisesRegex(ValueError, "不支持的 Style"):
                    self.node.select(style, **self.prompts)

    def test_selected_input_must_be_text(self):
        for style, name in BRANCHES.items():
            for value in (None, 42, False, {}, []):
                with self.subTest(style=style, value=value):
                    prompts = dict(self.prompts, **{name: value})
                    with self.assertRaisesRegex(ValueError, f"选中的 {name} 输入必须是文本"):
                        self.node.select(style, **prompts)

    def test_lazy_status_requests_only_selected_unavailable_branch(self):
        unresolved = dict.fromkeys(BRANCHES.values())
        for style, name in BRANCHES.items():
            with self.subTest(style=style):
                self.assertEqual(self.node.check_lazy_status(style, **unresolved), [name])

    def test_lazy_status_does_not_request_unconnected_optional_input(self):
        self.assertEqual(self.node.check_lazy_status("Cartoon"), [])
        self.assertEqual(self.node.check_lazy_status("Cartoon", cutout=None), [])

    def test_lazy_status_accepts_available_empty_text(self):
        unresolved = dict.fromkeys(BRANCHES.values())
        for style, name in BRANCHES.items():
            with self.subTest(style=style):
                available = dict(unresolved, **{name: ""})
                self.assertEqual(self.node.check_lazy_status(style, **available), [])

    def test_lazy_status_rejects_unsupported_style_before_requesting_inputs(self):
        with self.assertRaisesRegex(ValueError, "不支持的 Style"):
            self.node.check_lazy_status("Goofy", **dict.fromkeys(BRANCHES.values()))

    def test_lazy_protocol_resolves_only_one_branch(self):
        for style, name in BRANCHES.items():
            with self.subTest(style=style):
                inputs = dict.fromkeys(BRANCHES.values())
                requested = self.node.check_lazy_status(style, **inputs)
                evaluated = []
                for requested_name in requested:
                    evaluated.append(requested_name)
                    inputs[requested_name] = self.prompts[requested_name]
                self.assertEqual(evaluated, [name])
                self.assertEqual(self.node.check_lazy_status(style, **inputs), [])
                self.assertEqual(self.node.select(style, **inputs), (self.prompts[name],))

    def test_style_from_intent_json_routes_through_registered_function(self):
        intent_class = PACKAGE.NODE_CLASS_MAPPINGS["DMCanvasIntentInputJSONWithMetadata"]
        payload = json.loads(intent_class().build_json(
            "user:\nDraw a cat", style="style: cartoon",
        )[0])
        result = getattr(self.node, self.node.FUNCTION)(payload["style"], **self.prompts)
        self.assertEqual(result, (self.prompts["cartoon"],))


if __name__ == "__main__":
    unittest.main()
