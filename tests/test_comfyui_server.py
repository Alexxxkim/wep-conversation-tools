import copy
import json
import os
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen


SERVER_URL = os.environ.get("DMCANVAS_COMFYUI_TEST_URL", "").rstrip("/")


def request_json(path, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(f"{SERVER_URL}{path}", data=body, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def text_node(value):
    return {"class_type": "PrimitiveStringMultiline", "inputs": {"value": value}}


@unittest.skipUnless(SERVER_URL, "Set DMCANVAS_COMFYUI_TEST_URL to a running test ComfyUI server.")
class ComfyUIServerTests(unittest.TestCase):
    def execute(self, prompt, properties=None):
        payload = {"prompt": copy.deepcopy(prompt)}
        if properties is not None:
            payload["extra_data"] = {"extra_pnginfo": {"workflow": {"nodes": [
                {"id": 3, "properties": {"dmcanvas_style_names": properties}},
            ]}}}
        try:
            queued = request_json("/prompt", payload)
        except HTTPError as error:
            self.fail(error.read().decode())
        prompt_id = queued["prompt_id"]
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            history = request_json(f"/history/{prompt_id}")
            if prompt_id in history:
                return history[prompt_id]
            time.sleep(0.05)
        self.fail("Pure-text prompt did not finish within 20 seconds.")

    def output_text(self, result, node_id="4"):
        self.assertEqual(result["status"]["status_str"], "success", result["status"])
        return result["outputs"][node_id]["text"][0]

    def selector_prompt(self):
        return {
            "1": text_node("Watercolor"),
            "2": text_node("Watercolor PE\nKeep {subject} intact."),
            "3": {"class_type": "DMCanvasStyleSelector", "inputs": {
                "style": ["1", 0], "style_1": ["2", 0], "cartoon": ["5", 0],
            }},
            "4": {"class_type": "PreviewAny", "inputs": {"source": ["3", 0]}},
            "5": text_node("Oil painting PE"),
        }

    def test_socket_schema_and_frontend_registration(self):
        schemas = request_json("/object_info")
        for node_name, fields in (
            ("DMCanvasDrawingHistoryToConversation", ["text"]),
            ("DMCanvasIntentInputJSONWithMetadata", ["conversation", "region", "style"]),
        ):
            inputs = schemas[node_name]["input"]
            combined = {**inputs["required"], **inputs.get("optional", {})}
            self.assertEqual(list(combined), fields)
            self.assertTrue(all(specification[0] == "*" for specification in combined.values()))
        selector = schemas["DMCanvasStyleSelector"]["input"]
        self.assertEqual(list(selector["required"]), ["style"])
        self.assertEqual(list(selector["optional"]), ["cutout", "emoji", "retro", "cartoon", "empty"])
        self.assertTrue(any("wep-conversation-tools/external_inputs.js" in path for path in request_json("/extensions")))

    def test_history_to_intent_with_external_metadata(self):
        prompt = {
            "1": text_node("[1] 用户 · 2026-01-01 09:00:00\nDraw a cat"),
            "2": {"class_type": "DMCanvasDrawingHistoryToConversation", "inputs": {"text": ["1", 0]}},
            "3": {"class_type": "DMCanvasIntentInputJSONWithMetadata", "inputs": {
                "conversation": ["2", 0], "region": ["5", 0], "style": ["6", 0],
            }},
            "4": {"class_type": "PreviewAny", "inputs": {"source": ["3", 0]}},
            "5": text_node("[locale=zh-CN]"),
            "6": text_node("style: cartoon"),
        }
        payload = json.loads(self.output_text(self.execute(prompt)))
        self.assertEqual(payload["current_request"]["text"], "Draw a cat")
        self.assertEqual(payload["style"], "cartoon")
        self.assertIn("region", payload)
        del prompt["3"]["inputs"]["region"]
        del prompt["3"]["inputs"]["style"]
        payload = json.loads(self.output_text(self.execute(prompt)))
        self.assertNotIn("region", payload)
        self.assertNotIn("style", payload)

    def test_dynamic_style_is_resolved_lazily(self):
        prompt = self.selector_prompt()
        prompt["5"] = {"class_type": "DMCanvasIntentInputJSONWithMetadata", "inputs": {"conversation": "Invalid conversation"}}
        result = self.execute(prompt, {"style_1": ["Watercolor"], "cartoon": ["Oil painting"]})
        self.assertEqual(self.output_text(result), "Watercolor PE\nKeep {subject} intact.")
        executed = [message[1].get("node") for message in result["status"]["messages"] if message[0] == "executing"]
        self.assertNotIn("5", executed)

    def test_property_only_route_change_invalidates_output_cache(self):
        prompt = self.selector_prompt()
        first = self.execute(prompt, {"style_1": ["Watercolor"], "cartoon": ["Oil painting"]})
        second = self.execute(prompt, {"style_1": ["Oil painting"], "cartoon": ["Watercolor"]})
        self.assertEqual(self.output_text(first), "Watercolor PE\nKeep {subject} intact.")
        self.assertEqual(self.output_text(second), "Oil painting PE")

    def test_unconnected_selected_branch_returns_empty_text(self):
        prompt = self.selector_prompt()
        del prompt["3"]["inputs"]["style_1"]
        self.assertEqual(self.output_text(self.execute(prompt, {"style_1": ["Watercolor"]})), "")

    def test_selected_nontext_value_is_rejected_at_runtime(self):
        prompt = self.selector_prompt()
        prompt["2"] = {"class_type": "PrimitiveInt", "inputs": {"value": 42}}
        result = self.execute(prompt, {"style_1": ["Watercolor"]})
        self.assertEqual(result["status"]["status_str"], "error")
        self.assertTrue(any("输入必须是文本" in message[1].get("exception_message", "") for message in result["status"]["messages"]))
