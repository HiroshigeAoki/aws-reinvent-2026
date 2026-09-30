# local-data

gitignore 配下の手元データ。

```
local-data/catalog-full.sqlite
local-data/catalog-full.prev.sqlite
local-data/raw/snapshots/<UTC>/
local-data/raw/current -> snapshots/...
local-data/transcripts/{year}/{id}.md
local-data/summaries/{year}/{id}.json
local-data/streams.json
```

定数: `scripts/local_paths.py`（`catalog_full_path()`）。

## 全件カタログ

```bash
python3 private/catalog-tools/refresh_catalog.py
python3 private/catalog-tools/query_catalog.py \
  --tag-kind area_of_interest --tag 'Agentic' --limit 20
```

テーブル: `sessions` / `tags` / `speakers` / `sessions_fts` / `meta`。ツールは `private/catalog-tools/`。abstract はここだけ。

## 字幕・要約（Phase B）

```json
{
  "abstract": "...",
  "keywords": [],
  "source_transcript": "...",
  "created_on": "YYYY-MM-DD"
}
```
