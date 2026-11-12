import importlib.util
import json
from pathlib import Path
import unittest


PLUGIN_DIRECTORY = Path(__file__).resolve().parents[1] / "plugins"


def load_script(directory, name):
    specification = importlib.util.spec_from_file_location(
        name, PLUGIN_DIRECTORY / directory / f"{name}.py"
    )
    script = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(script)
    return script


CONVERTER = load_script("drawing-history-to-conversation", "drawing_history_to_conversation")
PARSER = load_script("intent-input-json", "intent_input_json")


class PipelineTests(unittest.TestCase):
    def test_example_pipeline_matches_documented_json(self):
        history = (PLUGIN_DIRECTORY / "drawing-history-to-conversation/examples/history.txt").read_text(
            encoding="utf-8"
        )
        inputs = json.loads((PLUGIN_DIRECTORY / "intent-input-json/examples/inputs.json").read_text(
            encoding="utf-8"
        ))
        expected = json.loads((PLUGIN_DIRECTORY / "intent-input-json/examples/output.json").read_text(
            encoding="utf-8"
        ))
        conversion = CONVERTER.run({"text": history})
        self.assertEqual(conversion["warnings"], "")
        self.assertEqual(conversion["conversation"], inputs["conversation"])
        inputs["conversation"] = conversion["conversation"]
        self.assertEqual(json.loads(PARSER.run(inputs)["json"]), expected)

    def test_cancelled_history_keeps_current_request_unmarked(self):
        history = (
            "[1] 用户 · 2026-01-01 09:00:00\nDraw a cat\n"
            "[2] AI · 2026-01-01 09:00:01\nGeneration cancelled\n"
            "[3] 用户 · 2026-01-01 09:00:02\nDraw a dog"
        )
        conversion = CONVERTER.run({"text": history})
        payload = json.loads(PARSER.run({"conversation": conversion["conversation"]})["json"])
        self.assertEqual(payload["history"][0]["status"], "cancelled")
        self.assertEqual(payload["current_request"], {"text": "Draw a dog", "attachments": []})

    def test_orphan_warning_does_not_enter_json(self):
        history = (
            "[1] 用户 · 2026-01-01 09:00:00\nDraw a cat\n"
            "[2] AI · 2026-01-01 09:00:01\n[图1]\n"
            "[3] AI · 2026-01-01 09:00:02\nGeneration cancelled\n"
            "[4] 用户 · 2026-01-01 09:00:03\nAdd a hat"
        )
        conversion = CONVERTER.run({"text": history})
        result = PARSER.run({"conversation": conversion["conversation"]})
        self.assertIn("cancelled", conversion["warnings"])
        self.assertNotIn("cancelled", result["json"])
        self.assertEqual(json.loads(result["json"])["latest_result_id"], "image1")


if __name__ == "__main__":
    unittest.main()
