import importlib.util
from pathlib import Path
import unittest


PLUGIN_DIRECTORY = Path(__file__).resolve().parents[1]
SPECIFICATION = importlib.util.spec_from_file_location(
    "drawing_history_to_conversation", PLUGIN_DIRECTORY / "drawing_history_to_conversation.py"
)
SCRIPT = importlib.util.module_from_spec(SPECIFICATION)
SPECIFICATION.loader.exec_module(SCRIPT)


def raw_history(*messages):
    return "\n\n".join(
        f"[{sequence}] {role} · 2026-01-01 09:00:{sequence:02d}\n{body}"
        for sequence, (role, body) in enumerate(messages, start=1)
    )


class DrawingHistoryTests(unittest.TestCase):
    def test_example_matches_expected_conversation(self):
        source = (PLUGIN_DIRECTORY / "examples/history.txt").read_text(encoding="utf-8")
        expected = (PLUGIN_DIRECTORY / "examples/conversation.txt").read_text(encoding="utf-8")
        self.assertEqual(SCRIPT.run({"text": source}), {
            "conversation": expected.rstrip("\n"), "warnings": "",
        })

    def test_formatted_conversation_is_preserved_exactly(self):
        for text in (
            "\n  user： 1， 2 \r\nCreate a sticker of [图1] and [图2]  \r\n",
            "assistant: 1\nOriginal AI text\nuser:\nMake sticker off a cat\n",
            "user:\nPending\nstatus: cancelled",
        ):
            with self.subTest(text=text):
                self.assertEqual(SCRIPT.run({"text": text}), {
                    "conversation": text, "warnings": "",
                })

    def test_prefix_case_typo_and_multiline_spacing_are_preserved(self):
        for body in (
            "Create a sticker of a cat", "CREATE STICKER OF a cat",
            "Please make sticker off a catt\nwith a blue hat",
            "  Make   sticker\tof a cat  \n\nwith a hat",
        ):
            with self.subTest(body=body):
                result = SCRIPT.run({"text": raw_history(("用户", body))})
                self.assertEqual(result["conversation"], f"user:\n{body}")

    def test_multiple_images_are_declared_once(self):
        source = raw_history(
            ("用户", "Combine [图1] and [图 2] with [图1]"),
            ("AI", "Using [图1], here are [图3] and [图4]"),
            ("用户", "Change [图3] using [图5]"),
        )
        self.assertEqual(SCRIPT.run({"text": source})["conversation"], (
            "user: 1, 2\nCombine [图1] and [图 2] with [图1]\n"
            "ai: 3, 4\nuser: 5\nChange [图3] using [图5]"
        ))

    def test_cancellation_variants_mark_historical_user(self):
        for marker in ("Generation cancelled", "Generation canceled.", "已取消"):
            with self.subTest(marker=marker):
                source = raw_history(("用户", "Draw a cat"), ("AI", marker), ("用户", "Draw a dog"))
                self.assertEqual(SCRIPT.run({"text": source}), {
                    "conversation": "user:\nDraw a cat\nstatus: cancelled\nuser:\nDraw a dog",
                    "warnings": "",
                })

    def test_failure_variants_mark_historical_user(self):
        for marker in (
            "[生成失败:timeout]", "[生成失败：timeout]",
            "Generation failed", "Couldn't generate content.",
        ):
            with self.subTest(marker=marker):
                source = raw_history(("用户", "Draw a cat"), ("AI", marker), ("用户", "Draw a dog"))
                self.assertIn("status: failed", SCRIPT.run({"text": source})["conversation"])

    def test_orphan_status_emits_warning_without_overriding_success(self):
        for marker, status in (("Generation cancelled", "cancelled"), ("Generation failed", "failed")):
            with self.subTest(status=status):
                source = raw_history(
                    ("用户", "Draw a cat"), ("AI", "[图1]"),
                    ("AI", marker), ("用户", "Add a hat"),
                )
                result = SCRIPT.run({"text": source})
                self.assertEqual(result["conversation"], "user:\nDraw a cat\nai: 1\nuser:\nAdd a hat")
                self.assertIn("第 3 条", result["warnings"])
                self.assertIn(status, result["warnings"])

    def test_unmarked_ai_does_not_invent_results(self):
        source = raw_history(
            ("用户", "Draw a cat"), ("AI", "Working on it."), ("用户", "Draw a dog"),
        )
        self.assertEqual(SCRIPT.run({"text": source}), {
            "conversation": "user:\nDraw a cat\nuser:\nDraw a dog", "warnings": "",
        })

    def test_copy_artifacts_and_crlf_headers(self):
        source = "\ufeff[1] 用户 · 2026-01-01 09:00:00\u200b\r\nDraw a cat\r\n"
        self.assertEqual(SCRIPT.run({"text": source})["conversation"], "user:\nDraw a cat")

    def test_english_roles_and_alternate_timestamp_separator(self):
        source = "[1] user ・ 2026-01-01T09:00:00.123\nDraw a cat"
        self.assertEqual(SCRIPT.run({"text": source})["conversation"], "user:\nDraw a cat")

    def test_missing_and_blank_input(self):
        self.assertEqual(SCRIPT.run({}), {"conversation": "", "warnings": ""})
        for text in ("", "\n  \r\n"):
            self.assertEqual(SCRIPT.run({"text": text}), {"conversation": text, "warnings": ""})

    def test_invalid_input_raises(self):
        for source, message in (
            (None, "必须是文本"),
            ("Draw a cat", "输入须为"),
            (raw_history(("用户", "Use [图0]")), "正整数"),
        ):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, message):
                    SCRIPT.run({"text": source})

    def test_completed_history_requires_real_current_request(self):
        for marker in ("[图1]", "Generation cancelled", "Generation failed"):
            with self.subTest(marker=marker):
                with self.assertRaisesRegex(ValueError, "待执行"):
                    SCRIPT.run({"text": raw_history(("用户", "Draw a cat"), ("AI", marker))})

    def test_conflicting_status_and_new_image_raises(self):
        source = raw_history(
            ("用户", "Draw a cat"), ("AI", "[生成失败:timeout][图1]"), ("用户", "Draw a dog"),
        )
        with self.assertRaisesRegex(ValueError, "同时包含"):
            SCRIPT.run({"text": source})


if __name__ == "__main__":
    unittest.main()
