# 出典と更新記録

確認日：2026-09-29（JST）。ページ内容は変更されるため、利用前に公式情報を再確認します。

## 2026年

| 出典 | 確認対象 |
|---|---|
| [公式トップ](https://aws.amazon.com/events/reinvent/) | 開催年・期間・場所 |
| [公式カタログ](https://registration.awsevents.com/flow/awsevents/reinvent2026/eventcatalog/page/eventcatalog) | 選定セッションのID、形式、レベル、日時、会場 |
| [学習形式](https://aws.amazon.com/events/reinvent/sessions/how-youll-learn/) | 形式とレベルの定義 |
| [Agenda](https://aws.amazon.com/events/reinvent/agenda/) | 開催日の全体構成 |
| [FAQ](https://aws.amazon.com/events/reinvent/faqs/) | favoriteと予約の違い、予約・当日の条件 |
| [会場](https://registration.awsevents.com/flow/awsevents/reinvent2026/venueshotel/page/venuehotel) | 2026年の会場と移動案内 |
| [分野別リスト](https://aws.amazon.com/events/reinvent/sessions/curated-agendas/) | 職種や分野別の公式導線 |

各セッションの `url` は公式カタログでIDを検索するURLです。英語 `title` は公式カタログで目視確認してから書き、捏造しない。`title_ja`（任意）と選定理由は独自に記載しています。`-R` や `-R1` は別の開催回として保持します。

## 2025年

出典リンクと学習案は [2025.md](2025.md) に記載しています。2025年の資料は予習用であり、2026年の仕様やスケジュールを保証しません。

## 更新手順

1. 公式ページで変更内容を確認する。
2. data/catalog.json の対象項目と `checked_on` を更新する。削除や別開催回の統合は自分のメモとの対応を確認して行う。
3. `validate` → `render` → 差分確認の順で実行する。
4. planning/ と notes/ は自分で必要な更新を行う。

CLI自体はネットワークにアクセスしません。変更検出はGitの差分で確認します。
