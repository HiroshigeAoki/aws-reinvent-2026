# notes の Qwen 推敲

`notes/*.md` を手元 Qwen で整える。

## コマンド

`qwen-oneshot rewrite-ja` は推敲を標準出力へ。`--save` は run ログだけ残し、入力は上書きしない。

```bash
qwen-oneshot rewrite-ja --file /tmp/paragraph.md --save

qwen-oneshot rewrite-ja --file notes/<file>.md --save > /tmp/rewritten.md
mv /tmp/rewritten.md notes/<file>.md
```

手元 Qwen（`LOCAL_QWEN_BASE_URL`）が `/v1/models` に応答すること。停止時は exit 3。

字幕・機械要約は Phase B（`docs/local-data.md`）。
