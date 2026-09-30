# AWS re:Invent 2026 notes — 詳細実装計画

> **別セッション実行時:** 先に [`2026-09-30-handoff.md`](2026-09-30-handoff.md) と [`2026-09-30-acceptance-rubric.md`](2026-09-30-acceptance-rubric.md) を読むこと。

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 個人用の参加準備リポジトリを、英語タイトル中心の薄い公開カタログ＋手元（local）の字幕/要約パイプライン前提で整える。README は目立つ説明を避け、静かに運用できる状態にする。

**Architecture:**
- **Git に載せる:** 自分のコード、手選びメタ（`data/catalog.json`）、planning / notes（自分の文章）、生成 Markdown、取得・要約の**仕組み**（スクリプトと短い手順）。
- **Git に載せない:** `local-data/`（transcript・機械要約・streams キャッシュ）、`.auth/`、`.env`、動画ファイル、`private/`。
- **表示:** `title`（公式英語・必須）が主、`title_ja`（任意・補助）。
- **README:** 他リポジトリとの比較や売り込みは書かない。必要最小の使い方だけ。

**Tech Stack:** Python 3.11 stdlib（現行 CLI）、unittest、将来の取得系は必要になった時点で依存追加。要約は手元 Qwen（`qwen-oneshot` / 後続スクリプト）。自動一括クロールはしない。

---

## 0. public / private のサイト検討（結論）

法務の最終判断ではない。AWS Site Terms（COPYRIGHT / LICENSE AND SITE ACCESS）は、サイトコンテンツの著作権を AWS 側に置き、一般の利用許諾から **data mining / robots 等による抽出** を除外している。Event 資料・カタログ文面・字幕は「リンクして自分で見る」分と「複製して GitHub で配る」分ではリスクが違う。

### 比較

| 観点 | public | private |
|---|---|---|
| 手選び ID・公式英題・公式 URL・自分の why/notes | 問題になりにくい | 同様に問題になりにくい |
| 公式 abstract / 字幕本文 / それを丸ごと載せた summaries を **リポジトリにコミット** | 避ける | それでも ToS・著作の論点は残る（非公開＝許可ではない）。現行 `content-policy` も「private に置けば解消」とは書いていない |
| **取得・要約スクリプトだけ**公開し、成果物は `local-data/` | データ再配布よりはマシ。ただし「抽出ツールの公開」自体が Site Terms の robots/extraction 条項と緊張しうる | 同じツールでも発見されにくく、社内・個人ツールとしての説明がしやすい |
| 発見性・誤解（公式アーカイブに見える） | README が目立つと不利 → **ひっそり README 必須** | 低い |
| 参照した Summit アーカイブ | **private** | 同型の全文アーカイブを public で真似る根拠にはならない |

### フェーズ別の推奨

**いま（開催前・取得スクリプト未実装、薄い catalog のみ）**  
→ **public にしてよい**（次の条件をすべて満たす場合）。

条件:
1. コミットするのは最小メタ＋自分の文章＋自作コードのみ（abstract / transcript / 機械要約の中身はコミットしない）。
2. README はひっそり（非公式一文、使い方、リンク。比較・大風呂敷・「アーカイブ」アピールなし）。
3. `content-policy` で「生成物は local」「一括収集しない」を維持。
4. CI で `local-data/` が誤って追跡されないことを確認できる（gitignore）。

**あと（オンデマンド後・ログイン付き字幕取得を本実装した直後）**  
→ **既定は private のまま様子を見る**のを推奨。  
理由: 認証付きポータル自動化は Site Terms・アカウントリスクの面で露出コストが上がる。安定し、かつ「catalog にある ID だけ」「失敗したら即停止」「成果物は local-data のみ」に狭い実装だと分かってから、public に戻すか判断する。

**迷ったら**  
→ **最初から private**。後から public にするのは容易。逆は履歴に残る。

### この計画でのリポジトリ可視性

| 段階 | 可視性 |
|---|---|
| Phase A（本計画の Task 1–8） | **public 可**（上記条件）。ユーザーが不安なら private で開始してよい |
| Phase B（Task 9 本実装後） | **いったん private 推奨**。narrow fetch が固まってから public 再検討 |

実装時に GitHub を作る場合は、ユーザーに「public / private」を再確認してから `gh repo create` する。

---

## 1. 固定する設計

### 1.1 データ配置

```
data/catalog.json          # 公開してよい最小メタ（手選び）
docs/catalog.md            # render 生成
sessions/{year}/{id}/README.md
planning/shortlist.md      # 優先と理由（手書き）
planning/schedule.json|md
notes/                     # 自分の文章（public してよい範囲だけ）
scripts/reinvent.py        # validate / search / render / check-schedule
scripts/local_*.py         # Phase B: 取得・要約（成果物は local-data のみ書く）
local-data/                # gitignore
  transcripts/{year}/{id}.md
  summaries/{year}/{id}.json
  streams.json             # 任意
.auth/                     # gitignore
private/                   # gitignore（旅程など）
```

`metadata.json` という名前は **必須にしない**。公開メタの単一入力は `data/catalog.json` のまま。AI / render はこれを読む。local 側に別インデックスが必要なら `local-data/index.json` をスクリプトが生成（コミットしない）。

### 1.2 catalog スキーマ（セッション）

| フィールド | 必須 | 備考 |
|---|---|---|
| `id`, `year` | 必須 | |
| `title` | 必須 | 公式英語タイトル |
| `title_ja` | 任意 | 短い補助ラベル |
| `format`, `level`, `venue` | 現行どおり | venue / level は null 可（現行ルール維持） |
| `starts_at`, `ends_at` | 現行どおり | オフセット付き ISO または null |
| `url`, `checked_on` | 必須 | |
| `topics` | 必須 | 文字列配列 |
| `why_ja` | 必須 | 選定理由（自分の文） |
| `sponsor` | 任意 | 現行どおり追加フィールド可 |

**載せない:** 公式 abstract 全文、スピーカー詳細の丸写し、字幕、機械要約。

### 1.3 shortlist

カタログ＝候補プール。shortlist＝その中の優先と理由。schedule＝時間に載せた予定。  
ファイル名は `planning/shortlist.md` のまま。冒頭に役割を短く書く（README で騒がない）。

### 1.4 README トーン（ひっそり）

書く:
- 非公式・個人用である一文
- 開催日と「公式を確認せよ」
- 最低限のコマンド
- 編集場所の表（短く）
- ライセンスへのリンク（末尾で十分）

書かない:
- 他リポジトリとの比較
- 「RAG 向け」「フルアーカイブ」「Summit 互換」など目立つ宣伝
- 長い AI プロンプト例の羅列（AGENTS に寄せる。README は 0〜数行まで）
- transcript 機能の大々的な紹介（local 手順は `docs/` の短い頁か AGENTS に閉じる）

### 1.5 要約の二系統

| 系統 | 入力 | 出力 | Git |
|---|---|---|---|
| notes 整形 | `notes/*.md`（自分の文） | 同ファイルの推敲 | してよい |
| 動画要約（Phase B） | `local-data/transcripts/...` | `local-data/summaries/...` | **しない** |
| 公開用の学び | 上の要約を読んだうえでの自分の言葉 | `notes/` の箇条書き | してよい |

---

## 2. Phase A — いま実装する Task

### Task A1: `title` 必須化（テスト先行）

**Files:**
- Modify: `tests/test_reinvent.py`
- Modify: `scripts/reinvent.py`

**Steps:**
1. フィクスチャを `title` 必須・`title_ja` 任意に変更した失敗テストを追加（欠落、render 見出し、補助行）。
2. `python3 -m unittest discover -s tests -v` で FAIL を確認。
3. `REQUIRED_SESSION_FIELDS` を更新。validate / render を実装。
4. テスト PASS。

**Done when:** タイトル欠落で validate が落ち、見出しが英語になる。

---

### Task A2: catalog 8 件の公式英題（手動確認）

**Files:**
- Modify: `data/catalog.json`
- Regenerated: `docs/catalog.md`, `sessions/2026/*/README.md`

**Steps:**
1. 公式カタログで各 ID の英題を目視確認（自動一括取得しない）。未確認は捏造しない。
2. 既存の日本語短ラベルは `title_ja` に残し、`title` に英題を入れる。
3. `checked_on` を確認日に更新。
4. `validate` → `render` → 目視。

対象: `DVT206`, `DVT212-S`, `SVS303-R`, `GHJ301-S`, `GHJ212`, `API304-R`, `SEC362`, `MAM419-R`

**Done when:** 8 件すべてに確認済み `title` があるか、未確認は作業ログで明示してスキップ理由が残る（コミットメッセージまたはチャット。ファイル本体に「解決済み」注記は書かない）。

---

### Task A3: shortlist を静かに充足

**Files:**
- Modify: `planning/shortlist.md` のみ（README には短list の長い説明を増やさない）

**Steps:**
1. 冒頭 3〜5 行で「候補プールとの違い」を書く。
2. 選定記録を 8 行にする（優先は案、`why_ja` ベース）。

**Done when:** 8 件分の行がある。

---

### Task A4: README をひっそり化＋ policy / AGENTS 整合

**Files:**
- Modify: `README.md`（短縮・比較削除・AI 節は最小化）
- Modify: `AGENTS.md`（`title` / `title_ja`、local-data ルール）
- Modify: `docs/content-policy.md`（タイトル可・abstract/transcript 本文はリポジトリに置かない・local-data は gitignore）
- Modify: `references/sources.md`（英題確認手順を一行）

**README 目標ボリューム:** 現状より短く。公式リンク表は残してよいが、説明文は削る。

**Done when:** README に他 repo 比較も「フルアーカイブ」も無い。policy と AGENTS が矛盾しない。

---

### Task A5: local-data レイアウトの「空の約束」

**Files:**
- Create: `local-data/README.md` は **作らない**（中身をコミットしない方針と矛盾しやすい）
- Create: `docs/local-data.md`（短い。パス規約と「コミットしない」だけ）
- Modify: `.gitignore`（`local-data/` が既にあることを確認。必要なら `local-data/**` を明示）
- Create: `scripts/local_paths.py` または `reinvent.py` 内の定数（Phase B が読むパス定義だけ。取得ロジックはまだ）

**レイアウト規約:**

```
local-data/transcripts/{year}/{id}.md
local-data/summaries/{year}/{id}.json   # {"abstract": "...", "keywords": [...], "source_transcript": "...", "created_on": "YYYY-MM-DD"}
local-data/streams.json                 # optional
```

**Done when:** ドキュメントとパス定数があり、誤って track されない。

---

### Task A6: notes 用 Qwen 手順（短く docs に）

**Files:**
- Create: `docs/qwen-notes.md`（notes 推敲のみ。transcript 要約は Phase B を参照）
- Modify: `AGENTS.md`（一行リンク）

```bash
qwen-oneshot rewrite-ja --file notes/<file>.md --save
```

**Done when:** notes と local transcript 要約の手順が混ざっていない。

---

### Task A7: git 初期化と GitHub 可視性

**Files:** リポジトリ全体

**Steps:**
1. ユーザー確認: **public（条件付き） / private（安全側）**。
2. `git init`（ユーザー許可後）。
3. `git status` で `local-data/`, `.env`, `.auth/` が未追跡であることを確認。
4. 初回コミットは **ユーザーが commit と言ったときだけ**。
5. remote 作成時: `gh repo create` の visibility を Step 1 に合わせる。デフォルト提案は **不安なら private**。public にするなら Section 0 の条件チェックリストをチャットで复唱。

**Done when:** git があり、秘匿パスが混ざっていない。

---

### Task A8: CI 確認

**Files:**
- Modify if needed: `.github/workflows/check.yml`

**Steps:**
1. unittest / validate / check-schedule / render+diff が git 化後に通ることを確認。
2. render 差分が出る場合は生成物をコミットしてから緑にする。

**Done when:** ローカルで workflow 相当が通る。

---

## 3. Phase B — オンデマンド後（詳細設計のみ。今は実装しない）

動画・字幕の実エンドポイントは開催後に確定する。**今はスタブと I/F だけ決め、本実装は別セッション。**

### Task B1: 発見（手動スパイク）

1. オンデマンドページまたはポータルで、対象セッションに字幕があるか確認。
2. 字幕が VTT / CaptionHub JSON / YouTube かを記録（`docs/` に長く書かず、必要なら `private/` にメモ）。
3. ログイン要否を確認。要なら「失敗即停止・再試行しない」。

### Task B2: `scripts/fetch_transcripts.py`（本実装時）

**挙動:**
- 入力: `data/catalog.json` の ID のみ（全件クロールしない）。
- 出力: `local-data/transcripts/{year}/{id}.md` のみ。
- 既存ファイルはスキップ（幂等）。
- 認証情報は `.env` / `.auth`（gitignore）。
- ネットワークエラーやログイン失敗でループしない。

**テスト:** フィクスチャ HTML/JSON を `tests/fixtures/` に最小限置き、パーサ単体をオフラインテスト（ライブ E2E は CI に載せない）。

### Task B3: `scripts/summarize_local.py`

- 入力: `local-data/transcripts/...`
- 出力: `local-data/summaries/...`
- 既定バックエンド: 手元 Qwen（環境変数で endpoint）。API キーを要する外部 SaaS をデフォルトにしない。
- 未処理のみ。幂等。

### Task B4: （任意）notes への「自分の言葉」転記支援

- 機械要約を読んで `notes/` に短く書くのは人間または AI 提案。
- 機械要約ファイル自体はコミットしない。

### Task B5: 可視性の再判断

- 認証 fetch が入ったら Section 0 どおり **private 推奨**を再確認。
- public を維持するなら: catalog 内 ID のみ・local のみ・README はひっそり、を PR 説明ではなく policy に残す。

---

## 4. やらないこと

- README での他イベント repo との比較や宣伝
- 公式 abstract 全文の catalog 化・コミット
- transcript / 機械要約の GitHub 掲載
- 開催前の配信ポータル本実装・硬コード
- 音声 STT
- 予約の自動同期
- この Cursor ワークスペースからの Codex 委譲

---

## 5. 実装順序

| 順 | Task | 目安 |
|---|---|---|
| 1 | A1 スキーマ＋テスト | 20–30 分 |
| 2 | A2 英題手動＋render | 30–60 分 |
| 3 | A3 shortlist | 10–15 分 |
| 4 | A4 ひっそり README + policy/AGENTS | 20–30 分 |
| 5 | A5 local-data 規約 | 15 分 |
| 6 | A6 qwen notes 手順 | 10 分 |
| 7 | A7 git + 可視性確認 | 10 分 |
| 8 | A8 CI | 10 分 |
| — | B1–B5 | オンデマンド後（別計画で着手） |

---

## 6. 完了条件（Phase A）

- [ ] `title` 必須、テスト緑、一覧見出しが英語
- [ ] 8 件の英題が確認済み（または未確認が明示）
- [ ] shortlist に 8 件の選定記録と短い役割説明
- [ ] README が短く、比較・アーカイブ宣伝がない
- [ ] `docs/local-data.md` と gitignore で成果物非コミットが明確
- [ ] notes 用 Qwen 手順が transcript 要約と分離
- [ ] git 初期化済み（許可時）。秘匿パス未追跡
- [ ] public にする場合は Section 0 条件を満たす / そうでなければ private

---

## 7. 実行前にユーザーへ確認すること

1. Phase A をこの内容で実装してよいか。
2. GitHub は **public（条件付き）** か **private（安全側）** か。
3. `git init` を今するか。初回コミットも今するか（別指示でも可）。
