# notes の Qwen 推敲

自分の文章（`notes/*.md`）を手元 Qwen で整える手順です。**コミットしてよい。**

## コマンド

`qwen-oneshot rewrite-ja` は推敲結果を **標準出力** に出します。`--save` はリクエスト／レスポンスを `$XDG_STATE_HOME/qwen-oneshot/runs/` に残すだけで、入力ファイルは上書きしません。

段落単位の例:

```bash
qwen-oneshot rewrite-ja --file /tmp/paragraph.md --save
```

ファイル全体を差し替える例:

```bash
qwen-oneshot rewrite-ja --file notes/<file>.md --save > /tmp/rewritten.md
# 内容を確認してから
mv /tmp/rewritten.md notes/<file>.md
```

- **入力:** `notes/` 配下の手書き Markdown（またはその抜粋）
- **出力:** 標準出力の推敲文。必要なら自分でファイルへ反映
- **前提:** 手元 Qwen（既定 `LOCAL_QWEN_BASE_URL`、未設定時は dgx 上の既定 endpoint）が `/v1/models` に応答すること。serve 停止時は exit 3

字幕 → `local-data/summaries` の機械要約は Phase B（`docs/local-data.md`）であり、本手順ではない。
