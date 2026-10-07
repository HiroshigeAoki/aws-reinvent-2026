"""Checks that the shared page stays free of personal plans."""

import unittest

from scripts.reinvent import ValidationError, check_schedule
from scripts.site import build_personal, build_shared, validate_guide
from tests.test_reinvent import catalog, item, schedule, session


def events(**overrides):
    entry = {
        "id": "expo", "title": "Welcome reception", "title_ja": "ウェルカム",
        "category": "reception", "date": "2026-11-30",
        "starts_at": "2026-11-30T16:00:00-08:00", "ends_at": "2026-11-30T19:00:00-08:00",
        "venue": "Venetian", "registration": "none", "url": "https://example.com/agenda",
        "checked_on": "2026-10-07", "note_ja": "A101 のあとに行く", "public_note_ja": "誰でも参加可",
        "intent": "maybe",
    }
    entry.update(overrides)
    return {"schema_version": 1, "checked_on": "2026-10-07", "timezone": "America/Los_Angeles",
            "sources": [{"id": "agenda", "url": "https://example.com/agenda", "label_ja": "Agenda"}],
            "events": [entry]}


def guide(**overrides):
    result = {
        "checked_on": "2026-10-07",
        "venues": [{"id": "venetian", "name": "The Venetian", "role_ja": "基調講演", "lat": 36.12, "lon": -115.17,
                    "year": 2026, "source": "https://example.com/venues"},
                   {"id": "mgm", "name": "MGM Grand", "role_ja": "セッション", "lat": 36.10, "lon": -115.17,
                    "year": 2025, "source": "https://example.com/venues"}],
        "transport": [], "walk_times": [],
        "tips": [{"id": "shoes", "category": "持ち物・服装", "title_ja": "歩きやすい靴<b>",
                  "body_ja": "一日に長く歩く。", "year": 2025, "sources": ["https://example.com/blog"]}],
        "links": [],
    }
    result.update(overrides)
    return result


class SharedPageTests(unittest.TestCase):
    def test_shared_page_omits_personal_notes_and_intents(self):
        html = build_shared(events(), guide(), "2026-10-07")
        self.assertIn("誰でも参加可", html)
        self.assertNotIn("A101", html)
        self.assertNotIn("検討", html)

    def test_text_is_escaped_and_no_script(self):
        html = build_shared(events(), guide(), "2026-10-07")
        self.assertIn("歩きやすい靴&lt;b&gt;", html)
        self.assertNotIn("<script", html)
        self.assertIn("script-src 'none'", html)

    def test_guide_entries_need_sources(self):
        broken = guide(tips=[{"id": "x", "category": "移動", "title_ja": "t", "body_ja": "b", "sources": []}])
        with self.assertRaises(ValidationError):
            validate_guide(broken)
        with self.assertRaises(ValidationError):
            validate_guide(guide(tips=[{"id": "x", "category": "不明", "title_ja": "t", "body_ja": "b",
                                        "sources": ["https://example.com"]}]))


class PersonalPageTests(unittest.TestCase):
    def test_review_flag_and_shared_link(self):
        reviewed = dict(item("A101", "reserved"), review_ja="イベント次第でキャンセル")
        html = build_personal(catalog(session()), events(), schedule(reviewed),
                              "https://example.com/shared", "2026-10-07T14:00:00+09:00", "2026-10-07")
        self.assertIn("見直し中", html)
        self.assertIn("イベント次第でキャンセル", html)
        self.assertIn('href="https://example.com/shared"', html)
        self.assertIn("A101 のあとに行く", html)

    def test_review_note_must_be_text(self):
        with self.assertRaises(ValidationError):
            check_schedule(catalog(session()), schedule(dict(item("A101", "reserved"), review_ja=3)))


if __name__ == "__main__":
    unittest.main()
