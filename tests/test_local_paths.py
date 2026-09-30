"""Path shape checks for local-data helpers."""

import unittest

from scripts.local_paths import (
    LOCAL_DATA,
    ROOT,
    local_data_root,
    streams_path,
    summary_path,
    transcript_path,
)


class LocalPathsTests(unittest.TestCase):
    def test_root_is_repo_local_data(self):
        self.assertEqual(local_data_root(), LOCAL_DATA)
        self.assertEqual(LOCAL_DATA, ROOT / "local-data")
        self.assertTrue(str(LOCAL_DATA).endswith("/local-data"))

    def test_transcript_and_summary_shapes(self):
        self.assertEqual(
            transcript_path(2026, "DVT206"),
            LOCAL_DATA / "transcripts" / "2026" / "DVT206.md",
        )
        self.assertEqual(
            summary_path(2026, "DVT206"),
            LOCAL_DATA / "summaries" / "2026" / "DVT206.json",
        )

    def test_streams_path(self):
        self.assertEqual(streams_path(), LOCAL_DATA / "streams.json")


if __name__ == "__main__":
    unittest.main()
