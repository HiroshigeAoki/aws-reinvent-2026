#!/usr/bin/env python3
"""Build the shared guide page and the personal schedule page as static HTML."""

from __future__ import annotations

import argparse
from datetime import date, datetime
from html import escape
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

if __package__:
    from .reinvent import (
        EVENT_CATEGORIES, EVENT_INTENT, EVENT_REGISTRATION, ROOT, ValidationError, check_schedule,
        event_relation, is_text, parse_time, read_json, require_valid_catalog, require_valid_events,
        timezone, valid_date, validate_url,
    )
else:
    from reinvent import (
        EVENT_CATEGORIES, EVENT_INTENT, EVENT_REGISTRATION, ROOT, ValidationError, check_schedule,
        event_relation, is_text, parse_time, read_json, require_valid_catalog, require_valid_events,
        timezone, valid_date, validate_url,
    )

OUT_DIR = ROOT / "local-data" / "site"
CONFIG = ROOT / "local-data" / "site.json"
MANIFEST_HOOK = Path.home() / ".claude" / "hooks" / "html-artifact-manifest.sh"
WEEKDAYS = "月火水木金土日"
TIP_CATEGORIES = ("移動", "セッション・予約", "持ち物・服装", "食事", "体調", "通信・お金", "夜・イベント", "英語・現地")

CSS = """
:root{--bg:#f7f6f3;--card:#fff;--fg:#1f2328;--mut:#5f6670;--line:#e3e1dc;--acc:#b4530f;--acc2:#0f6b8f;--warn:#9a3b00;--warnbg:#fff1e5;--chip:#efece6;--ok:#1b6e3a}
@media (prefers-color-scheme:dark){:root{--bg:#16181c;--card:#1f2228;--fg:#e6e6e6;--mut:#9aa1ab;--line:#30343b;--acc:#f0a35e;--acc2:#6cc3e6;--warn:#ffb27a;--warnbg:#3a2717;--chip:#2a2e35;--ok:#7ed69b}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.75 system-ui,-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif}
a{color:var(--acc2)}
.wrap{max-width:980px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.6rem;margin:0 0 4px}
.lead{color:var(--mut);margin:0 0 16px}
nav{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:.9rem;margin:0 0 8px}
.note{background:var(--warnbg);border-left:4px solid var(--warn);padding:10px 14px;border-radius:6px;margin:12px 0 20px}
h2{font-size:1.25rem;border-bottom:2px solid var(--acc);padding-bottom:4px;margin:36px 0 12px}
h3{font-size:1.05rem;margin:22px 0 8px}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.9rem;background:var(--card)}
th,td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{background:var(--chip)}
td.tm{white-space:nowrap;font-variant-numeric:tabular-nums}
.en{color:var(--mut);font-size:.8rem}
.mut{color:var(--mut)}
.id{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--acc)}
.badge{display:inline-block;font-size:.74rem;border-radius:4px;padding:0 6px;border:1px solid currentColor;white-space:nowrap}
.b-ok{color:var(--ok)}.b-rev{color:var(--warn);background:var(--warnbg)}.b-ev{color:var(--acc2)}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.c{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px}
.c h4{font-size:.98rem;margin:0 0 4px;line-height:1.45}
.c p{margin:0;font-size:.9rem}
.src{font-size:.76rem;color:var(--mut);margin-top:6px}
svg.map{width:100%;max-width:520px;height:auto;background:var(--card);border:1px solid var(--line);border-radius:10px}
svg.map text{fill:var(--fg);font-size:12px}
svg.map .strip{stroke:var(--line);stroke-width:10;stroke-linecap:round}
svg.map circle{fill:var(--acc)}
svg.map .role{fill:var(--mut);font-size:10.5px}
footer{margin-top:40px;color:var(--mut);font-size:.82rem}
"""


def h(value: Any) -> str:
    return escape("" if value is None else str(value), quote=True)


def link(url: str, text: str) -> str:
    return f'<a href="{h(url)}" rel="noopener">{h(text)}</a>'


def day_label(day: str) -> str:
    value = date.fromisoformat(day)
    return f"{value.month}/{value.day}（{WEEKDAYS[value.weekday()]}）"


def clock(start: datetime | None, end: datetime | None, zone) -> str:
    if start is None:
        return "時刻未定"
    text = start.astimezone(zone).strftime("%H:%M")
    return text + ("–" + end.astimezone(zone).strftime("%H:%M") if end else "")


def validate_guide(guide: Any) -> dict[str, Any]:
    """Light schema check: every displayed fact needs a source URL and a year."""
    errors: list[str] = []
    if not isinstance(guide, dict) or not valid_date(guide.get("checked_on")):
        raise ValidationError("guide: checked_on (YYYY-MM-DD) を持つオブジェクトが必要です")
    shapes = {
        "venues": ("id", "name", "role_ja"), "transport": ("id", "title_ja", "body_ja"),
        "walk_times": ("from", "to"), "tips": ("id", "category", "title_ja", "body_ja"),
        "links": ("title", "url", "why_ja"),
    }
    for collection, fields in shapes.items():
        entries = guide.get(collection, [])
        if not isinstance(entries, list):
            errors.append(f"guide.{collection}: 配列が必要です")
            continue
        for index, entry in enumerate(entries):
            label = f"guide.{collection}[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{label}: JSON オブジェクトが必要です")
                continue
            for name in fields:
                if not is_text(entry.get(name)):
                    errors.append(f"{label}.{name}: 空でない文字列が必要です")
            urls = entry.get("sources") if collection == "tips" else [entry.get("url" if collection == "links" else "source")]
            if not isinstance(urls, list) or not urls:
                errors.append(f"{label}: 出典 URL が必要です")
                urls = []
            for url in urls:
                try:
                    validate_url(url, f"{label} 出典")
                except ValidationError as exc:
                    errors.append(str(exc))
            if collection != "links" and entry.get("year") is not None and type(entry.get("year")) is not int:
                errors.append(f"{label}.year: 整数か null が必要です")
            if collection == "tips" and entry.get("category") not in TIP_CATEGORIES:
                errors.append(f"{label}.category: {' / '.join(TIP_CATEGORIES)} のいずれかが必要です")
    if errors:
        raise ValidationError("\n".join(errors))
    return guide


def year_badge(year: Any, current: int) -> str:
    if year is None:
        return '<span class="badge">年不明</span>'
    if year == current:
        return f'<span class="badge b-ok">{year} 公式</span>'
    return f'<span class="badge">{h(year)} 年の情報</span>'


def page(title: str, head_meta: str, body: str) -> str:
    return (
        "<!doctype html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<meta http-equiv=\"content-security-policy\" content=\"script-src 'none'\">\n"
        f"<title>{h(title)}</title>\n{head_meta}<style>{CSS}</style>\n</head>\n"
        f"<body><div class=\"wrap\">\n{body}\n</div></body>\n</html>\n"
    )


def venue_map(venues: list[dict[str, Any]]) -> str:
    """Schematic north-to-south strip; positions use lat/lon when present."""
    placed = [v for v in venues if isinstance(v.get("lat"), (int, float)) and isinstance(v.get("lon"), (int, float))]
    if len(placed) < 2:
        return ""
    lats = [v["lat"] for v in placed]
    lons = [v["lon"] for v in placed]
    top, bottom = max(lats), min(lats)
    west, east = min(lons), max(lons)
    width, height, pad = 520, 60 + 56 * len(placed), 30
    def y(lat):
        return pad + (top - lat) / ((top - bottom) or 1) * (height - 2 * pad)
    def x(lon):
        return 150 + (lon - west) / ((east - west) or 1) * 60
    parts = [f'<svg class="map" viewBox="0 0 {width} {height}" role="img" aria-label="会場の南北配置（模式図）">',
             f'<line class="strip" x1="180" y1="{pad - 10}" x2="180" y2="{height - pad + 10}"/>',
             f'<text x="12" y="{pad}">北 ↑</text><text x="12" y="{height - pad + 4}">南 ↓</text>']
    last = -1e9
    for venue in sorted(placed, key=lambda v: -v["lat"]):
        cy = max(y(venue["lat"]), last + 34)
        last = cy
        cx = x(venue["lon"])
        parts.append(f'<circle cx="{cx:.1f}" cy="{y(venue["lat"]):.1f}" r="6"/>')
        parts.append(f'<line x1="{cx + 6:.1f}" y1="{y(venue["lat"]):.1f}" x2="236" y2="{cy:.1f}" stroke="currentColor" stroke-opacity=".3"/>')
        parts.append(f'<text x="240" y="{cy:.1f}">{h(venue["name"])}</text>')
        parts.append(f'<text class="role" x="240" y="{cy + 14:.1f}">{h(venue["role_ja"][:28])}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def build_shared(events: dict[str, Any], guide: dict[str, Any], built_on: str) -> str:
    """General info only: no session IDs, no intents, no personal notes."""
    zone = timezone(events["timezone"], "timezone")
    year = 2026
    nav = "".join(f'<a href="#{a}">{t}</a>' for a, t in
                  (("events", "日別イベント"), ("map", "会場マップ"), ("move", "移動"), ("tips", "Tips"), ("links", "リンク")))
    body = [
        "<h1>AWS re:Invent 2026 現地ガイド</h1>",
        f'<p class="lead">ラスベガス 2026-11-30〜12-04（受付は 11/29 から）。時刻はすべて現地時間（PST, UTC−8）。最終更新 {h(built_on)}。</p>',
        f"<nav>{nav}</nav>",
        '<div class="note">公式発表前の項目は「未確認」と書いています。'
        '過去年の情報には年を付けました。2026 年は変わることがあるので、最終確認は公式ページと公式アプリで行ってください。</div>',
        '<h2 id="events">日別イベント</h2>',
        f'<p class="mut">確認日 {h(events["checked_on"])}。セッション以外の全体イベントです。</p>',
    ]
    by_day: dict[str | None, list[dict[str, Any]]] = {}
    for entry in events["events"]:
        by_day.setdefault(entry["date"], []).append(entry)
    for day in sorted(by_day, key=lambda d: d or "9999"):
        body.append(f"<h3>{h(day_label(day) if day else '日付未定')}</h3>")
        body.append('<div class="scroll"><table><tr><th>時間</th><th>イベント</th><th>種類</th><th>会場</th><th>登録</th><th>メモ</th></tr>')
        def order(entry):
            start = parse_time(entry["starts_at"], "starts_at")
            return (start is None, start.timestamp() if start else 0, entry["id"])
        for entry in sorted(by_day[day], key=order):
            start = parse_time(entry["starts_at"], "starts_at")
            end = parse_time(entry["ends_at"], "ends_at")
            title = link(entry["url"], entry["title_ja"] or entry["title"])
            if entry["title_ja"]:
                title += f'<br><span class="en">{h(entry["title"])}</span>'
            body.append(
                f'<tr><td class="tm">{h(clock(start, end, zone))}</td><td>{title}</td>'
                f'<td>{h(EVENT_CATEGORIES[entry["category"]])}</td><td>{h(entry["venue"] or "未確認")}</td>'
                f'<td>{h(EVENT_REGISTRATION[entry["registration"]])}</td><td>{h(entry.get("public_note_ja") or "—")}</td></tr>'
            )
        body.append("</table></div>")
    body.append('<h2 id="map">会場マップ</h2>')
    body.append('<p class="mut">ストリップ沿いの南北の並びを示す模式図です。距離は正確ではありません。正確な地図は下の公式リンクで確認してください。</p>')
    body.append(venue_map(guide.get("venues", [])))
    if guide.get("venues"):
        body.append('<div class="scroll"><table><tr><th>会場</th><th>主な用途</th><th>年</th></tr>')
        for venue in guide["venues"]:
            body.append(f'<tr><td>{link(venue["source"], venue["name"])}</td><td>{h(venue["role_ja"])}</td>'
                        f'<td>{year_badge(venue.get("year"), year)}</td></tr>')
        body.append("</table></div>")
    body.append('<h2 id="move">移動</h2><div class="cards">')
    for item in guide.get("transport", []):
        body.append(f'<div class="c"><h4>{h(item["title_ja"])} {year_badge(item.get("year"), year)}</h4>'
                    f'<p>{h(item["body_ja"])}</p><div class="src">{link(item["source"], "出典")}</div></div>')
    body.append("</div>")
    names = {v["id"]: v["name"] for v in guide.get("venues", [])}
    if guide.get("walk_times"):
        body.append('<h3>会場間の所要時間（目安）</h3><div class="scroll"><table><tr><th>区間</th><th>手段</th><th>目安</th><th>メモ</th><th>年</th></tr>')
        for walk in guide["walk_times"]:
            minutes = f'{walk["minutes"]} 分' if walk.get("minutes") is not None else "未確認"
            mode = {"walk": "徒歩", "shuttle": "シャトル", "monorail": "モノレール"}.get(walk.get("mode"), walk.get("mode") or "—")
            body.append(f'<tr><td>{h(names.get(walk["from"], walk["from"]))} ↔ {h(names.get(walk["to"], walk["to"]))}</td>'
                        f'<td>{h(mode)}</td><td class="tm">{h(minutes)}</td><td>{h(walk.get("note_ja") or "—")} '
                        f'<span class="src">{link(walk["source"], "出典")}</span></td><td>{year_badge(walk.get("year"), year)}</td></tr>')
        body.append("</table></div>")
    body.append('<h2 id="tips">過去の参加者の Tips</h2>'
                '<p class="mut">過去の参加レポートで繰り返し挙がっている点を要約しました。出典を開くと元の記事を読めます。</p>')
    tips = guide.get("tips", [])
    for category in TIP_CATEGORIES:
        selected = [t for t in tips if t["category"] == category]
        if not selected:
            continue
        body.append(f'<h3>{h(category)}</h3><div class="cards">')
        for tip in selected:
            sources = " ".join(link(url, f"出典{i + 1}") for i, url in enumerate(tip["sources"]))
            body.append(f'<div class="c"><h4>{h(tip["title_ja"])}</h4><p>{h(tip["body_ja"])}</p>'
                        f'<div class="src">{year_badge(tip.get("year"), year)} {sources}</div></div>')
        body.append("</div>")
    body.append('<h2 id="links">リンク</h2><ul>')
    for item in guide.get("links", []):
        body.append(f'<li>{link(item["url"], item["title"])}: {h(item["why_ja"])}</li>')
    for source in events["sources"]:
        body.append(f'<li>{link(source["url"], source["label_ja"])}</li>')
    body.append("</ul>")
    body.append(f'<footer>ガイド情報の確認日 {h(guide["checked_on"])}。イベント情報の確認日 {h(events["checked_on"])}。'
                "公式ページの説明文は転載せず、要点を自分の言葉でまとめています。</footer>")
    meta = '<meta name="summary" content="re:Invent 2026 の日別イベント・会場・移動・過去参加者の Tips">\n'
    return page("re:Invent 2026 現地ガイド", meta, "\n".join(body))


def build_personal(catalog: dict[str, Any], events: dict[str, Any], schedule: dict[str, Any],
                   shared_url: str | None, created: str, built_on: str) -> str:
    report = check_schedule(catalog, schedule, events)
    zone = timezone(schedule["timezone"], "schedule.timezone")
    sessions = {(s["year"], s["id"]): s for s in catalog["sessions"]}
    active = [(item, sessions[(item["year"], item["id"])]) for item in schedule["items"]
              if item["status"] in {"planned", "reserved"}]
    rows: list[tuple[datetime, str]] = []
    for item, session in active:
        start = parse_time(session["starts_at"], "starts_at")
        end = parse_time(session["ends_at"], "ends_at")
        if start is None:
            continue
        status = '<span class="badge b-ok">予約済み</span>' if item["status"] == "reserved" else '<span class="badge">計画</span>'
        if is_text(item.get("review_ja")):
            status += f' <span class="badge b-rev">見直し中</span><br><span class="mut">{h(item["review_ja"])}</span>'
        title = (f'<span class="id">{h(session["id"])}</span> {link(session["url"], session.get("title_ja") or session["title"])}'
                 f'<br><span class="en">{h(session["title"])} · {h(session["format"])} {h(session["level"])}</span>')
        rows.append((start, f'<tr><td class="tm">{h(clock(start, end, zone))}</td><td>{title}</td>'
                            f'<td>{h(session["venue"] or "未確認")}</td><td>{status}</td></tr>'))
    session_list = [s for _, s in active]
    for entry in events["events"]:
        start = parse_time(entry["starts_at"], "starts_at")
        if entry["intent"] not in {"go", "maybe"} or start is None:
            continue
        end = parse_time(entry["ends_at"], "ends_at")
        relation = event_relation(entry, session_list, schedule["transfer_minutes"])
        note = " / ".join(x for x in (entry["note_ja"], relation if relation not in {"なし", "—"} else None) if x)
        rows.append((start, f'<tr><td class="tm">{h(clock(start, end, zone))}</td>'
                            f'<td><span class="badge b-ev">イベント</span> {link(entry["url"], entry["title_ja"] or entry["title"])}'
                            f'<br><span class="mut">{h(note)}</span></td><td>{h(entry["venue"] or "未確認")}</td>'
                            f'<td>{h(EVENT_INTENT[entry["intent"]])}</td></tr>'))
    reviewing = [(item, s) for item, s in active if is_text(item.get("review_ja"))]
    shared = link(shared_url, "共有版の現地ガイド（会場マップ・移動・Tips・全体イベント）") if shared_url else "共有版: 未公開"
    body = [
        "<h1>re:Invent 2026 自分の予定</h1>",
        f'<p class="lead">現地時間（PST）。最終更新 {h(built_on)}。予約 {len(active)} 件、見直し中 {len(reviewing)} 件。</p>',
        f'<div class="note">{shared}</div>',
    ]
    if report.errors or report.warnings:
        body.append('<div class="note"><b>予定チェック</b><ul>' + "".join(f"<li>{h(m)}</li>" for m in report.errors + report.warnings) + "</ul></div>")
    if reviewing:
        body.append("<h2>見直し中の予約</h2><ul>")
        for item, s in reviewing:
            body.append(f'<li><span class="id">{h(s["id"])}</span> {h(s.get("title_ja") or s["title"])}: {h(item["review_ja"])}</li>')
        body.append("</ul>")
    current = None
    for start, row in sorted(rows, key=lambda r: r[0]):
        day = start.astimezone(zone).date().isoformat()
        if day != current:
            if current is not None:
                body.append("</table></div>")
            body.append(f"<h2>{h(day_label(day))}</h2>")
            body.append('<div class="scroll"><table><tr><th>時間</th><th>内容</th><th>会場</th><th>状態</th></tr>')
            current = day
        body.append(row)
    if current is not None:
        body.append("</table></div>")
    undated = [e for e in events["events"] if e["intent"] in {"go", "maybe"} and e["starts_at"] is None]
    if undated:
        body.append("<h2>時刻未定で気になるイベント</h2><ul>")
        for e in undated:
            body.append(f'<li>{link(e["url"], e["title_ja"] or e["title"])}（{h(day_label(e["date"]) if e["date"] else "日付未定")}）'
                        f' {h(EVENT_INTENT[e["intent"]])}: {h(e["note_ja"] or "")}</li>')
        body.append("</ul>")
    body.append(f'<footer>カタログ確認日 {h(catalog["checked_on"])}。イベント確認日 {h(events["checked_on"])}。'
                "生成元は data/catalog.json・data/events.json・planning/schedule.json。</footer>")
    meta = (f'<meta name="tags" content="plan, reinvent-2026, aws">\n<meta name="created" content="{h(created)}">\n'
            '<meta name="summary" content="予約セッションと参加予定イベントの日別表。共有版ガイドへのリンク付き">\n')
    return page("re:Invent 2026 自分の予定", meta, "\n".join(body))


def load_config() -> dict[str, Any]:
    return read_json(CONFIG) if CONFIG.exists() else {}


def build(config: dict[str, Any]) -> tuple[Path, Path]:
    catalog = require_valid_catalog(read_json(ROOT / "data" / "catalog.json"))
    events = require_valid_events(read_json(ROOT / "data" / "events.json"))
    schedule = read_json(ROOT / "planning" / "schedule.json")
    guide = validate_guide(read_json(ROOT / "data" / "guide.json"))
    built_on = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    shared_path = OUT_DIR / "shared" / "index.html"
    personal_path = OUT_DIR / "personal.html"
    shared_path.parent.mkdir(parents=True, exist_ok=True)
    shared_path.write_text(build_shared(events, guide, built_on), encoding="utf-8")
    created = config.get("personal_created") or datetime.now().astimezone().isoformat(timespec="seconds")
    personal_path.write_text(build_personal(catalog, events, schedule, config.get("shared_url"), created, built_on),
                             encoding="utf-8")
    return shared_path, personal_path


def publish(config: dict[str, Any], shared_path: Path, personal_path: Path) -> None:
    if config.get("gera_id"):
        subprocess.run(["gera", "update", config["gera_id"], str(shared_path)], check=True)
    else:
        print("共有版は未公開です。初回は gera push で公開し、ID と URL を local-data/site.json に書いてください。")
    target = config.get("personal_path")
    if target:
        target = Path(target).expanduser()
        shutil.copyfile(personal_path, target)
        if MANIFEST_HOOK.exists():
            payload = json.dumps({"tool_input": {"file_path": str(target)}})
            subprocess.run([str(MANIFEST_HOOK)], input=payload, text=True, check=False)
        print(f"個人版を更新: {target}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "publish"))
    args = parser.parse_args(argv)
    try:
        config = load_config()
        shared_path, personal_path = build(config)
        print(f"OK: {shared_path}\nOK: {personal_path}")
        if args.command == "publish":
            publish(config, shared_path, personal_path)
        return 0
    except (ValidationError, OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
