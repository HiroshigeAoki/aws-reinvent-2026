# Task A6 completion

- **task:** A6（notes 用 Qwen 手順）
- **date:** 2026-09-30

## Changed files

| Path | Action |
| --- | --- |
| `docs/qwen-notes.md` | 新規。notes 推敲のみ（`qwen-oneshot rewrite-ja`） |
| `AGENTS.md` | notes 行に `docs/qwen-notes.md` への一行リンクを追加 |
| `docs/plans/_a6-completion.md` | 本完了報告（新規） |

## Brief what changed

`notes/*.md` を手元 Qwen で推敲する短い手順を分離して置いた。字幕・機械要約の手順は書いていない（Phase B / `docs/local-data.md` への対比一文のみ）。

## Evidence

### `docs/qwen-notes.md` は notes のみ

- コマンドは `qwen-oneshot rewrite-ja --file notes/<file>.md --save` のみ
- 入力・出力は `notes/` 同ファイル推敲
- `summarize_local` / `fetch_transcript` / `qwen-oneshot summarize` の手順なし
- 末尾一文で「字幕 → local-data/summaries は Phase B」と本手順から切り離している

### AGENTS リンク

```text
AGENTS.md:9: ... For notes polishing with Qwen, see docs/qwen-notes.md.
```

### D-6

`docs/qwen-notes.md` が存在し、transcript 要約手順と混在していない → Pass 相当。

## Open items

- A7（git init / 可視性）・A8（CI）は未着手
- Phase B（transcript 取得・要約）は未実装
- 本タスクでは git init / commit なし
