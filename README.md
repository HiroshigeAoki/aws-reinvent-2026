# AWS re:Invent 2026 — 個人の参加準備・学習ノート

非公式の個人用リポジトリです。AWS の運営・承認を示すものではありません。

**開催：2026年11月30日〜12月4日 / Las Vegas**  

## 使い始める

1. [参加候補一覧](docs/catalog.md)
2. [2025年の予習](references/2025.md)
3. [優先順位](planning/shortlist.md) / [日別計画](planning/schedule.md)
4. [メモのテンプレート](notes/TEMPLATE.md)

## 公式情報

| 内容 | リンク |
|---|---|
| 開催概要 | [公式サイト](https://aws.amazon.com/events/reinvent/) |
| セッション検索 | [公式カタログ](https://registration.awsevents.com/flow/awsevents/reinvent2026/eventcatalog/page/eventcatalog) |
| 日程 | [Agenda](https://aws.amazon.com/events/reinvent/agenda/) |
| 形式・難易度 | [How you'll learn](https://aws.amazon.com/events/reinvent/sessions/how-youll-learn/) |
| 分野別案内 | [Curated agendas](https://aws.amazon.com/events/reinvent/sessions/curated-agendas/) |
| FAQ | [FAQ](https://aws.amazon.com/events/reinvent/faqs/) |

## CLI

```bash
python3 scripts/reinvent.py validate
python3 scripts/reinvent.py search AI
python3 scripts/reinvent.py render
python3 scripts/reinvent.py check-schedule
```

## 編集する場所

| パス | 用途 |
|---|---|
| `data/catalog.json` | 選定セッションの入力（手編集） |
| `docs/catalog.md` / `sessions/` | `render` が生成 |
| `planning/` | 優先順位・予定（手編集） |
| `notes/` | 質問・学び（手編集） |
| `private/` | 非公開メモ（Git 対象外） |

AI の作業ルールは [AGENTS.md](AGENTS.md) を参照。

## ライセンス

独自作成部分は [MIT License](LICENSE)。公開方針は [docs/content-policy.md](docs/content-policy.md)、出典は [references/sources.md](references/sources.md)。
