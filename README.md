# bookmark-analyze

Firefox の `bookmarks.html` エクスポートを読み込み、Obsidian で使える
ブックマーク知識アーカイブへ変換するツールです。

1件のブックマークにつき1つの Markdown ノートを生成し、Dataview で扱いやすい
YAML frontmatter を付与します。

## 機能

- Firefox / Netscape 形式のブックマークHTMLを解析
- URLの正規化
  - `http` を `https` に変換
  - 末尾スラッシュを削除
  - `utm_source` などのトラッキングパラメータを削除
- `tldextract` による登録ドメイン抽出
- ルールベースの自動カテゴリ分類
  - shopping
  - ai
  - anime
  - video
  - pharmacy
  - archive
  - misc
- OpenAI / Gemini による任意のAI分類
- Obsidian / Dataview 対応の Markdown ノート生成
- カテゴリ別フォルダの自動作成
- 正規化URLが同じブックマークを重複として検出
- 重複ノートには `duplicate: true` を付与

## インストール

```bash
python3 -m pip install -e .
```

AI分類も使う場合:

```bash
python3 -m pip install -e ".[ai]"
```

開発・テスト用:

```bash
python3 -m pip install -e ".[dev]"
```

## 使い方

デフォルトの入力・出力パスは仕様に合わせています。

```bash
bookmark-analyze
```

読み込み元:

```text
bookmarks/bookmarks.html
```

出力先:

```text
ObsidianVault/Bookmarks/
```

パスを明示する場合:

```bash
bookmark-analyze /path/to/bookmarks.html --output /path/to/ObsidianVault/Bookmarks
```

インストールせずにソースから実行する場合:

```bash
python3 -m bookmark_analyze.cli bookmarks/bookmarks.html --output ObsidianVault/Bookmarks
```

## 出力構成

例:

```text
ObsidianVault/
└── Bookmarks/
    ├── Shopping/
    ├── AI/
    ├── Anime/
    ├── Video/
    ├── Pharmacy/
    ├── Archive/
    └── Misc/
```

## AI分類

通常はオフラインのルールベース分類が使われます。
`--ai-provider` を指定した場合だけ、AI分類を実行します。

OpenAI:

```bash
export OPENAI_API_KEY="..."
bookmark-analyze --ai-provider openai
```

Gemini:

```bash
export GEMINI_API_KEY="..."
bookmark-analyze --ai-provider gemini
```

モデルを指定する場合:

```bash
bookmark-analyze --ai-provider openai --ai-model gpt-4.1-mini
bookmark-analyze --ai-provider gemini --ai-model gemini-2.5-flash
```

## 生成されるノート例

```markdown
---
title: Amazon
url: https://amazon.co.jp
domain: amazon.co.jp
folder: shopping
folder_path:
  - shopping
category: shopping
tags:
  - shopping
  - ecommerce
created: 2026-05-16
---

# Amazon

## URL
https://amazon.co.jp

## Memo

## Related
```

## Dataview クエリ例

```dataview
TABLE domain, category
FROM "Bookmarks"
SORT domain
```

重複だけを確認する例:

```dataview
TABLE url, domain, category
FROM "Bookmarks"
WHERE duplicate = true
SORT domain
```

カテゴリ別に確認する例:

```dataview
TABLE url, domain, tags
FROM "Bookmarks"
WHERE category = "ai"
SORT title
```

## 開発

テスト実行:

```bash
python3 -m pytest
```

サンプルデータで変換を試す:

```bash
bookmark-analyze examples/bookmarks.html --output /tmp/ObsidianVault/Bookmarks
```

