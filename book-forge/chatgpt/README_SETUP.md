# book-forge を ChatGPT で使う手順

ChatGPT の「プロジェクト（Projects）」機能に入れて、いつでも本づくりを呼び出せるようにします。所要5分。

## 1. プロジェクトを作る
1. ChatGPT 左サイドバー →「プロジェクト」→「新しいプロジェクト」
2. 名前を「book-forge（本づくり）」などにする

## 2. 指示（Instructions）を貼る
1. プロジェクトの「指示」欄を開く
2. `PROJECT_INSTRUCTIONS.md` の中身を全部コピーして貼り付け → 保存
   - これがこのプロジェクトの“頭脳”。常に読まれます。

## 3. ナレッジ（ファイル）をアップロード
プロジェクトの「ファイル」に、この4つを追加：
- `pj.py` … 状態管理スクリプト（コードインタプリタで実行）
- `PHASES.md` … 対話の詳しい手順・種類別インタビュー質問集
- `RULES_FAILURE-LOG.md` … 守るべきルールと過去の失敗と正解
- （任意）`SKILL.md` … 概要

## 4. 使い方
プロジェクト内の新しいチャットで、こう言うだけ：
> 本を作りたい

→ フェーズ0の質問から順に進みます。「小論文を書きたい」でもOK。

## 5. PDFの作り方（重要）
ChatGPT の中では日本語のLaTeX組版（pandoc/tectonic）が動きません。PDFは外部で作ります。
- **Overleaf（無料・おすすめ）**：出力された `book.tex` を新規プロジェクトに貼る。
  - フォントは Overleaf にある `Noto Serif CJK JP` を使う（指示文にそう書いてあります）。
  - コンパイラは XeLaTeX か LuaLaTeX を選ぶ。
- **Mac（このワークスペース）**：`~/.openclaw/workspace/book-forge/scripts/build.sh` で PDF 化（Hiragino Mincho使用）。ソラに「このtexをPDFにして」と言えばやります。

## 6. 続きから再開
ChatGPT が出す `project.json` を保存しておけば、別の日・別環境（Claude Code / OpenClaw）でも同じ状態から続けられます。アップロードして「この project.json の続きから」と言えばOK。

## メモ：ChatGPTでできること／できないこと
- できる：対話ヒアリング、ブラウジングで資料裏取り、pj.py実行、原稿(md)とLaTeX(tex)生成、図の作成（matplotlib等）
- できない（外部で）：日本語PDFの最終組版、natural-japanese の lint.py 実行（※AI臭ルールは指示文でモデルが適用）
