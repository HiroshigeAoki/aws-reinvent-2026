#!/usr/bin/env python3
"""Build the shared guide page and the personal schedule page as static HTML."""

from __future__ import annotations

import argparse
from datetime import date, datetime
from html import escape
import json
import math
import re
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any
from urllib.parse import quote_plus

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
TIP_CATEGORIES = ("準備・荷造り", "出入国・乗り継ぎ", "ホテル", "移動", "セッション・予約", "持ち物・服装", "食事", "体調", "通信・お金", "夜・イベント", "英語・現地", "天気", "緊急時", "空き時間")
PRIVATE_GUIDE = ROOT / "private" / "guide-private.json"

CSS = """
:root{--venuebg:#fbe3cf;--venuefg:#8a3d06;--stnbg:#dcedf4;--bg:#f7f6f3;--card:#fff;--fg:#1f2328;--mut:#5f6670;--line:#e3e1dc;--acc:#b4530f;--acc2:#0f6b8f;--warn:#9a3b00;--warnbg:#fff1e5;--chip:#efece6;--ok:#1b6e3a}
@media (prefers-color-scheme:dark){:root{--venuebg:#4a2c14;--venuefg:#ffc999;--stnbg:#163846;--bg:#16181c;--card:#1f2228;--fg:#e6e6e6;--mut:#9aa1ab;--line:#30343b;--acc:#f0a35e;--acc2:#6cc3e6;--warn:#ffb27a;--warnbg:#3a2717;--chip:#2a2e35;--ok:#7ed69b}}
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
.mapwrap{overflow-x:auto;max-width:640px;margin:0 0 12px}
svg.map{display:block;width:100%;min-width:540px;height:auto;background:var(--card);border:1px solid var(--line);border-radius:10px;margin:0}
svg.map text{fill:var(--fg);font-size:13px}
svg.map .strip{fill:none;stroke:var(--line);stroke-width:12;stroke-linecap:round;stroke-linejoin:round}
svg.map .rail{fill:none;stroke:var(--acc2);stroke-width:2.5;stroke-dasharray:6 4}
svg.map .stn{fill:var(--card);stroke:var(--acc2);stroke-width:2}
svg.map .stn-label{fill:var(--acc2);font-size:10.5px}
svg.map circle{fill:var(--acc)}
svg.map a .venue{fill:var(--acc);font-weight:700;text-decoration:underline}
svg.map .role{fill:var(--mut);font-size:11px}
svg.map .bar{stroke:var(--fg);stroke-width:3}
svg.map .leg{stroke:var(--mut);stroke-width:2;stroke-dasharray:0 5;stroke-linecap:round}
svg.map .leg-label{fill:var(--fg);font-size:11.5px;font-weight:600;paint-order:stroke;stroke:var(--card);stroke-width:4px;stroke-linejoin:round}
svg.map .leg-km{fill:var(--mut);font-weight:400}
svg.map .board rect{fill:var(--bg);stroke:var(--line)}
svg.map .board text{font-size:12px}
svg.map .board .board-title{font-weight:700;font-size:13px}
svg.map .board .board-head{fill:var(--mut);font-size:10.5px}
svg.map .board .board-mono{fill:var(--acc2);font-weight:700}
svg.map .board .board-walk{fill:var(--mut)}
svg.map .board .board-shuttle{fill:var(--fg);font-size:11px}
svg.map .board .role{font-size:10.5px}
a.pl,span.pl{display:inline-block;padding:0 .45em;margin:0 .12em;border-radius:5px;line-height:1.55;font-size:.92em;white-space:nowrap;text-decoration:none;color:var(--fg);background:var(--chip);border:1px solid var(--line)}
a.pl:hover{border-color:currentColor}
a.pl:focus-visible{outline:2px solid var(--acc2);outline-offset:1px}
a.pl-v,span.pl-v{background:var(--venuebg);border-color:transparent;color:var(--venuefg);font-weight:600}
a.pl-st,span.pl-st{background:var(--stnbg);border-color:transparent;color:var(--acc2)}
details.more{margin:4px 0 12px}
details.more summary{cursor:pointer;color:var(--acc2);font-size:.9rem;padding:4px 0}
details.more summary:focus-visible{outline:2px solid var(--acc2);outline-offset:2px}
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
        "links": ("title", "url", "why_ja"), "day_flow": ("time", "what_ja"),
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
            if not isinstance(urls, list) or (not urls and entry.get("origin") != "handover"):
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
    line = guide.get("monorail")
    if line is not None:
        stations, gaps = line.get("stations"), line.get("minutes")
        if not (isinstance(stations, list) and isinstance(gaps, list) and len(gaps) == len(stations) - 1
                and all(type(m) is int and m > 0 for m in gaps)):
            errors.append("guide.monorail: stations と、その間の minutes（正の整数、駅数 −1 個）が必要です")
        try:
            validate_url(line.get("source"), "guide.monorail 出典")
        except ValidationError as exc:
            errors.append(str(exc))
    if errors:
        raise ValidationError("\n".join(errors))
    return guide


def merge_guides(public: Any, private: Any) -> dict[str, Any]:
    """Append the gitignored overlay (company-internal handover notes) to the public guide."""
    guide = validate_guide(public)
    if private is None:
        return guide
    private = validate_guide(private)
    merged = dict(guide)
    for collection in ("venues", "transport", "walk_times", "tips", "links", "day_flow", "map_points"):
        merged[collection] = list(guide.get(collection, [])) + list(private.get(collection, []))
    return merged


def year_badge(year: Any, current: int) -> str:
    if year is None:
        return '<span class="badge">年不明</span>'
    if year == current:
        return f'<span class="badge b-ok">{year}公式</span>'
    return f'<span class="badge">{h(year)}年の情報</span>'


def page(title: str, head_meta: str, body: str) -> str:
    return (
        "<!doctype html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<meta http-equiv=\"content-security-policy\" content=\"script-src 'none'\">\n"
        f"<title>{h(title)}</title>\n{head_meta}<style>{CSS}</style>\n</head>\n"
        f"<body><div class=\"wrap\">\n{body}\n</div></body>\n</html>\n"
    )


def maps_url(venue: dict[str, Any]) -> str:
    query = venue.get("maps_query") or f'{venue["name"]}, Las Vegas, NV'
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(query)


PLACE_CLASSES = {"venue": "pl pl-v", "station": "pl pl-st"}


def place_index(guide: dict[str, Any] | None) -> list[tuple[str, str, str]]:
    """(text, css class, Google Maps URL) for every place name, longest first."""
    if not guide:
        return []
    found: dict[str, tuple[str, str, str]] = {}
    def add(names, kind, entry):
        url = maps_url(entry)
        for name in names:
            if name and name not in found:
                found[name] = (name, PLACE_CLASSES.get(kind, "pl"), url)
    for venue in guide.get("venues", []):
        add([venue["name"], *venue.get("aliases", [])], "venue", venue)
    for point in guide.get("map_points", []):
        if point.get("kind") == "monorail":
            query = {"name": point["name"], "maps_query": f'{point["name"]} Station, Las Vegas Monorail'}
            add([f'{n}駅' for n in (point["name"], *point.get("aliases", []))], "station", query)
    for place in guide.get("places", []):
        add([place["name"], *place.get("aliases", [])], place.get("kind"), place)
    return sorted(found.values(), key=lambda p: -len(p[0]))


def rich(text: Any, places: list[tuple[str, str, str]]) -> str:
    """Escape text and turn each known place name into a sticker linking to Google Maps."""
    text = str(text)
    if not places:
        return h(text)
    lookup = {name: (cls, url) for name, cls, url in places}
    pattern = re.compile("(?<![A-Za-z0-9])(" + "|".join(re.escape(name) for name, _, _ in places) + ")(?![A-Za-z0-9])")
    out, last = [], 0
    for match in pattern.finditer(text):
        cls, url = lookup[match.group(1)]
        out.append(h(text[last:match.start()]))
        out.append(f'<a class="{cls}" href="{h(url)}" rel="noopener">{h(match.group(1))}</a>')
        last = match.end()
    out.append(h(text[last:]))
    return "".join(out)


def has_point(entry: dict[str, Any]) -> bool:
    return isinstance(entry.get("lat"), (int, float)) and isinstance(entry.get("lon"), (int, float))


def meters(a: dict[str, Any], b: dict[str, Any]) -> float:
    """Equirectangular distance; accurate to well under 1% across the Strip."""
    lat0 = math.radians((a["lat"] + b["lat"]) / 2)
    dx = (b["lon"] - a["lon"]) * 111320 * math.cos(lat0)
    dy = (b["lat"] - a["lat"]) * 110574
    return math.hypot(dx, dy)


def walk_minutes(distance: float) -> int:
    """Straight line x1.3 detour at 75 m/min; casinos add indoor walking on top."""
    return max(1, round(distance * 1.3 / 75))


def venue_map(guide: dict[str, Any]) -> str:
    """To-scale map: Strip, monorail, venues (linked to Google Maps), scale bar."""
    venues = [v for v in guide.get("venues", []) if has_point(v)]
    points = [p for p in guide.get("map_points", []) if has_point(p)]
    if len(venues) < 2:
        return ""
    north, south = max(v["lat"] for v in venues) + 0.002, min(v["lat"] for v in venues) - 0.002
    east = max(v["lon"] for v in venues) + 0.002
    points = [p for p in points if p.get("kind") == "airport" or (south <= p["lat"] <= north and p["lon"] <= east)]
    framed = venues + [p for p in points if p.get("kind") in {"monorail", "strip"}]
    lat0 = math.radians(sum(v["lat"] for v in venues) / len(venues))
    def project(entry):
        return (entry["lon"] * 111320 * math.cos(lat0), -entry["lat"] * 110574)
    xs, ys = zip(*(project(e) for e in framed))
    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
    width, max_height, pad_x, pad_y = 640, 640, 150, 40
    scale = min((width - 2 * pad_x) / ((max_x - min_x) or 1), (max_height - 2 * pad_y) / ((max_y - min_y) or 1))
    height = round((max_y - min_y) * scale + 2 * pad_y)
    left = (width - (max_x - min_x) * scale) / 2
    def xy(entry):
        px, py = project(entry)
        return left + (px - min_x) * scale, pad_y + (py - min_y) * scale
    parts = [f'<svg class="map" viewBox="0 0 {width} {height}" role="img" aria-label="会場の位置（縮尺あり）">']
    strip = [xy(p) for p in points if p.get("kind") == "strip"]
    if len(strip) >= 2:
        path = " ".join(f"{x:.1f},{y:.1f}" for x, y in sorted(strip, key=lambda q: q[1]))
        parts.append(f'<polyline class="strip" points="{path}"/>')
        top = min(strip, key=lambda q: q[1])
        parts.append(f'<text class="role" x="{top[0] - 12:.1f}" y="{top[1] + 4:.1f}" text-anchor="end">Las Vegas Blvd（ストリップ）</text>')
    by_id = {v["id"]: v for v in venues}
    for leg in guide.get("map_legs", []):
        a, b = by_id.get(leg["from"]), by_id.get(leg["to"])
        if not a or not b:
            continue
        (x1, y1), (x2, y2) = xy(a), xy(b)
        d = meters(a, b)
        mx, my = (x1 + x2) / 2 + leg.get("dx", 10), (y1 + y2) / 2 + leg.get("dy", 0)
        anchor = "end" if leg.get("dx", 10) < 0 else "start"
        parts.append(f'<line class="leg" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'
                     f'<text class="leg-label" x="{mx:.1f}" y="{my:.1f}" text-anchor="{anchor}">'
                     f'徒歩{walk_minutes(d)}分<tspan class="leg-km"> {d / 1000:.1f}km</tspan></text>')
    rail = [(xy(p), p) for p in points if p.get("kind") == "monorail"]
    if len(rail) >= 2:
        path = " ".join(f"{x:.1f},{y:.1f}" for (x, y), _ in sorted(rail, key=lambda q: q[0][1]))
        parts.append(f'<polyline class="rail" points="{path}"/>')
        for (x, y), station in rail:
            east = station.get("label_side") == "right"
            query = {"name": station["name"], "maps_query": station.get("maps_query") or f'{station["name"]} Station, Las Vegas Monorail'}
            parts.append(f'<a href="{h(maps_url(query))}" target="_blank" rel="noopener">'
                         f'<rect class="stn" x="{x - 4:.1f}" y="{y - 4:.1f}" width="8" height="8"/>'
                         f'<text class="stn-label" x="{x + 8 if east else x - 8:.1f}" y="{y + 4:.1f}" text-anchor="{"start" if east else "end"}">{h(station["name"])}駅</text></a>')
    for venue in venues:
        x, y = xy(venue)
        west = venue.get("label_side") == "left"
        anchor, tx = ("end", x - 10) if west else ("start", x + 10)
        ty = y + 4 + venue.get("label_dy", 0)
        parts.append(f'<a href="{h(maps_url(venue))}" target="_blank" rel="noopener">'
                     f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7"/>'
                     f'<text class="venue" x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anchor}">{h(venue["name"])}</text></a>')
    hub = by_id.get((guide.get("map_board") or {}).get("to"))
    if hub:
        others = sorted((v for v in venues if v is not hub), key=lambda v: -v["lat"])
        bw, row = 236, 20
        bh = 46 + row * len(others) + 42
        bx = width - bw - 12
        by = (min(xy(v)[1] for v in others[-2:]) + xy(hub)[1]) / 2 - bh / 2
        wait = (guide.get("monorail") or {}).get("headway_max", 0)
        parts.append(f'<g class="board"><rect x="{bx:.1f}" y="{by:.1f}" width="{bw}" height="{bh}" rx="8"/>'
                     f'<text class="board-title" x="{bx + 12:.1f}" y="{by + 20:.1f}">{h(hub["name"])}まで</text>'
                     f'<text class="board-head" x="{bx + 124:.1f}" y="{by + 38:.1f}">モノレール</text>'
                     f'<text class="board-head" x="{bx + bw - 12:.1f}" y="{by + 38:.1f}" text-anchor="end">徒歩</text>')
        for i, v in enumerate(others):
            ty = by + 58 + row * i
            trip = monorail_trip(guide, v, hub)
            mono = f"{trip[0]}〜{trip[0] + wait}分" if trip else "—"
            parts.append(f'<text x="{bx + 12:.1f}" y="{ty:.1f}">{h(v["name"])}</text>'
                         f'<text class="board-mono" x="{bx + 124:.1f}" y="{ty:.1f}">{mono}</text>'
                         f'<text class="board-walk" x="{bx + bw - 12:.1f}" y="{ty:.1f}" text-anchor="end">'
                         f'{walk_minutes(meters(v, hub))}分</text>')
        parts.append(f'<text class="board-shuttle" x="{bx + 12:.1f}" y="{by + bh - 26:.1f}">シャトル: 2026年の路線と時刻は未公表</text>'
                     f'<text class="role" x="{bx + 12:.1f}" y="{by + bh - 8:.1f}">モノレールは電車待ち込み。館内の移動は別</text></g>')
    bar = 500 * scale
    parts.append(f'<line class="bar" x1="20" y1="{height - 20}" x2="{20 + bar:.1f}" y2="{height - 20}"/>'
                 f'<text class="role" x="20" y="{height - 28}">500m（徒歩約7〜9分）</text>'
                 f'<text class="role" x="{width - 20}" y="24" text-anchor="end">↑ 北</text>')
    airport = next((p for p in points if p.get("kind") == "airport"), None)
    if airport:
        nearest = min(venues, key=lambda v: meters(v, airport))
        parts.append(f'<text class="role" x="{width - 20}" y="{height - 20}" text-anchor="end">'
                     f'空港（LAS）は{h(nearest["name"])}から南東へ約{meters(nearest, airport) / 1000:.1f}km（図の外）</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def monorail_trip(guide: dict[str, Any], a: dict[str, Any], b: dict[str, Any]) -> tuple[int, str, str] | None:
    """Fastest walk-ride-walk over every station pair, excluding the wait for a train."""
    line = guide.get("monorail")
    points = {p["id"]: p for p in guide.get("map_points", []) if has_point(p)}
    if not line or not all(s in points for s in line["stations"]):
        return None
    order, gaps = line["stations"], line["minutes"]
    best = None
    for i, s in enumerate(order):
        for j, t in enumerate(order):
            if i == j:
                continue
            lo, hi = sorted((i, j))
            total = walk_minutes(meters(a, points[s])) + sum(gaps[lo:hi]) + walk_minutes(meters(points[t], b))
            if best is None or total < best[0]:
                best = (total, points[s]["name"], points[t]["name"])
    return best


def distance_table(guide: dict[str, Any]) -> str:
    venues = [v for v in guide.get("venues", []) if has_point(v)]
    if len(venues) < 2:
        return ""
    places = place_index(guide)
    line = guide.get("monorail") or {}
    wait = line.get("headway_max", 0)
    rows = ['<div class="scroll"><table><tr><th>区間</th><th>直線</th><th>徒歩</th>'
            '<th>モノレール</th><th>シャトル</th><th>目安の手段</th></tr>']
    for i, a in enumerate(venues):
        for b in venues[i + 1:]:
            d = meters(a, b)
            walk = walk_minutes(d)
            trip = monorail_trip(guide, a, b)
            faster = trip is not None and trip[0] + wait / 2 < walk
            if faster:
                mono = (f"約{trip[0]}〜{trip[0] + wait}分"
                        f'<br><span class="mut">{h(trip[1])}駅→{h(trip[2])}駅</span>')
            else:
                mono = '<span class="mut">徒歩の方が早い</span>'
            far = walk > 25
            shuttle = "路線・所要は未公表" if far else '<span class="mut">—</span>'
            if not far:
                pick = "徒歩"
            elif faster:
                pick = "モノレール / シャトル"
            else:
                pick = "徒歩（シャトルは路線次第）"
            rows.append(f"<tr><td>{rich(a['name'], places)} ↔ {rich(b['name'], places)}</td><td class=\"tm\">{d / 1000:.1f}km</td>"
                        f'<td class="tm">約{walk}分</td><td class="tm">{mono}</td><td>{shuttle}</td><td>{pick}</td></tr>')
    rows.append("</table></div>")
    return "\n".join(rows)


def build_shared(events: dict[str, Any], guide: dict[str, Any], built_on: str) -> str:
    """General info only: no session IDs, no intents, no personal notes."""
    zone = timezone(events["timezone"], "timezone")
    year = 2026
    places = place_index(guide)
    nav = "".join(f'<a href="#{a}">{t}</a>' for a, t in
                  (("events", "日別イベント"), ("day", "1日の流れ"), ("map", "会場マップ"), ("move", "移動"), ("tips", "Tips"), ("links", "リンク")))
    body = [
        "<h1>AWS re:Invent 2026 現地ガイド</h1>",
        f'<p class="lead">ラスベガスで2026-11-30〜12-04に開催（受付は11/29から）。時刻はすべて現地時間（PST、UTC−8）。最終更新は{h(built_on)}。</p>',
        f"<nav>{nav}</nav>",
        '<div class="note">公式発表前の項目は「未確認」と書いています。'
        '過去年の情報には年を付けました。2026年は変わることがあるので、最終確認は公式ページと公式アプリで行ってください。'
        '<br>地名は色付きのラベルにしています。<span class="pl pl-v">会場</span>は橙、<span class="pl pl-st">モノレール駅</span>は青、'
        '<span class="pl">空港やほかの場所</span>は灰色で、押すとGoogleマップが開きます。</div>',
        '<h2 id="events">日別イベント</h2>',
        f'<p class="mut">確認日は{h(events["checked_on"])}。セッション以外の全体イベントです。</p>',
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
                f'<td>{h(EVENT_CATEGORIES[entry["category"]])}</td><td>{rich(entry["venue"] or "未確認", places)}</td>'
                f'<td>{h(EVENT_REGISTRATION[entry["registration"]])}</td><td>{rich(entry.get("public_note_ja") or "—", places)}</td></tr>'
            )
        body.append("</table></div>")
    if guide.get("day_flow"):
        body.append('<h2 id="day">1日の流れ（例）</h2><div class="scroll"><table><tr><th>時刻</th><th>内容</th><th>出典</th></tr>')
        for step in guide["day_flow"]:
            body.append(f'<tr><td class="tm">{h(step["time"])}</td><td>{rich(step["what_ja"], places)}</td>'
                        f'<td>{year_badge(step.get("year"), year)} {link(step["source"], "出典")}</td></tr>')
        body.append("</table></div>")
    body.append('<h2 id="map">会場マップ</h2>')
    body.append('<p class="mut">緯度経度から描いた縮尺付きの図です。点線は歩ける区間で、徒歩の分数を添えています。'
                '離れたMGM Grandへの時間は右下の表にまとめました。会場名と駅名（■）を押すとGoogleマップが開きます。'
                '時間は直線距離の1.3倍を分速75mで割った推定です。ホテルの入口から会場の部屋までの移動（5〜15分）は含みません。'
                'シャトル乗り場は2026年の場所が未公表のため、図にはまだ入れていません。</p>')
    body.append(f'<div class="mapwrap">{venue_map(guide)}</div>')
    line = guide.get("monorail")
    if line:
        body.append(f'<p class="mut">モノレール: 駅間1〜4分、全線約15分、{line["headway_min"]}〜{line["headway_max"]}分間隔。'
                    f'{year_badge(line.get("year"), year)} <span class="src">{link(line["source"], "出典")}</span></p>')
    example = guide.get("shuttle_example")
    if example:
        body.append(f'<p class="mut">シャトル: 2026年の路線・所要時間は未公表（「秋に公開予定」）。参考に、{rich(example["note_ja"], places)} '
                    f'{year_badge(example.get("year"), year)} <span class="src">{link(example["source"], "出典")}</span></p>')
    body.append('<details class="more"><summary>全15区間の距離と時間を表で見る</summary>'
                '<p class="mut">モノレールは「最寄り駅までの徒歩＋公式の駅間所要時間＋駅から会場までの徒歩」で、幅は電車待ち（0〜最大の運行間隔）です。</p>')
    body.append(distance_table(guide))
    body.append('</details>')
    if guide.get("venues"):
        body.append('<div class="scroll"><table><tr><th>会場</th><th>主な用途</th><th>年</th></tr>')
        for venue in guide["venues"]:
            body.append(f'<tr><td>{rich(venue["name"], places)}<br><span class="src">{link(venue["source"], "出典")}</span></td>'
                        f'<td>{rich(venue["role_ja"], places)}</td><td>{year_badge(venue.get("year"), year)}</td></tr>')
        body.append("</table></div>")
    body.append('<h2 id="move">移動</h2><div class="cards">')
    for item in guide.get("transport", []):
        body.append(f'<div class="c"><h4>{rich(item["title_ja"], places)} {year_badge(item.get("year"), year)}</h4>'
                    f'<p>{rich(item["body_ja"], places)}</p><div class="src">{link(item["source"], "出典")}</div></div>')
    body.append("</div>")
    names = {v["id"]: v["name"] for v in guide.get("venues", [])}
    if guide.get("walk_times"):
        body.append('<h3>会場間の所要時間（目安）</h3><div class="scroll"><table><tr><th>区間</th><th>手段</th><th>目安</th><th>メモ</th><th>年</th></tr>')
        for walk in guide["walk_times"]:
            minutes = f'{walk["minutes"]}分' if walk.get("minutes") is not None else "未確認"
            mode = {"walk": "徒歩", "shuttle": "シャトル", "monorail": "モノレール"}.get(walk.get("mode"), walk.get("mode") or "—")
            body.append(f'<tr><td>{rich(names.get(walk["from"], walk["from"]), places)} ↔ {rich(names.get(walk["to"], walk["to"]), places)}</td>'
                        f'<td>{h(mode)}</td><td class="tm">{h(minutes)}</td><td>{rich(walk.get("note_ja") or "—", places)} '
                        f'<span class="src">{link(walk["source"], "出典")}</span></td><td>{year_badge(walk.get("year"), year)}</td></tr>')
        body.append("</table></div>")
    body.append('<h2 id="tips">過去の参加者のTips</h2>'
                '<p class="mut">過去の参加レポートで繰り返し挙がっている点を要約しました。出典を開くと元の記事を読めます。</p>')
    tips = guide.get("tips", [])
    for category in TIP_CATEGORIES:
        selected = [t for t in tips if t["category"] == category]
        if not selected:
            continue
        body.append(f'<h3>{h(category)}</h3><div class="cards">')
        for tip in selected:
            sources = " ".join(link(url, f"出典{i + 1}") for i, url in enumerate(tip["sources"]))
            if tip.get("origin") == "handover":
                sources = '<span class="badge b-ev">社内の引き継ぎ</span> ' + sources
            body.append(f'<div class="c"><h4>{rich(tip["title_ja"], places)}</h4><p>{rich(tip["body_ja"], places)}</p>'
                        f'<div class="src">{year_badge(tip.get("year"), year)} {sources}</div></div>')
        body.append("</div>")
    body.append('<h2 id="links">リンク</h2><ul>')
    for item in guide.get("links", []):
        body.append(f'<li>{link(item["url"], item["title"])}: {rich(item["why_ja"], places)}</li>')
    for source in events["sources"]:
        body.append(f'<li>{link(source["url"], source["label_ja"])}</li>')
    body.append("</ul>")
    body.append(f'<footer>ガイド情報の確認日は{h(guide["checked_on"])}、イベント情報の確認日は{h(events["checked_on"])}。'
                "公式ページの説明文は転載せず、要点を自分の言葉でまとめています。</footer>")
    meta = '<meta name="summary" content="re:Invent 2026の日別イベント・会場・移動・過去参加者のTips">\n'
    return page("re:Invent 2026 現地ガイド", meta, "\n".join(body))


def build_personal(catalog: dict[str, Any], events: dict[str, Any], schedule: dict[str, Any],
                   shared_url: str | None, created: str, built_on: str, guide: dict[str, Any] | None = None) -> str:
    places = place_index(guide)
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
            status += f' <span class="badge b-rev">見直し中</span><br><span class="mut">{rich(item["review_ja"], places)}</span>'
        title = (f'<span class="id">{h(session["id"])}</span> {link(session["url"], session.get("title_ja") or session["title"])}'
                 f'<br><span class="en">{h(session["title"])} · {h(session["format"])} {h(session["level"])}</span>')
        rows.append((start, f'<tr><td class="tm">{h(clock(start, end, zone))}</td><td>{title}</td>'
                            f'<td>{rich(session["venue"] or "未確認", places)}</td><td>{status}</td></tr>'))
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
                            f'<br><span class="mut">{rich(note, places)}</span></td><td>{rich(entry["venue"] or "未確認", places)}</td>'
                            f'<td>{h(EVENT_INTENT[entry["intent"]])}</td></tr>'))
    reviewing = [(item, s) for item, s in active if is_text(item.get("review_ja"))]
    shared = link(shared_url, "共有版の現地ガイド（会場マップ・移動・Tips・全体イベント）") if shared_url else "共有版: 未公開"
    body = [
        "<h1>re:Invent 2026 自分の予定</h1>",
        f'<p class="lead">現地時間（PST）。最終更新は{h(built_on)}。予約{len(active)}件、見直し中{len(reviewing)}件。</p>',
        f'<div class="note">{shared}</div>',
    ]
    if report.errors or report.warnings:
        body.append('<div class="note"><b>予定チェック</b><ul>' + "".join(f"<li>{h(m)}</li>" for m in report.errors + report.warnings) + "</ul></div>")
    if reviewing:
        body.append("<h2>見直し中の予約</h2><ul>")
        for item, s in reviewing:
            body.append(f'<li><span class="id">{h(s["id"])}</span> {h(s.get("title_ja") or s["title"])}: {rich(item["review_ja"], places)}</li>')
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
                        f' {h(EVENT_INTENT[e["intent"]])}: {rich(e["note_ja"] or "", places)}</li>')
        body.append("</ul>")
    body.append(f'<footer>カタログ確認日は{h(catalog["checked_on"])}、イベント確認日は{h(events["checked_on"])}。'
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
    guide = merge_guides(read_json(ROOT / "data" / "guide.json"),
                         read_json(PRIVATE_GUIDE) if PRIVATE_GUIDE.exists() else None)
    built_on = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    shared_path = OUT_DIR / "shared" / "index.html"
    personal_path = OUT_DIR / "personal.html"
    shared_path.parent.mkdir(parents=True, exist_ok=True)
    shared_path.write_text(build_shared(events, guide, built_on), encoding="utf-8")
    created = config.get("personal_created") or datetime.now().astimezone().isoformat(timespec="seconds")
    personal_path.write_text(build_personal(catalog, events, schedule, config.get("shared_url"), created, built_on, guide),
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
