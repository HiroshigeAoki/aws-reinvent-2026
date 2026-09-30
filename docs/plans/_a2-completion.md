# Task A2 completion

- **task:** A2（catalog 8件の公式英題・手動確認）
- **date:** 2026-09-30
- **method:** playwright-cli（Firefox）で公式 Event Catalog を **ID ごと**に検索し、一覧に表示されたセッション英題を転記。一括クロールなし。

## Changed / regenerated files

| Path | Action |
| --- | --- |
| `data/catalog.json` | 8件すべてに公式 `title` を追加。既存 `title_ja` は維持。各 session と top-level の `checked_on` を `2026-09-30` に更新 |
| `docs/catalog.md` | `python3 scripts/reinvent.py render` で再生成 |
| `sessions/2026/*/README.md`（8件） | 同上 |

## Confirmed titles

| ID | confirmed title | source note |
| --- | --- | --- |
| DVT206 | 10x or bust: How Amazon's Frontier teams ship with Kiro | `?search=DVT206` — 1 result; button text matched `(DVT206)` |
| DVT212-S | 100 Million Bugs Later: A Field Report From the Agentic Era (sponsored by CodeRabbit) | `?search=DVT212-S` — 1 result; button text matched `(DVT212-S)` |
| SVS303-R | AI-driven serverless development with Kiro | `?search=SVS303-R` — 1 result; button text matched `(SVS303-R)` |
| GHJ301-S | AWS GameDay - Agentic AI & AI Application Monitoring ft. New Relic | `?search=GHJ301-S` — 1 result; button text matched `(GHJ301-S)` |
| GHJ212 | AWS AI League: Build agents with AgentCore (Agentic Football Cup) | `?search=GHJ212` — 1 result; button text matched `(GHJ212)` |
| API304-R | API Gateway unleashed | `?search=API304-R` — 1 result; button text matched `(API304-R)` |
| SEC362 | Authentication, authorization, and audit for agentic AI on AWS | `?search=SEC362` — 1 result; button text matched `(SEC362)` |
| MAM419-R | Accelerate legacy Java modernization with custom AI-powered transformations | `?search=MAM419-R` — 1 result; button text matched `(MAM419-R)` |

Base URL pattern: `https://registration.awsevents.com/flow/awsevents/reinvent2026/eventcatalog/page/eventcatalog?search={ID}`

## Unconfirmed / skipped

なし（8件すべて公式ページで確認済み。捏造なし）。

## Spot-check

`sessions/2026/DVT206/README.md` H1:

```text
# DVT206: 10x or bust: How Amazon's Frontier teams ship with Kiro
```

続く補助行は既存 `title_ja`（`Kiroを使うチームの開発習慣`）。

## validate + render output

```text
$ python3 scripts/reinvent.py validate
OK: 8 セッションを検証しました

$ python3 scripts/reinvent.py render
OK: 9 ファイルを生成しました
```

## Open items

- A3 以降は未着手（本タスク範囲外）。
- git commit なし。
- Phase B 未着手。
- GHJ212 は会場・開始時刻がカタログ上も未設定のまま（本タスクでは英題のみ更新）。
