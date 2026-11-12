import importlib.util
import json
from pathlib import Path
import unittest


PLUGIN_DIRECTORY = Path(__file__).resolve().parents[1]
SPECIFICATION = importlib.util.spec_from_file_location(
    "intent_input_json", PLUGIN_DIRECTORY / "intent_input_json.py"
)
SCRIPT = importlib.util.module_from_spec(SPECIFICATION)
SPECIFICATION.loader.exec_module(SCRIPT)


class IntentInputJSONTests(unittest.TestCase):
    def test_example_matches_expected_output(self):
        inputs = json.loads((PLUGIN_DIRECTORY / "examples/inputs.json").read_text(encoding="utf-8"))
        expected = json.loads((PLUGIN_DIRECTORY / "examples/output.json").read_text(encoding="utf-8"))
        self.assertEqual(json.loads(SCRIPT.run(inputs)["json"]), expected)

    def test_single_round_returns_formatted_unicode_json(self):
        result = SCRIPT.run({"conversation": "user:\n画一只猫"})
        self.assertEqual(set(result), {"json"})
        self.assertIn('\n  "current_request": {', result["json"])
        self.assertIn("画一只猫", result["json"])
        self.assertEqual(json.loads(result["json"]), {
            "current_request": {"text": "画一只猫", "attachments": []}, "history": [],
        })

    def test_status_preserves_separate_requests(self):
        for status in ("cancelled", "failed"):
            with self.subTest(status=status):
                payload = SCRIPT.parse_conversation(
                    f"user:\nDraw a cat\nstatus: {status}\nuser:\nDraw a dog"
                )
                self.assertEqual(payload["history"], [{
                    "role": "user", "text": "Draw a cat", "attachments": [], "status": status,
                }])
                self.assertEqual(payload["current_request"], {"text": "Draw a dog", "attachments": []})
                self.assertNotIn("latest_result_id", payload)

    def test_image_mapping_runs_from_newest_to_oldest(self):
        payload = SCRIPT.parse_conversation(
            "user: 1\nChange [图 1]\nai: 2\nuser: 3, 4\nCombine [图3] and [图4]"
        )
        self.assertEqual(payload["current_request"]["attachments"], [
            {"id": "image1", "type": "image"}, {"id": "image2", "type": "image"},
        ])
        self.assertEqual(payload["current_request"]["text"], "Combine [image1] and [image2]")
        self.assertEqual(payload["history"][0]["text"], "Change [image4]")
        self.assertEqual(payload["latest_result_id"], "image3")

    def test_ai_and_assistant_headers_are_equivalent(self):
        source = "user:\nDraw a cat\nai: 1\n[图1]\nuser:\nChange its color"
        self.assertEqual(
            SCRIPT.run({"conversation": source}),
            SCRIPT.run({"conversation": source.replace("ai:", "assistant:")}),
        )

    def test_chinese_punctuation_and_indented_headers(self):
        payload = SCRIPT.parse_conversation("user:\n画猫\n  ai： 1， 2 \nuser:\n修改 [图2]")
        self.assertEqual(payload["history"][1]["role"], "assistant")
        self.assertEqual(len(payload["history"][1]["attachments"]), 2)
        self.assertEqual(payload["latest_result_id"], "image1")
        self.assertEqual(payload["current_request"]["text"], "修改 [image2]")

    def test_empty_ai_is_removed_but_ai_body_is_preserved(self):
        payload = SCRIPT.parse_conversation(
            "user:\nDraw a cat\nai：\n\nuser:\nDraw a dog\nai:\nWorking on it\nuser:\nAdd a hat"
        )
        self.assertEqual(len(payload["history"]), 3)
        self.assertEqual(payload["history"][-1]["text"], "Working on it")
        self.assertNotIn("latest_result_id", payload)

    def test_body_numbers_are_not_attachments_and_status_is_not_invented(self):
        payload = SCRIPT.parse_conversation("user:\nDraw 2 cats\nai:\n1\nuser:\nAdd a hat")
        self.assertEqual(payload["history"][1]["attachments"], [])
        self.assertNotIn("status", payload["history"][0])
        self.assertNotIn("status", payload["current_request"])

    def test_missing_conversation_returns_empty_string(self):
        for inputs in ({}, {"region": "[locale=zh-CN]"}, {"style": "style: cartoon"}):
            self.assertEqual(SCRIPT.run(inputs), {"json": ""})

    def test_style_and_region_field_order(self):
        payload = json.loads(SCRIPT.run({
            "conversation": "user:\nDraw a cat\nai: 1\nuser:\nAdd a hat",
            "region": "[locale=zh-CN]", "style": "style: cartoon",
        })["json"])
        self.assertEqual(list(payload), [
            "current_request", "latest_result_id", "history", "style", "region",
        ])
        self.assertEqual(payload["style"], "cartoon")
        self.assertEqual(payload["region"], {"locale": "zh-CN"})

    def test_optional_inputs_are_independent(self):
        base = {"conversation": "user:\nDraw a cat"}
        style_payload = json.loads(SCRIPT.run({**base, "style": "style: cartoon"})["json"])
        region_payload = json.loads(SCRIPT.run({**base, "region": "[locale=zh-CN]"})["json"])
        self.assertEqual(style_payload["style"], "cartoon")
        self.assertNotIn("region", style_payload)
        self.assertEqual(region_payload["region"], {"locale": "zh-CN"})
        self.assertNotIn("style", region_payload)

    def test_blank_optional_inputs_preserve_original_output(self):
        inputs = {"conversation": "user:\nDraw a cat"}
        original = SCRIPT.run(inputs)
        for value in (None, "", "\t\n\u00a0"):
            with self.subTest(value=value):
                self.assertEqual(SCRIPT.run({**inputs, "region": value, "style": value}), original)
        for style in ("style:", " STYLE ：\n\t\u00a0"):
            self.assertEqual(SCRIPT.run({**inputs, "style": style}), original)

    def test_region_whitespace_and_locale_subtags(self):
        for region, expected in (
            ("\n [locale=en-AU]\t", "en-AU"),
            ("[ locale = zh-Hant-TW ]", "zh-Hant-TW"),
            ("[locale=es-419]", "es-419"),
        ):
            with self.subTest(region=region):
                self.assertEqual(SCRIPT.parse_region(region), {"locale": expected})

    def test_style_case_and_multiline_body(self):
        for style, expected in (
            (" Style : watercolor ", "watercolor"),
            ("STYLE： 3D Cartoon", "3D Cartoon"),
            ("style: hand drawn\nsoft colors", "hand drawn\nsoft colors"),
        ):
            with self.subTest(style=style):
                self.assertEqual(SCRIPT.parse_style(style), expected)

    def test_invalid_metadata_raises(self):
        for field, values in (
            ("region", (1, {}, "zh-CN", "[locale=]", "[locale=en AU]", "[country=CN]")),
            ("style", (1, {}, "cartoon", "style=cartoon", "styles: cartoon")),
        ):
            for value in values:
                with self.subTest(field=field, value=value):
                    with self.assertRaisesRegex(ValueError, field.title()):
                        SCRIPT.run({"conversation": "user:\nDraw a cat", field: value})

    def test_invalid_conversation_raises(self):
        for conversation, message in (
            (None, "必须是文本"),
            ("", "最后一条消息"),
            ("Draw a cat", "请以 user"),
            ("user:\nDraw a cat\nai: 1", "最后一条消息"),
            ("user:\nDraw a cat\nstatus: cancelled", "尚未执行"),
            ("user:\nOld\nstatus: succeeded\nuser:\nNew", "只能填写"),
            ("user:\nOld\nstatus: failed\nstatus: failed\nuser:\nNew", "只能填写一次"),
            ("user:\nOld\nai:\nstatus: failed\nuser:\nNew", "只能标记"),
            ("user:\nOld\nstatus: failed\nai: 1\nuser:\nNew", "不能同时声明"),
            ("user: 0\nDraw a cat", "正整数"),
            ("user: 1\nOld\nuser: 1\nNew", "只声明一次"),
            ("user:\nUse [图9]", "引用未声明"),
        ):
            with self.subTest(conversation=conversation):
                with self.assertRaisesRegex(ValueError, message):
                    SCRIPT.parse_conversation(conversation)


if __name__ == "__main__":
    unittest.main()
