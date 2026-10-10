#!/usr/bin/env python3
"""Unattended daily refresh: headless Claude updates event data, then this script tests, commits and publishes."""

from __future__ import annotations

from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "local-data" / "refresh"
PROMPT = ROOT / "docs" / "daily-refresh.md"
# Claude may edit only these; render regenerates RENDERED from them.
EDITABLE = ("data/events.json", "data/guide.json")
RENDERED = ("docs/events.md", "docs/catalog.md", "sessions/")
ALLOWED_TOOLS = [
    "Read", "Glob", "Grep", "WebFetch",
    "Edit(data/events.json)", "Edit(data/guide.json)", "Write(local-data/refresh/report.json)",
    "Bash(python3 scripts/reinvent.py watch-events)", "Bash(python3 scripts/reinvent.py validate)",
    "mcp__awsevents__AWSEventsPublicApi-Mcp-prod___ListEvents",
    "mcp__awsevents__AWSEventsPublicApi-Mcp-prod___ListSessions",
    "mcp__awsevents__AWSEventsPublicApi-Mcp-prod___GetSession",
    "mcp__awsevents__AWSEventsPublicApi-Mcp-prod___GetSchedule",
]
CLAUDE_TIMEOUT = 30 * 60


def classify_changes(paths: list[str]) -> tuple[list[str], list[str]]:
    """Split changed paths into ones the refresh may commit and ones that must block it."""
    stage = [p for p in paths if p in EDITABLE or p.startswith(RENDERED)]
    return stage, [p for p in paths if p not in stage]


def run(*args: str, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)


def changed_files() -> list[str]:
    result = run("git", "status", "--porcelain", "--untracked-files=no")
    return [line[3:] for line in result.stdout.splitlines() if line.strip()]


def instructions() -> str:
    return PROMPT.read_text(encoding="utf-8").split("## 指示", 1)[1].strip()


def refresh() -> dict:
    status: dict = {"outcome": "error", "summary_ja": "", "changes_ja": [], "api_ja": None, "commit": None}
    if changed_files():
        status.update(outcome="skipped", summary_ja="未commitの変更があるため、今日の自動調査は止めました。")
        return status
    report_path = STATE / "report.json"
    report_path.unlink(missing_ok=True)
    claude = run("claude", "-p", instructions(), "--permission-mode", "dontAsk", "--allowedTools", *ALLOWED_TOOLS,
                 "--model", "sonnet", "--no-session-persistence", "--output-format", "json", timeout=CLAUDE_TIMEOUT)
    (STATE / "claude-last.json").write_text(claude.stdout + claude.stderr, encoding="utf-8")
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    status.update(summary_ja=report.get("summary_ja") or "", changes_ja=report.get("changes_ja") or [],
                  api_ja=report.get("api_ja"))
    if claude.returncode != 0 or not report:
        status["summary_ja"] = f"Claudeの実行に失敗しました（終了コード{claude.returncode}）。claude-last.jsonを確認してください。"
        return status
    if not changed_files():
        status["outcome"] = "unchanged"
        return status
    if run("python3", "scripts/reinvent.py", "render").returncode != 0:
        status["summary_ja"] = "renderに失敗しました。dataの変更はcommitしていません。"
        return status
    stage, foreign = classify_changes(changed_files())
    if foreign:
        status["summary_ja"] = f"許可外のファイルが変わったためcommitしていません: {', '.join(foreign)}"
        return status
    for check in (("python3", "scripts/reinvent.py", "validate"), ("python3", "-m", "unittest", "discover", "-s", "tests")):
        result = run(*check)
        if result.returncode != 0:
            status["summary_ja"] = f"{' '.join(check[1:])} が失敗したためcommitしていません。"
            (STATE / "check-failure.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
            return status
    run("git", "add", "--", *stage)
    message = "Refresh event data from official pages.\n\n" + "\n".join(f"- {c}" for c in status["changes_ja"]) \
        + "\n\nCo-Authored-By: Claude Sonnet <noreply@anthropic.com>\n"
    if run("git", "commit", "-q", "-m", message).returncode != 0:
        status["summary_ja"] = "git commitに失敗しました。"
        return status
    status.update(outcome="changed", commit=run("git", "rev-parse", "--short", "HEAD").stdout.strip())
    return status


def main() -> int:
    os.environ["PATH"] = f"{Path.home() / '.local' / 'bin'}:{os.environ.get('PATH', '/usr/bin:/bin')}"
    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE / ".lock", "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("another refresh is running", file=sys.stderr)
            return 1
        try:
            status = refresh()
        except Exception as exc:  # Surface any crash on the personal page instead of failing silently.
            status = {"outcome": "error", "summary_ja": f"自動調査が途中で止まりました: {exc}"}
        status["ran_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        (STATE / "latest.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        command = "publish" if status["outcome"] == "changed" else "publish-personal"
        published = run("python3", "scripts/site.py", command)
        print(f"{status['ran_at']} {status['outcome']} {status.get('summary_ja', '')}")
        print(published.stdout + published.stderr)
        return 0 if status["outcome"] in {"changed", "unchanged"} and published.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
