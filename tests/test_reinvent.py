"""Checks for input safety and planning behavior, using offline fixtures."""

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from scripts.reinvent import (
    ValidationError, check_schedule, render_catalog, require_valid_catalog,
    search_catalog, validate_catalog,
)


def session(session_id="A101", **overrides):
    result = {
        "id": session_id, "year": 2026,
        "title": "Designing Agents",
        "title_ja": "エージェントの設計",
        "format": "Workshop", "level": "300", "venue": "Venetian",
        "starts_at": "2026-11-30T09:00:00-08:00", "ends_at": "2026-11-30T10:00:00-08:00",
        "url": "https://example.com/session/A101", "checked_on": "2026-09-29",
        "topics": ["AI", "Bedrock"], "why_ja": "ツール呼び出しの設計を学ぶ。",
    }
    result.update(overrides)
    return result


def catalog(*sessions):
    return {
        "schema_version": 1, "checked_on": "2026-09-29",
        "event": {"year": 2026, "timezone": "America/Los_Angeles"},
        "sessions": list(sessions) or [session()],
    }


def schedule(*items):
    return {"timezone": "America/Los_Angeles", "transfer_minutes": 45, "items": list(items)}


def item(session_id, status="planned"):
    return {"id": session_id, "year": 2026, "status": status}


class CatalogValidationTests(unittest.TestCase):
    def test_valid_and_previous_year_entries(self):
        previous = session("A101", year=2025, starts_at=None, ends_at=None)
        self.assertEqual(validate_catalog(catalog(session(), previous)), [])

    def test_path_traversal_and_non_ascii_ids_are_rejected(self):
        for unsafe in ("../notes", "x/y", "x\\y", ".", "", "Ａ101", "A101\n"):
            with self.subTest(unsafe=unsafe):
                self.assertTrue(validate_catalog(catalog(session(unsafe))))
                with tempfile.TemporaryDirectory() as directory:
                    with self.assertRaises(ValidationError):
                        render_catalog(catalog(session(unsafe)), Path(directory))
                    self.assertEqual(list(Path(directory).iterdir()), [])

    def test_duplicate_is_scoped_to_year_and_id(self):
        errors = validate_catalog(catalog(session(), session()))
        self.assertTrue(any("重複" in error for error in errors))

    def test_naive_datetime_wrong_year_and_reversed_times_are_rejected(self):
        cases = (
            {"starts_at": "2026-11-30T09:00:00"},
            {"starts_at": "2025-11-30T09:00:00-08:00"},
            {"ends_at": "2026-11-30T08:00:00-08:00"},
            {"ends_at": "2026-11-30T09:00:00-08:00"},
            {"year": True},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                self.assertTrue(validate_catalog(catalog(session(**overrides))))

    def test_unknown_end_is_allowed_without_guessing_duration(self):
        self.assertEqual(validate_catalog(catalog(session(ends_at=None))), [])

    def test_source_urls_reject_credentials_and_non_https(self):
        for url in (
            "http://example.com", "https://user:secret@example.com", "https://user@example.com",
            "file:///etc/passwd", "https:///missing", "https://example.com:wrong",
            "https://example.com\n/x", "https://example.com\\@other.example",
        ):
            with self.subTest(url=url):
                self.assertTrue(validate_catalog(catalog(session(url=url))))

    def test_bad_core_types_produce_errors(self):
        broken = catalog()
        broken["schema_version"] = True
        broken["sessions"][0]["topics"] = "AI"
        broken["sessions"][0]["checked_on"] = "2026-02-30"
        broken["event"]["timezone"] = "Not/AZone"
        self.assertGreaterEqual(len(validate_catalog(broken)), 4)

    def test_missing_title_is_rejected(self):
        data = catalog(session())
        del data["sessions"][0]["title"]
        errors = validate_catalog(data)
        self.assertTrue(any(".title" in error for error in errors))
        with self.assertRaises(ValidationError):
            require_valid_catalog(data)

    def test_empty_or_whitespace_title_is_rejected(self):
        for bad in ("", "   ", "\t"):
            with self.subTest(title=bad):
                errors = validate_catalog(catalog(session(title=bad)))
                self.assertTrue(any(".title" in error for error in errors))

    def test_title_ja_may_be_omitted(self):
        data = catalog(session())
        del data["sessions"][0]["title_ja"]
        self.assertEqual(validate_catalog(data), [])

    def test_empty_title_ja_is_rejected_when_present(self):
        for bad in ("", "   "):
            with self.subTest(title_ja=bad):
                errors = validate_catalog(catalog(session(title_ja=bad)))
                self.assertTrue(any(".title_ja" in error for error in errors))


class ScheduleTests(unittest.TestCase):
    def test_nested_overlaps_are_all_found(self):
        data = catalog(
            session("A", ends_at="2026-11-30T13:00:00-08:00"),
            session("B", starts_at="2026-11-30T10:00:00-08:00", ends_at="2026-11-30T11:00:00-08:00"),
            session("C", starts_at="2026-11-30T12:00:00-08:00", ends_at="2026-11-30T13:00:00-08:00"),
        )
        result = check_schedule(data, schedule(item("A"), item("B"), item("C", "reserved")))
        self.assertEqual(len(result.errors), 2)
        self.assertTrue(all("重複" in error for error in result.errors))

    def test_transfer_gap_and_same_venue(self):
        second = session("B", venue="MGM", starts_at="2026-11-30T10:30:00-08:00", ends_at="2026-11-30T11:30:00-08:00")
        data = catalog(session("A"), second)
        plan = schedule(item("A"), item("B"))
        self.assertTrue(any("移動時間不足" in e for e in check_schedule(data, plan).errors))
        second["venue"] = "Venetian"
        self.assertEqual(check_schedule(data, plan).errors, [])

    def test_exact_transfer_boundary_is_allowed(self):
        data = catalog(session("A"), session("B", venue="MGM", starts_at="2026-11-30T10:45:00-08:00", ends_at="2026-11-30T11:45:00-08:00"))
        self.assertEqual(check_schedule(data, schedule(item("A"), item("B"))).errors, [])

    def test_offsets_are_compared_as_instants(self):
        data = catalog(session("A"), session("B", starts_at="2026-11-30T17:30:00+00:00", ends_at="2026-11-30T18:30:00+00:00"))
        self.assertEqual(len(check_schedule(data, schedule(item("A"), item("B"))).errors), 1)

    def test_candidates_do_not_conflict_and_incomplete_times_warn(self):
        data = catalog(session("A"), session("B"), session("C", ends_at=None))
        result = check_schedule(data, schedule(item("A"), item("B", "candidate"), item("C")))
        self.assertEqual(result.errors, [])
        self.assertEqual(result.checked, 1)
        self.assertTrue(any("未確定" in warning for warning in result.warnings))

    def test_unknown_session_invalid_status_and_duplicates_fail(self):
        for plan in (
            schedule(item("missing")), schedule(item("A101", "booked")),
            schedule(item("A101"), item("A101")),
        ):
            with self.subTest(plan=plan), self.assertRaises(ValidationError):
                check_schedule(catalog(), plan)


class RenderingTests(unittest.TestCase):
    def test_deterministic_render_preserves_notes_and_input(self):
        data = catalog(session("B"), session("A", ends_at=None))
        original = deepcopy(data)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note = root / "notes" / "A.md"
            note.parent.mkdir()
            note.write_bytes(b"private handwritten notes\n")
            first_paths = render_catalog(data, root)
            first = {path.relative_to(root): path.read_bytes() for path in first_paths}
            data["sessions"].reverse()
            second_paths = render_catalog(data, root)
            second = {path.relative_to(root): path.read_bytes() for path in second_paths}
            self.assertEqual(first, second)
            self.assertEqual(note.read_bytes(), b"private handwritten notes\n")
            self.assertIn("未確認", (root / "sessions" / "2026" / "A" / "README.md").read_text())
            data["sessions"].reverse()
            self.assertEqual(data, original)

    def test_handwritten_target_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "docs" / "catalog.md"
            target.parent.mkdir()
            target.write_text("my notes\n", encoding="utf-8")
            with self.assertRaises(ValidationError):
                render_catalog(catalog(), root)
            self.assertEqual(target.read_text(), "my notes\n")
            self.assertFalse((root / "sessions").exists())

    def test_output_symlink_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as other:
            root = Path(directory)
            (root / "sessions").symlink_to(Path(other), target_is_directory=True)
            with self.assertRaises(ValidationError):
                render_catalog(catalog(), root)
            self.assertEqual(list(Path(other).iterdir()), [])

    def test_search_matches_topics_case_insensitively(self):
        self.assertEqual(len(search_catalog(catalog(), "BEDROCK")), 1)
        self.assertEqual(search_catalog(catalog(), "unknown"), [])

    def test_render_h1_uses_english_title(self):
        data = catalog(session(
            title="Designing Agents",
            title_ja="エージェントの設計",
        ))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            render_catalog(data, root)
            readme = (root / "sessions" / "2026" / "A101" / "README.md").read_text(encoding="utf-8")
            self.assertIn("# A101: Designing Agents", readme)
            self.assertNotIn("# A101: エージェントの設計", readme)

    def test_render_includes_title_ja_helper_line(self):
        data = catalog(session(title="Designing Agents", title_ja="エージェントの設計"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            render_catalog(data, root)
            readme = (root / "sessions" / "2026" / "A101" / "README.md").read_text(encoding="utf-8")
            self.assertIn("エージェントの設計", readme)
            lines = readme.splitlines()
            h1_index = next(i for i, line in enumerate(lines) if line.startswith("# A101:"))
            helper = "\n".join(lines[h1_index + 1:h1_index + 4])
            self.assertIn("エージェントの設計", helper)

    def test_catalog_table_uses_english_title(self):
        data = catalog(session(title="Designing Agents", title_ja="エージェントの設計"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            render_catalog(data, root)
            table = (root / "docs" / "catalog.md").read_text(encoding="utf-8")
            self.assertIn("[Designing Agents](../sessions/2026/A101/README.md)", table)
            self.assertNotIn("[エージェントの設計](../sessions/2026/A101/README.md)", table)

    def test_search_prefers_english_title_in_results(self):
        matches = search_catalog(catalog(session(title="Designing Agents")), "Designing")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["title"], "Designing Agents")


if __name__ == "__main__":
    unittest.main()
