# 公開コンテンツの方針

確認日：2026-09-30。これはこのリポジトリの運用方針であり、個別の法的判断や権利者の許可を保証するものではありません。

## 掲載できるもの

- 独自実装したコードと説明文。
- 選定したセッションの ID、公式英語タイトル（`title`）、任意の短い補助ラベル（`title_ja`）、形式、レベル、必要最小限の日時・会場と公式 URL。
- 独自の選定理由（`why_ja`）、質問、実験結果、参加後の学び（自分の文章）。
- 情報を確認した日付（`checked_on`）。未確認の項目は空欄または null。

## リポジトリに置かないもの

- 公式 abstract（カタログ説明文）の全文。
- 字幕・transcript 本文、機械生成の要約本文。
- 動画、音声、スライド、PDF、画像、公式ロゴ。
- ログインが必要な資料や登録情報、社内情報、他の参加者の個人情報。
- 会社や第三者のリポジトリにあるコード・文章の、許諾が確認できない複製。

公開設定や出典表示だけでは、第三者コンテンツを再配布する許可にはなりません。`private/` に置いても ToS・著作の制限は解消されません。

## データの取り扱い

公式ページを参照して少数の基本情報を選定・更新します。通常の公開ページの閲覧と、一括収集・再配布の権限は区別します。AWS Site Terms は一般の利用許諾からロボット等によるデータ抽出を除外しているため、この実装には自動スクレイパーや認証情報の取得処理を含めていません。

`local-data/` は gitignore 対象です。transcript・機械要約などの成果物はここにのみ置き、コミットしません。非公開に保存するだけで取得・利用の制限が解消されるわけではありません。

## 商標・ライセンス

AWS との提携や公式性を表示しません。名称は対象を説明するためのプレーンテキストとして使い、ロゴは使いません。MIT ライセンスの対象は独自作成部分で、第三者コンテンツ・商標を再許諾しません。

## 参考

- [AWS Site Terms](https://aws.amazon.com/terms/) — COPYRIGHT / LICENSE AND SITE ACCESS
- [AWS Trademark Guidelines](https://aws.amazon.com/trademark-guidelines/) — 特に 13、15 項
- [AWS Event Terms](https://aws.amazon.com/events/terms/)
- [GitHub: Licensing a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
