---
name: "book-forge"
description: "本や小論文を対話で作る。資料裏取り→インタビュー→目次承認→執筆→lint→組版→PDF/LaTeX出力まで一貫."
---

# book-forge — 対話で本を1冊つくるスキル

利用者と対話しながら、**本・小論文を企画から入稿原稿まで一貫**で作る。
資料集め（裏取り）・著者インタビュー・目次の承認・執筆・AI臭の除去・図の作成・組版（PDF/LaTeX）までを、状態ファイル `project.json` に記録しながら**中断・再開・環境またぎ**で進める。

## いつ使うか
- 「本を作りたい」「小論文/レポートを書きたい」「エッセイ/技術書/実用書を一冊にしたい」
- 原稿だけでなく**資料収集・インタビュー・図の挿入・組版**まで通しでやりたいとき
- 出版社に渡せる **LaTeX原稿** や、KDP等に使う **PDF** が欲しいとき

## 全体の流れ（フェーズ0〜7・ゲート制）
各フェーズは `scripts/pj.py check <pj> <phase>` を通るまで次に進めない。**目次を著者が承認するまで本文を書かない**のが最重要ゲート。

0. **intake** 要件ヒアリング（種類・判型・読者・狙い・分量・トーン）→ `meta` を埋める
1. **research** 資料収集。web検索で**URL＋参照日つきで裏取り**（体験主体のエッセイ等は軽め）
2. **interview** 著者インタビュー（原体験・独自ノウハウ・主張と反論）＝独自性の源
3. **outline** 目次（章・節＋各章の目標字数＋結論を含む見出し）→ **著者承認** → `approve`
4. **drafting** 執筆。目標字数に**必ず**届かせる（実測して足りなければ加筆）
5. **revision** `scripts/lint.sh` で**AI臭を機械検出**し、natural-japanese の判断で収束させる
6. **layout** 図を作成/挿入し、`scripts/build.sh` で組版
7. **export** `book.pdf`（プレビュー）と `book.tex`（入稿用LaTeX）を出力

詳しい対話手順・種類別の質問バンクは **references/PHASES.md** を参照。

## スクリプト（車輪の再発明をしない）
- `scripts/pj.py` … 状態管理CLI。`init/show/get/set/add-research/add-interview/set-outline/approve/state/check`。bash(Claude Code/OpenClaw)でもpython(ChatGPT)でも同じに動く。
- `scripts/build.sh` … Markdown→LaTeX→PDF（pandoc＋tectonic）。**判型・密度は環境変数**で調整：`PAPER`(四六/A5/B5/A4) `FONTSIZE` `MARGIN`(mm) `LINESPREAD`。既定＝見出しを詰める・ノンブル下中央・キャプション小。
- `scripts/lint.sh` … フェーズ5のAI臭検出。natural-japanese スキルの `lint.py` をそのまま利用。

## 必ず守るルール（違反しやすい順）— 詳細は references/FAILURE-LOG.md
- **指定字数は必ず満たす**。下回ったら加筆して再ビルド（字数は実測）。
- **無意味な太字を付けない**。太字は核心1箇所のみ。日付・数字を機械的に太字化しない。
- **取り上げた内容に関する図を入れる**。図は出典明記・**線と文字を重ねない**・見切れない・日本語フォント（豆腐防止）。
- **図のキャプションは本文より小さい文字**（本文の続きと区別）。
- **出典はURL＋参照日**を必ず記載し、web検索で**実在・数値を裏取り**（捏造厳禁）。
- **語彙・固有名詞の表記を全体で統一**（表記ゆれ禁止。例：Claude Code／Claude Opus 4.8。本文カタカナと参考文献の英語を混在させない）。
- **ノンブルは下部中央・柱なし**。
- **図サイズ・1ページの文字数（密度）は利用者が自由に変更できる**（`{width=70%}`、`FONTSIZE/MARGIN/LINESPREAD`）。

## 使い方の例（bash）
```bash
BF=~/.openclaw/workspace/book-forge   # スクリプトの場所（環境に合わせて）
python3 "$BF/scripts/pj.py" init ./mybook --種類 技術書 --体裁 book --判型 四六 \
  --読者 "一般＋実ユーザ" --狙い "…" --目標文字数 5000 --トーン 軽妙
# …research/interview/outline を pj.py で記録し、outline承認後 approve …
python3 "$BF/scripts/pj.py" approve ./mybook
bash "$BF/scripts/lint.sh" ./mybook/manuscript.md essay --json
PAPER=四六 FONTSIZE=9pt MARGIN=14 bash "$BF/scripts/build.sh" ./mybook/manuscript.md ./mybook/out
```

## 環境アダプタ
- **Claude Code / OpenClaw**：本手順＋スクリプトをbashで実行。調査はweb検索/サブエージェント。
- **ChatGPT**：本手順を指示に、`pj.py` をコード実行で再現。調査はブラウジング。**入出力は同じ project.json**。
