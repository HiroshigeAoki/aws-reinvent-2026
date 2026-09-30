# Phase A 完了判定 — acceptance rubric

**対象:** [`2026-09-30-refinement.md`](2026-09-30-refinement.md) Task A1–A8  
**作業ルート:** `/home/aoki/dev/aws-reinvent-2026`  
**判定者:** 実装完了後の verification サブエージェント（または orchestrator）

各項目は **Pass / Fail / N/A**。Phase A 完了には **必須（Required）** をすべて Pass。

---

## A. スキーマと CLI（A1）

| ID | 必須 | 判定基準 |
|---|---|---|
| A-1 | Required | `data/catalog.json` の各セッションに `title`（非空文字列）がある |
| A-2 | Required | `title_ja` は省略可。ある場合は非空 |
| A-3 | Required | `title` 欠落セッションで `validate` が非ゼロ終了 |
| A-4 | Required | `python3 -m unittest discover -s tests -v` が全件 PASS |
| A-5 | Required | `render` 後、`sessions/*/README.md` の H1 が `{id}: {英語title}` 形式 |

---

## B. カタログ内容（A2）

| ID | 必須 | 判定基準 |
|---|---|---|
| B-1 | Required | 8 セッションすべてに `title` が入っている（未確認の捏造英題がない） |
| B-2 | Required | 旧 `title_ja` の独自ラベルが `title_ja` に残っている（該当する場合） |
| B-3 | Required | 各セッションの `checked_on` が英題確認日と整合 |
| B-4 | Required | `validate` → `render` がエラーなく完了 |

---

## C. shortlist（A3）

| ID | 必須 | 判定基準 |
|---|---|---|
| C-1 | Required | `planning/shortlist.md` 冒頭に「カタログ vs shortlist」の短い説明（3–5 行程度） |
| C-2 | Required | 選定記録テーブルに 8 セッション ID の行がある |
| C-3 | Required | README に shortlist の長い説明を **増やしていない** |

---

## D. ドキュメント（A4–A6）

| ID | 必須 | 判定基準 |
|---|---|---|
| D-1 | Required | `README.md` が現状より短い、または同等に簡素（比較・宣伝・長い AI 例なし） |
| D-2 | Required | README に他リポジトリ（Summit 等）との比較段落がない |
| D-3 | Required | `AGENTS.md` が `title` 必須・`title_ja` 任意・local-data 非コミットを反映 |
| D-4 | Required | `docs/content-policy.md` が abstract/transcript/機械要約の非コミットと整合 |
| D-5 | Required | `docs/local-data.md` が存在し、パス規約と「コミットしない」が書いてある |
| D-6 | Required | `docs/qwen-notes.md` が存在し、**notes 推敲のみ**（transcript 要約と混在しない） |
| D-7 | Required | `scripts/local_paths.py`（または同等）に local-data パス定数がある |

---

## E. Git と秘匿（A7）

| ID | 必須 | 判定基準 |
|---|---|---|
| E-1 | Required | `git init` 済み（ユーザーが A7 を実行許可した場合）。未許可なら N/A で Phase A 一部未完扱い |
| E-2 | Required | `git status` に `local-data/`, `.env`, `.auth/`, `private/` の **中身** が staged されていない |
| E-3 | Required | ユーザーが commit 指示していない限り、commit されていない |
| E-4 | Optional | remote 作成済み・visibility がユーザー指定と一致 |

---

## F. CI 相当（A8）

| ID | 必須 | 判定基準 |
|---|---|---|
| F-1 | Required | unittest + validate + check-schedule が PASS |
| F-2 | Required | `render` 後、生成物が最新（git 化後は `git diff --exit-code -- docs/catalog.md sessions/` が clean、または意図的差分が commit 済み） |
| F-3 | Required | 新規テスト・既存テストに regression なし |

---

## G. スコープ外（Fail 条件）

以下が **コミットに含まれていたら Fail**:

- 公式 abstract 全文の追加
- `local-data/` 配下の transcript / summary 実データ
- Phase B の fetch / summarize 本実装（スタブ・パス定数のみは可）
- README への「Summit 互換」「フルアーカイブ」等の宣伝

---

## H. 総合判定

```
Phase A COMPLETE  :=  A.* B.* C.* D.* F.* がすべて Pass
                      AND G に該当なし
                      AND E はユーザー指示に従う（init 許可時は E-1,E-2 Pass）
```

判定結果はチャットに報告（ファイル本体に「判定済み」注記は書かない）。

---

## I. 検証コマンド（証拠として貼る）

```bash
cd /home/aoki/dev/aws-reinvent-2026
python3 -m unittest discover -s tests -v
python3 scripts/reinvent.py validate
python3 scripts/reinvent.py check-schedule
python3 scripts/reinvent.py render
git status
git diff --stat   # git 化後
```
