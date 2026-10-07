# Working rules

- `AGENTS.local.md` があればローカル手順（全件カタログ等）はそちら。
- ドキュメントは日本語。私的な旅程は `private/`。
- セッション追加・変更は公式カタログ準拠。`id` / `year` / `url` / `checked_on` / 公式英題 `title` を保持。`title_ja` は任意の短い補助ラベル。無い項目は null（推測しない）。
- abstract・字幕・機械要約は `local-data/` のみ。`data/catalog.json` は選抜メタ。`docs/catalog.md` と `sessions/*/README.md` は `render` 生成。
- `notes/` と `planning/*.md` は手書き。カタログ更新で上書きしない。notes 推敲は `docs/qwen-notes.md`。
- 時刻は America/Los_Angeles（オフセット付き）。2025 の日程を 2026 にコピーしない。`why_ja` は短く。
- `python3 scripts/reinvent.py validate` と `python3 -m unittest discover -s tests -v`。`reserved` は実予約後のみ。
- `data/events.json` は公式・主催者の出典のみ。未確認は null。説明文を転載しない。
