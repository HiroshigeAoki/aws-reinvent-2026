# Task A5 completion

- **task:** A5（local-data レイアウトの「空の約束」）
- **date:** 2026-09-30

## Changed files

| Path | Action |
| --- | --- |
| `docs/local-data.md` | 新規。パス規約と「コミットしない」のみ |
| `scripts/local_paths.py` | 新規。local-data ルート / transcript / summary / streams のパス定数・ヘルパー |
| `tests/test_local_paths.py` | 新規。パス形状の軽い unittest |
| `.gitignore` | 変更なし（`local-data/` 既存） |
| `docs/plans/_a5-completion.md` | 本完了報告（新規） |

**未作成（意図的）:** `local-data/README.md`、fetch/summarize、A6 以降

## Brief what changed

手元成果物の置き場を docs と `local_paths` で約束しただけ。ネットワーク・取得・要約ロジックは入れていない。gitignore は既に `local-data/` があるため触っていない。

## Evidence

### Key symbols (`scripts/local_paths.py`)

- `ROOT`, `LOCAL_DATA`
- `local_data_root()`, `transcript_path(year, id)`, `summary_path(year, id)`, `streams_path()`

### Path shapes

```text
LOCAL_DATA= .../local-data
transcript= .../local-data/transcripts/2026/DVT206.md
summary=    .../local-data/summaries/2026/DVT206.json
streams=    .../local-data/streams.json
```

### `grep local-data .gitignore`

```text
7:local-data/
```

### unittest

```text
python3 -m unittest tests.test_local_paths -v
→ 3 tests OK
```

### `local-data/README.md`

存在しない（確認済み）。

## Open items

- A6（`docs/qwen-notes.md`）以降は未着手
- Phase B（fetch / summarize）は未実装（パス定数のみ）
- 本タスクでは git init / commit なし
