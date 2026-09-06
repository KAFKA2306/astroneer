https://kafka2306.github.io/astroneer/io/

# ASTRONEER 日本語Wiki

ASTRONEER の日本語攻略Wikiです。

- `data/wiki.json` が記事・カテゴリ・source・確認日の正本です。
- `io/` が GitHub Pages 公開面です。
- `scripts/audit_wiki.py` が完成率、欠落、内部リンク、source、README production URLを監査します。
- 未収録記事は `planned`、本文と検証が完了した記事だけ `implemented` とします。
- 画像は原則として複製せず、原典の記事・画像ページへリンクします。

監査:

```
python scripts/audit_wiki.py
python scripts/audit_wiki.py --strict
```

`--strict` は全記事が完成した最終監査用です。
