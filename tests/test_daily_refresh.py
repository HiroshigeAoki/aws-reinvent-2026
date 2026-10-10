"""Checks the guardrails around the unattended daily refresh."""

import unittest

from scripts.daily_refresh import EDITABLE, classify_changes


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


if __name__ == "__main__":
    unittest.main()
