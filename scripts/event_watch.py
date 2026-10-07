"""Fetch normalized official event pages and compare local snapshots."""

from __future__ import annotations

from datetime import datetime, timezone
from difflib import unified_diff
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen

if __package__:
    from .local_paths import events_snapshot_root
else:
    from local_paths import events_snapshot_root


class TextParser(HTMLParser):
    BLOCK_TAGS = {"p", "div", "li", "h1", "h2", "h3", "tr", "section", "article", "header", "footer"}
    HIDDEN_TAGS = {"script", "style", "noscript"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = []

    def handle_starttag(self, tag, attrs):
        if tag in self.HIDDEN_TAGS:
            self.hidden.append(tag)
        if not self.hidden and (tag in self.BLOCK_TAGS or tag == "br"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
            return
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    parser = TextParser()
    parser.feed(html)
    parser.close()
    lines = [re.sub(r"\s+", " ", line).strip() for line in "".join(parser.parts).splitlines()]
    return "".join(line + "\n" for line in lines if line)


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; reInvent-event-watch/1.0)"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode(response.headers.get_content_charset() or "utf-8")


def watch_events(sources, *, root: Path | None = None, fetcher=fetch_html,
                 now: datetime | None = None, source: str | None = None, output=None) -> int:
    output = sys.stdout if output is None else output
    root = events_snapshot_root() if root is None else root
    selected = [entry for entry in sources if source is None or entry["id"] == source]
    if source is not None and not selected:
        print(f"ERROR: {source}: 不明な出典です", file=output)
        return 1
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = root / stamp
    counts = dict(changed=0, unchanged=0, new=0, failed=0)
    previous_dirs = sorted((path for path in root.iterdir() if path.is_dir() and re.fullmatch(r"\d{8}T\d{6}Z", path.name)
                            and path.name < stamp), reverse=True) if root.exists() else []
    for entry in selected:
        source_id = entry["id"]
        try:
            content = html_to_text(fetcher(entry["url"]))
            filename = source_id + ".txt"
            previous = next((path / filename for path in previous_dirs if (path / filename).is_file()), None)
            old = previous.read_text(encoding="utf-8") if previous else None
            target.mkdir(parents=True, exist_ok=True)
            (target / filename).write_text(content, encoding="utf-8", newline="\n")
            if old is None:
                counts["new"] += 1
                print(f"初回取得: {source_id}", file=output)
            elif old == content:
                counts["unchanged"] += 1
                print(f"変化なし: {source_id}", file=output)
            else:
                counts["changed"] += 1
                output.writelines(unified_diff(old.splitlines(keepends=True), content.splitlines(keepends=True),
                                              fromfile=str(previous), tofile=str(target / filename)))
        except Exception as exc:
            counts["failed"] += 1
            print(f"ERROR: {source_id}: {exc}", file=output)
    print("集計: " + " / ".join(f"{key}: {value}" for key, value in counts.items()), file=output)
    return int(counts["failed"] > 0)
