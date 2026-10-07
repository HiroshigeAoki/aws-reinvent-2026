# AWS re:Invent 2026 — 参加準備・学習ノート

**開催：2026年11月30日〜12月4日 / Las Vegas**

## 使い始める

1. [参加候補一覧](docs/catalog.md) / [イベント一覧](docs/events.md)
2. [2025年の予習](references/2025.md)
3. [優先順位](planning/shortlist.md) / [日別計画](planning/schedule.md)
4. [メモのテンプレート](notes/TEMPLATE.md)

## リンク

| 内容 | URL |
|---|---|
| 概要 | https://aws.amazon.com/events/reinvent/ |
| カタログ | https://registration.awsevents.com/flow/awsevents/reinvent2026/eventcatalog/page/eventcatalog |
| Agenda | https://aws.amazon.com/events/reinvent/agenda/ |
| 形式・難易度 | https://aws.amazon.com/events/reinvent/sessions/how-youll-learn/ |
| Curated agendas | https://aws.amazon.com/events/reinvent/sessions/curated-agendas/ |
| FAQ | https://aws.amazon.com/events/reinvent/faqs/ |

## CLI

```bash
python3 scripts/reinvent.py validate
python3 scripts/reinvent.py search AI
python3 scripts/reinvent.py render
python3 scripts/reinvent.py check-schedule
python3 scripts/reinvent.py watch-events
python3 scripts/reinvent.py watch-events --source agenda
python3 scripts/site.py build     # local-data/site/ に共有版・個人版 HTML
python3 scripts/site.py publish   # 上に加えて gera update と html-artifacts 更新
```

共有版（gera）は一般情報とイベントのみ。`note_ja` と参加予定は出さず、`public_note_ja` だけ載せる。予約を見直すときは `planning/schedule.json` の項目に `review_ja` を書く。公開先の ID とパスは `local-data/site.json`。

## パス

| パス | 用途 |
|---|---|
| `data/catalog.json` | 選定入力 |
| `data/events.json` | 公式イベントの日時・参加予定 |
| `data/guide.json` | 会場・移動・過去 Tips（出典と年付き） |
| `docs/events.md` | `render` 生成 |
| `docs/catalog.md` / `sessions/` | `render` 生成 |
| `planning/` | 優先・予定 |
| `notes/` | 学び |
| `private/` | 非公開（gitignore） |

[AGENTS.md](AGENTS.md) / [content-policy](docs/content-policy.md) / [出典](references/sources.md) / [MIT](LICENSE)
