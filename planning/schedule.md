# 日別計画

現地時間 `America/Los_Angeles`。

| 日付 | メモ |
|---|---|
| 2026-11-29（日） | 受付・事前 |
| 2026-11-30（月） | 初日。会場と移動 |
| 2026-12-01（火） | 演習・質問 |
| 2026-12-02（水） | 代替回を含めて調整 |
| 2026-12-03（木） | 追加演習 |
| 2026-12-04（金） | まとめ・帰宅後の実験 |

[schedule.json](schedule.json) で機械チェック。時刻は `data/catalog.json` にオフセット付きで入れ、`planned` / `reserved` を付ける。

```bash
python3 scripts/reinvent.py check-schedule
```

会場間移動は目安 45 分。タイムゾーンは IANA（Las Vegas = UTC−08:00）。公式 Agenda の PDT 表記は時期とずれることがある。

出典: [Agenda](https://aws.amazon.com/events/reinvent/agenda/) / [FAQ](https://aws.amazon.com/events/reinvent/faqs/)（2026-09-29）
