# local-data（手元のみ）

字幕・機械要約など、リポジトリに載せない成果物の置き場です。**コミットしない。** `.gitignore` の `local-data/` 対象です。

## パス規約

```
local-data/transcripts/{year}/{id}.md
local-data/summaries/{year}/{id}.json
local-data/streams.json                 # 任意
```

`summaries` の JSON 形（Phase B）:

```json
{
  "abstract": "...",
  "keywords": [],
  "source_transcript": "...",
  "created_on": "YYYY-MM-DD"
}
```

パス定数は `scripts/local_paths.py`。取得・要約の実装は Phase B。
