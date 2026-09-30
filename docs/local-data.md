# local-data（手元のみ）

字幕・機械要約・全件カタログなど、リポジトリに載せない成果物の置き場です。**コミットしない。** `.gitignore` の `local-data/` 対象です。

## パス規約

```
local-data/catalog-full.sqlite          # 全件カタログ正本（AI 照会用）
local-data/catalog-full.prev.sqlite     # 直前スナップショット（更新時）
local-data/raw/snapshots/<UTC>/         # 取得生 JSON（再取得のたびに追加）
local-data/raw/current -> snapshots/... # 最新 raw へのリンク
local-data/transcripts/{year}/{id}.md
local-data/summaries/{year}/{id}.json
local-data/streams.json                 # 任意
```

パス定数は `scripts/local_paths.py`（`catalog_full_path()` → `.sqlite`）。

## 全件カタログ（SQLite）

AI（特に Qwen）が調べるための手元 DB。**コミットしない。**  
JSON 全件ダンプより、**タグで絞ってから abstract を読む**方がトークン効率が良い。

abstract や会場・時刻は公式側で更新されうる。更新手順:

```bash
python3 private/catalog-tools/refresh_catalog.py
```

主なテーブル:

- `sessions` … id, title, format, level, starts_at/ends_at, venue, room, abstract
- `tags` … kind (`topic` / `area_of_interest` / `role` / `feature` / `service` / `industry` / `sponsor_topic`) + value
- `speakers` … name, company, job_title, roles
- `sessions_fts` … title / abstract / tag の FTS5
- `meta` … checked_on 等

取得・正規化は `private/catalog-tools/`（gitignore）。照会例:

```bash
# 薄い一覧（abstract なし）— まずこれ
python3 private/catalog-tools/query_catalog.py \
  --tag-kind area_of_interest --tag 'Agentic' --limit 20

# 候補が絞れたら abstract を付与
python3 private/catalog-tools/query_catalog.py \
  --tag-kind topic --tag 'Artificial Intelligence' --limit 10 --with-abstract
```

`abstract` は **local のみ**。Git / `data/catalog.json` / `notes/` にコピーしない。

字幕・要約の合成スモーク（`transcripts/2026/DVT206.md` 等）とは別物。

## 字幕・要約（Phase B）

`summaries` の JSON 形:

```json
{
  "abstract": "...",
  "keywords": [],
  "source_transcript": "...",
  "created_on": "YYYY-MM-DD"
}
```

取得・要約の実装は Phase B。
