import importlib.util
import json
import math
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
    "cutout": "cutout", "3d emoji": "emoji", "retro game": "retro",
    "cartoon": "cartoon", "none": "empty",
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

    def test_style_and_all_style_contents_are_external_input_sockets(self):
        inputs = STYLE_CLASS.INPUT_TYPES()
        self.assertEqual(list(inputs["required"]), ["style"])
        self.assertEqual(list(inputs["optional"]), ["cutout", "emoji", "retro", "cartoon", "empty"])
        self.assertEqual(len(inputs["optional"]), 5)
        self.assertEqual(inputs["hidden"], {"unique_id": "UNIQUE_ID", "extra_pnginfo": "EXTRA_PNGINFO"})
        value_type, options = inputs["required"]["style"]
        self.assertEqual(value_type, "STRING")
        self.assertFalse(options.get("lazy", False))
        self.assertTrue(options["forceInput"])
        self.assertNotIn("default", options)

    def test_pe_inputs_are_lazy_sockets_without_text_widgets(self):
        inputs = STYLE_CLASS.INPUT_TYPES()
        for name, (value_type, options) in inputs["optional"].items():
            with self.subTest(name=name):
                self.assertEqual(value_type, "STRING")
                self.assertEqual(options, {"forceInput": True, "lazy": True})

    def test_default_configuration_matches_requested_lowercase_names(self):
        options = STYLE_CLASS.INPUT_TYPES()["required"]["style"][1]
        names = options["dmcanvas_style_names"]
        self.assertEqual(list(names), list(BRANCHES.values()))
        self.assertEqual([aliases[0] for aliases in names.values()], list(BRANCHES))
        self.assertEqual(names["empty"], ["none", ""])

    def test_unconfigured_style_inputs_are_not_in_the_serialized_schema(self):
        inputs = STYLE_CLASS.INPUT_TYPES()
        serialized = json.loads(json.dumps(inputs))
        self.assertEqual(list(serialized["optional"]), list(BRANCHES.values()))
        self.assertNotIn("style_names", serialized["required"])
        self.assertNotIn("style_1", serialized["optional"])
        self.assertEqual(inputs["optional"]["style_12"], ("STRING", {"forceInput": True, "lazy": True}))
        self.assertIn("style_12", inputs["optional"])
        for name in ("style_0", "style_01", "unexpected"):
            with self.subTest(name=name):
                self.assertNotIn(name, inputs["optional"])
                with self.assertRaises(KeyError):
                    inputs["optional"][name]

    def test_style_configuration_is_loaded_from_workflow_properties(self):
        metadata = {"workflow": {"nodes": [{"id": 12, "properties": {"dmcanvas_style_names": {
            "style_1": ["Watercolor"], "cartoon": ["Oil painting"],
        }}}]}}
        self.assertEqual(self.node.check_lazy_status("Watercolor", extra_pnginfo=metadata, unique_id="12", style_1=None), ["style_1"])
        self.assertEqual(self.node.select("Watercolor", extra_pnginfo=metadata, unique_id="12", style_1="Selected"), ("Selected",))
        self.assertEqual(self.node.select("Oil painting", extra_pnginfo=metadata, unique_id=12, cartoon="Oil PE"), ("Oil PE",))

    def test_missing_metadata_uses_default_styles(self):
        for metadata in (None, {}, {"workflow": {}}, {"workflow": {"nodes": []}}):
            with self.subTest(metadata=metadata):
                self.assertEqual(self.node.select("none", extra_pnginfo=metadata, unique_id="12", empty="Default"), ("Default",))

    def test_workflow_properties_do_not_leak_between_nodes(self):
        metadata = {"workflow": {"nodes": [{"id": 12, "properties": {"dmcanvas_style_names": {"cartoon": ["Oil painting"]}}}]}}
        self.assertEqual(self.node.select("cartoon", extra_pnginfo=metadata, unique_id="13", cartoon="Other"), ("Other",))

    def test_property_changes_do_not_reuse_cached_selector_output(self):
        self.assertTrue(math.isnan(STYLE_CLASS.IS_CHANGED()))

    def test_style_names_can_be_changed_without_changing_connections(self):
        configuration = json.dumps({"cartoon": ["水彩"]})
        self.assertEqual(self.node.select("style: 水彩", configuration, cartoon="Watercolor PE"), ("Watercolor PE",))
        with self.assertRaisesRegex(ValueError, "不支持的 Style"):
            self.node.select("Cartoon", configuration, cartoon="Watercolor PE")

    def test_more_than_five_styles_can_be_added(self):
        names = {f"style_{index}": [f"Custom {index}"] for index in range(1, 10)}
        configuration = json.dumps(names)
        prompts = {input_name: f"PE for {input_name}" for input_name in names}
        for input_name, aliases in names.items():
            with self.subTest(input_name=input_name):
                self.assertEqual(self.node.select(aliases[0], configuration, **prompts), (prompts[input_name],))

    def test_custom_styles_use_the_same_lazy_protocol(self):
        configuration = json.dumps({"style_1": ["Watercolor"], "style_2": ["Pixel Art"]})
        self.assertEqual(self.node.check_lazy_status("Watercolor", configuration, style_1=None, style_2=None), ["style_1"])
        self.assertEqual(self.node.check_lazy_status("Watercolor", configuration), [])
        self.assertEqual(self.node.select("Pixel Art", configuration, style_1=None, style_2="Pixel PE"), ("Pixel PE",))

    def test_removed_style_is_not_selectable(self):
        configuration = json.dumps({"style_1": ["Watercolor"]})
        with self.assertRaisesRegex(ValueError, "不支持的 Style"):
            self.node.select("Cartoon", configuration, cartoon="Unused", style_1="Watercolor")

    def test_duplicate_normalized_style_names_are_rejected(self):
        for aliases in ([" WaterColor "], ["WATERCOLOR"]):
            with self.subTest(aliases=aliases):
                configuration = json.dumps({"style_1": ["Watercolor"], "style_2": aliases})
                with self.assertRaisesRegex(ValueError, "风格名称重复"):
                    self.node.select("Watercolor", configuration)

    def test_invalid_configuration_is_rejected_during_prompt_validation(self):
        for configuration in (None, "", "[]", "null", '{"style_0":["New"]}', '{"cartoon":[]}', '{"cartoon":[1]}'):
            with self.subTest(configuration=configuration):
                self.assertIsInstance(STYLE_CLASS.VALIDATE_INPUTS(configuration), str)
                with self.assertRaises(ValueError):
                    self.node.select("Cartoon", configuration)
        self.assertTrue(STYLE_CLASS.VALIDATE_INPUTS())
        too_many = json.dumps({f"style_{index}": [f"Style {index}"] for index in range(1, 66)})
        self.assertIn("64", STYLE_CLASS.VALIDATE_INPUTS(too_many))

    def test_custom_empty_style_and_pe_preservation(self):
        configuration = json.dumps({"style_1": [""], "style_2": ["手绘"]}, ensure_ascii=False)
        self.assertEqual(self.node.select(" \n", configuration, style_1="Empty PE"), ("Empty PE",))
        prompt = "\n手绘 {variable}\r\n  "
        self.assertEqual(self.node.select("style：手绘", configuration, style_2=prompt), (prompt,))

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

    def test_none_and_empty_style_select_the_same_default_branch(self):
        for style in ("none", "None", " NONE\n", "style: none", "STYLE： None", "", " ", "\t\n\r\u00a0", "style:", "style： "):
            with self.subTest(style=style):
                self.assertEqual(self.node.select(style, **self.prompts), (self.prompts["empty"],))

    def test_none_branch_uses_lazy_input_and_preserves_text(self):
        self.assertEqual(self.node.check_lazy_status("none", empty=None, cartoon=None), ["empty"])
        self.assertEqual(self.node.select("none", empty="空\n{subject}  "), ("空\n{subject}  ",))

    def test_renamed_none_branch_does_not_keep_default_aliases(self):
        configuration = json.dumps({"empty": ["plain"]})
        self.assertEqual(self.node.select("plain", configuration, empty="Plain PE"), ("Plain PE",))
        for style in ("none", ""):
            with self.subTest(style=style):
                with self.assertRaisesRegex(ValueError, "不支持的 Style"):
                    self.node.select(style, configuration, empty="Plain PE")

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
        for style in ("Goofy", "watercolor", "null", "cartoon, cutout", '{"style":"cartoon"}'):
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
