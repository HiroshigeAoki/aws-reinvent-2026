"""Checks the guardrails around the unattended daily refresh."""

import unittest

from scripts.daily_refresh import (ALLOWED_TOOLS, CLAUDE_FLAGS, DENIED_TOOLS, EDITABLE, classify_changes,
                                   foreign_new_urls, parse_report)


class ClassifyChangesTests(unittest.TestCase):
    def test_editable_and_rendered_files_are_staged(self):
        stage, foreign = classify_changes(["data/events.json", "docs/events.md", "sessions/2026/A101/README.md"])
        self.assertEqual(stage, ["data/events.json", "docs/events.md", "sessions/2026/A101/README.md"])
        self.assertEqual(foreign, [])

    def test_other_files_block_the_commit(self):
        stage, foreign = classify_changes(["data/guide.json", "planning/schedule.json", "scripts/site.py"])
        self.assertEqual(stage, ["data/guide.json"])
        self.assertEqual(foreign, ["planning/schedule.json", "scripts/site.py"])

    def test_rendered_files_alone_are_not_a_data_change(self):
        stage, _ = classify_changes(["docs/catalog.md"])
        self.assertFalse(any(path in EDITABLE for path in stage))


class ToolScopeTests(unittest.TestCase):
    def test_reads_and_fetches_are_scoped(self):
        for bare in ("Read", "Glob", "Grep", "WebFetch", "WebSearch", "Bash", "Edit", "Write"):
            self.assertNotIn(bare, ALLOWED_TOOLS)
        self.assertFalse(any("private" in tool for tool in ALLOWED_TOOLS))
        self.assertTrue(all(t.startswith("WebFetch(domain:") for t in ALLOWED_TOOLS if t.startswith("WebFetch")))
        self.assertFalse(any(t.startswith(("Bash", "Write")) for t in ALLOWED_TOOLS))
        self.assertIn("Read(private/**)", DENIED_TOOLS)
        self.assertIn("Read(local-data/**)", DENIED_TOOLS)


    def test_run_ignores_user_settings(self):
        self.assertIn("--restricted", CLAUDE_FLAGS)
        self.assertEqual(CLAUDE_FLAGS[CLAUDE_FLAGS.index("--tools") + 1], "Read,Edit,WebFetch")
        self.assertEqual(CLAUDE_FLAGS[CLAUDE_FLAGS.index("--permission-mode") + 1], "dontAsk")


class ForeignUrlTests(unittest.TestCase):
    def test_new_outside_link_is_reported(self):
        before = '["https://dev.to/old"]'
        after = '["https://dev.to/old", "https://evil.example/x?d=1", "https://aws.amazon.com/events/reinvent/agenda/"]'
        self.assertEqual(foreign_new_urls(before, after), ["https://evil.example/x?d=1"])

    def test_existing_links_are_left_alone(self):
        text = '{"url": "https://dev.to/old"}'
        self.assertEqual(foreign_new_urls(text, text), [])

    def test_lookalike_host_is_outside(self):
        after = '{"url": "https://aws.amazon.com.evil.example/"}'
        self.assertEqual(foreign_new_urls("{}", after), ["https://aws.amazon.com.evil.example/"])

    def test_json_escapes_and_case_do_not_hide_a_link(self):
        for raw, url in (('https:\\/\\/evil.example\\/x', "https://evil.example/x"),
                         ('\\u0068ttps://evil.example/', "https://evil.example/"),
                         ("HTTPS://evil.example/", "HTTPS://evil.example/"),
                         ("//evil.example/x", "//evil.example/x"),
                         ("https://aws.amazon.com@evil.example/", "https://aws.amazon.com@evil.example/")):
            self.assertEqual(foreign_new_urls("{}", '{"body_ja": "見て ' + raw + '"}'), [url], raw)

    def test_official_link_with_userinfo_is_outside(self):
        self.assertEqual(foreign_new_urls("{}", '{"u": "https://x@aws.amazon.com/"}'), ["https://x@aws.amazon.com/"])

    def test_unparseable_json_blocks(self):
        self.assertEqual(foreign_new_urls("{}", "{broken"), ["(JSONとして読めない)"])


class ParseReportTests(unittest.TestCase):
    def test_last_json_object_is_the_report(self):
        result = '確認しました。\n```json\n{\n  "summary_ja": "変化なし",\n  "changes_ja": []\n}\n```'
        self.assertEqual(parse_report(result), {"summary_ja": "変化なし", "changes_ja": []})

    def test_no_json_gives_empty_report(self):
        self.assertEqual(parse_report("失敗しました"), {})


if __name__ == "__main__":
    unittest.main()
