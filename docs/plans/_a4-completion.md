# Task A4 completion

- **task:** A4（README ひっそり化 + policy / AGENTS 整合）
- **date:** 2026-09-30

## Changed files

| Path | Action |
| --- | --- |
| `README.md` | 短縮。比較・宣伝・長い AI 例・予定ステータス説明を削除。公式リンク表は維持。AI は AGENTS.md への一行ポインタのみ |
| `AGENTS.md` | `title` 必須・`title_ja` 任意、abstract/transcript/機械要約の非コミット、`local-data/` gitignore を明記 |
| `docs/content-policy.md` | 掲載可（ID・英題・任意 title_ja・why_ja・notes・URL・checked_on）と非掲載（abstract 全文・transcript・機械要約）を整合。local-data / private でも ToS は免除されない旨を維持 |
| `references/sources.md` | 英語 `title` は公式カタログで目視確認してから書く（捏造しない）を一行追加 |
| `docs/plans/_a4-completion.md` | 本完了報告（新規） |

## Brief what changed

README を非公式一文・日程・公式表・最小 CLI・短い編集表・ライセンスリンクに絞った。AGENTS / content-policy / sources を `title` 必須スキーマと「成果物は local-data のみ」方針に揃えた。Phase B の取得・要約実装はしていない。

## Evidence

### `wc -l README.md`

| | lines |
| --- | ---: |
| before | 73 |
| after | 51 |

### README に禁止語なし

```text
grep -nE 'Summit|フルアーカイブ|比較|RAG|アーカイブ|他リポジトリ|他のリポジトリ' README.md
→ (no matches)
```

### AGENTS / policy 整合（抜粋）

- AGENTS: `title` must / `title_ja` optional / do not commit abstract·transcript·machine summaries / `local-data/` gitignored
- content-policy: 掲載可に英題と任意 title_ja；リポジトリに置かないに abstract 全文・transcript・機械要約；`local-data/` gitignore
- sources: 英題は公式カタログ目視確認、捏造しない

## Open items

- A5（`docs/local-data.md` + パス定数）以降は未着手
- A7 の public/private・`git init` はユーザー確認待ち
- 本タスクでは git init / commit なし
