"""Checks that the shared page stays free of personal plans."""

import unittest

from scripts.reinvent import ValidationError, check_schedule
from scripts.site import build_personal, build_shared, meters, merge_guides, validate_guide
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
        "venues": [{"id": "venetian", "name": "The Venetian", "aliases": ["Venetian"], "role_ja": "基調講演", "lat": 36.12, "lon": -115.17,
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

    def test_private_overlay_is_appended_and_marked(self):
        overlay = {"checked_on": "2026-10-07", "tips": [
            {"id": "pen", "category": "出入国・乗り継ぎ", "title_ja": "ペンを持つ", "body_ja": "書類用。",
             "year": 2025, "origin": "handover", "sources": []}]}
        merged = merge_guides(guide(), overlay)
        self.assertEqual(len(merged["tips"]), 2)
        html = build_shared(events(), merged, "2026-10-07")
        self.assertIn("社内の引き継ぎ", html)
        self.assertIn("ペンを持つ", html)

    def test_map_links_venues_to_google_maps_and_is_to_scale(self):
        html = build_shared(events(), guide(), "2026-10-07")
        self.assertIn("https://www.google.com/maps/search/?api=1&amp;query=The+Venetian%2C+Las+Vegas%2C+NV", html)
        self.assertIn("500m", html)
        a, b = guide()["venues"]
        self.assertAlmostEqual(meters(a, b), 2211, delta=10)  # 0.02 deg latitude

    def test_monorail_estimate_and_station_links(self):
        stations = [{"id": "s1", "kind": "monorail", "name": "North", "lat": 36.12, "lon": -115.168, "source": "https://example.com/m"},
                    {"id": "s2", "kind": "monorail", "name": "South", "lat": 36.10, "lon": -115.168, "source": "https://example.com/m"}]
        line = {"stations": ["s1", "s2"], "minutes": [5], "headway_min": 4, "headway_max": 8,
                "year": 2026, "source": "https://example.com/m"}
        html = build_shared(events(), guide(map_points=stations, monorail=line), "2026-10-07")
        self.assertIn("North駅→South駅", html)
        self.assertIn("query=North+Station%2C+Las+Vegas+Monorail", html)
        self.assertIn("路線・所要は未公表", html)

    def test_map_embeds_walking_legs_and_time_board(self):
        g = guide(map_legs=[{"from": "venetian", "to": "mgm"}], map_board={"to": "mgm"})
        html = build_shared(events(), g, "2026-10-07")
        self.assertIn('class="leg"', html)
        self.assertIn("徒歩38分", html)
        self.assertIn("MGM Grandまで", html)


    def test_place_names_render_as_linked_stickers(self):
        g = guide(places=[{"name": "Harrah's", "kind": "hotel", "maps_query": "Harrah's Las Vegas"}],
                  tips=[{"id": "x", "category": "食事", "title_ja": "朝食", "year": 2025, "sources": ["https://example.com"],
                         "body_ja": "Harrah's泊でもThe Venetianで食べた。<i>"}])
        html = build_shared(events(), g, "2026-10-07")
        self.assertIn('class="pl pl-v" href="https://www.google.com/maps/search/?api=1&amp;query=The+Venetian%2C+Las+Vegas%2C+NV"', html)
        self.assertIn(">Harrah&#x27;s</a>泊でも", html)
        self.assertIn("&lt;i&gt;", html)

    def test_each_venue_gets_its_own_color(self):
        g = guide()
        g["venues"][0]["color"] = "amber"
        html = build_shared(events(), g, "2026-10-07")
        self.assertIn('class="pl pl-v c-amber"', html)
        self.assertIn('<a class="c-amber" href=', html)
        self.assertIn(".c-amber{--pbg:", html)


    def test_private_stay_drives_hotel_section_and_board(self):
        overlay = {"checked_on": "2026-10-07", "stay": {"venue": "mgm", "points_ja": ["朝食はMGM Grandで済ませる。"]}}
        merged = merge_guides(guide(map_board={"to": "mgm"}), overlay)
        html = build_shared(events(), merged, "2026-10-07")
        self.assertIn("宿泊先", html)
        self.assertIn("MGM Grand（宿泊先）から", html)
        self.assertIn("朝食は<a class=", html)
        self.assertNotIn("宿泊先", build_shared(events(), guide(), "2026-10-07"))


    def test_official_badge_needs_aws_sources(self):
        g = guide(tips=[{"id": "a", "category": "食事", "title_ja": "公式", "body_ja": "x", "year": 2026,
                         "sources": ["https://aws.amazon.com/events/reinvent/faqs/"]},
                        {"id": "b", "category": "食事", "title_ja": "記事", "body_ja": "y", "year": 2026,
                         "sources": ["https://news.example.com/a"]}])
        html = build_shared(events(), g, "2026-10-07")
        self.assertEqual(html.count("2026公式"), 1)
        self.assertIn("2026年の情報", html)


class PersonalPageTests(unittest.TestCase):
    def test_review_flag_and_shared_link(self):
        reviewed = dict(item("A101", "reserved"), review_ja="イベント次第でキャンセル")
        html = build_personal(catalog(session()), events(), schedule(reviewed),
                              "https://example.com/shared", "2026-10-07T14:00:00+09:00", "2026-10-07")
        self.assertIn("見直し中", html)
        self.assertIn("イベント次第でキャンセル", html)
        self.assertIn('href="https://example.com/shared"', html)
        self.assertIn("A101 のあとに行く", html)

    def test_personal_page_venues_are_stickers(self):
        html = build_personal(catalog(session()), events(), schedule(item("A101", "reserved")),
                              "https://example.com/shared", "2026-10-07T14:00:00+09:00", "2026-10-07", guide())
        self.assertIn('class="pl pl-v"', html)
        self.assertIn('>Venetian</a>', html)

    def test_private_plans_show_only_on_personal_page(self):
        plan = {"title_ja": "招待パーティー", "starts_at": "2026-12-02T19:00:00-08:00",
                "ends_at": "2026-12-02T21:00:00-08:00", "venue": "Example Hall", "note_ja": "申込済み"}
        merged = merge_guides(guide(), {"checked_on": "2026-10-07", "plans": [plan]})
        html = build_personal(catalog(session()), events(), schedule(item("A101", "reserved")),
                              None, "2026-10-07T14:00:00+09:00", "2026-10-07", merged)
        self.assertIn("招待パーティー", html)
        self.assertIn("申込済み", html)
        self.assertIn("非公開", html)
        self.assertNotIn("招待パーティー", build_shared(events(), merged, "2026-10-07"))

    def test_meal_plans_get_their_own_badge(self):
        meal = {"kind": "meal", "title_ja": "昼食", "starts_at": "2026-11-30T12:00:00-08:00",
                "ends_at": "2026-11-30T13:00:00-08:00", "venue": "Venetian"}
        merged = merge_guides(guide(), {"checked_on": "2026-10-07", "plans": [meal]})
        html = build_personal(catalog(session()), events(), schedule(item("A101", "reserved")),
                              None, "2026-10-07T14:00:00+09:00", "2026-10-07", merged)
        self.assertIn('<span class="badge b-meal">食事</span> 昼食', html)
        self.assertIn("<td>目安</td>", html)

    def test_travel_plans_get_their_own_badge(self):
        trip = {"kind": "travel", "title_ja": "ラスベガス着", "starts_at": "2026-11-28T16:25:00-08:00", "venue": "LAS"}
        merged = merge_guides(guide(), {"checked_on": "2026-10-07", "plans": [trip]})
        html = build_personal(catalog(session()), events(), schedule(item("A101", "reserved")),
                              None, "2026-10-07T14:00:00+09:00", "2026-10-07", merged)
        self.assertIn('<span class="badge b-trip">移動</span> ラスベガス着', html)
        self.assertIn("<td>確定</td>", html)

    def test_private_plans_need_title_and_times(self):
        with self.assertRaises(ValidationError):
            merge_guides(guide(), {"checked_on": "2026-10-07", "plans": [{"title_ja": "x", "starts_at": "nope"}]})

    def test_prep_tasks_list_before_the_days_and_badge_the_session(self):
        prep = [{"task_ja": "ドキュメントを読む<b>", "done": True}, {"task_ja": "質問を書く", "done": False}]
        html = build_personal(catalog(session()), events(), schedule(dict(item("A101", "reserved"), prep=prep)),
                              None, "2026-10-07T14:00:00+09:00", "2026-10-07 10:00 JST")
        self.assertIn('<h2 id="prep">予習</h2>', html)
        self.assertIn("ドキュメントを読む&lt;b&gt;", html)
        self.assertIn('<li class="done">', html)
        self.assertIn("54日", html)
        self.assertIn('<a class="badge b-prep" href="#prep-A101">予習 1/2</a>', html)
        self.assertLess(html.index('id="prep"'), html.index("11/30（月）"))

    def test_finished_prep_shows_as_done(self):
        prep = [{"task_ja": "読む", "done": True}]
        html = build_personal(catalog(session()), events(), schedule(dict(item("A101", "reserved"), prep=prep)),
                              None, "2026-10-07T14:00:00+09:00", "2026-10-07")
        self.assertIn('href="#prep-A101">予習済み</a>', html)

    def test_no_prep_section_without_tasks(self):
        html = build_personal(catalog(session()), events(), schedule(item("A101", "reserved")),
                              None, "2026-10-07T14:00:00+09:00", "2026-10-07")
        self.assertNotIn('id="prep"', html)

    def test_prep_plans_get_their_own_badge(self):
        block = {"kind": "prep", "title_ja": "翌日のハンズオンを見直す", "starts_at": "2026-11-29T21:00:00-08:00",
                 "ends_at": "2026-11-29T21:30:00-08:00", "venue": "MGM Grand"}
        merged = merge_guides(guide(), {"checked_on": "2026-10-07", "plans": [block]})
        html = build_personal(catalog(session()), events(), schedule(item("A101", "reserved")),
                              None, "2026-10-07T14:00:00+09:00", "2026-10-07", merged)
        self.assertIn('<span class="badge b-prep">予習</span> 翌日のハンズオンを見直す', html)

    def test_prep_tasks_must_be_valid(self):
        for prep in ("読む", [{"task_ja": "", "done": False}], [{"task_ja": "読む", "done": "no"}],
                     [{"task_ja": "読む", "done": False, "url": 3}]):
            with self.assertRaises(ValidationError):
                check_schedule(catalog(session()), schedule(dict(item("A101", "reserved"), prep=prep)))

    def test_refresh_status_shows_on_personal_page_only(self):
        refresh = {"ran_at": "2026-10-11T06:30:00+09:00", "outcome": "changed", "summary_ja": "基調講演の時刻が出た<b>",
                   "changes_ja": ["12/2の基調講演を追加"], "api_ja": "カタログはまだ0件", "commit": "abc1234"}
        html = build_personal(catalog(session()), events(), schedule(item("A101", "reserved")),
                              None, "2026-10-07T14:00:00+09:00", "2026-10-07", refresh=refresh)
        self.assertIn("自動調査", html)
        self.assertIn("10/11 06:30", html)
        self.assertIn("基調講演の時刻が出た&lt;b&gt;", html)
        self.assertIn("<li>12/2の基調講演を追加</li>", html)
        self.assertIn("カタログはまだ0件", html)
        self.assertNotIn("自動調査", build_shared(events(), guide(), "2026-10-07"))

    def test_failed_refresh_is_flagged(self):
        refresh = {"ran_at": "2026-10-11T06:30:00+09:00", "outcome": "error", "summary_ja": "テストが失敗"}
        html = build_personal(catalog(session()), events(), schedule(item("A101", "reserved")),
                              None, "2026-10-07T14:00:00+09:00", "2026-10-07", refresh=refresh)
        self.assertIn('<span class="badge b-rev">要確認</span>', html)

    def test_review_note_must_be_text(self):
        with self.assertRaises(ValidationError):
            check_schedule(catalog(session()), schedule(dict(item("A101", "reserved"), review_ja=3)))


if __name__ == "__main__":
    unittest.main()
