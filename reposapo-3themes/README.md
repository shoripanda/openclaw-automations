# reposapo-3themes — @reposapo 3テーマ定期収集

Claude Code / Codex / 無検閲(uncensored·abliterated)LLM の3テーマを定期収集し、
X(@reposapo)向けの投稿文を生成 → **既存の朝承認フロー**で人間が確認 → 承認分だけ自動投稿する。

- 導入日: 2026-09-01
- 対象アカウント: X `@reposapo`
- 投稿フロー: **A（承認してから自動投稿）**。捏造・誇張は承認ゲートで止まる。
- 実装先: `~/xpost-bot/generate.py`（既存ボットに関数追加。キュー/投稿ロジックは無改変）

## 収集ソース

| テーマ | ソース | 選別 |
|---|---|---|
| Claude Code | GitHub `anthropics/claude-code` releases.atom | `collect_news()`（既存） |
| Codex | GitHub `openai/codex` releases.atom | `collect_news()`（既存） |
| 無検閲LLM | HuggingFace models API（`search=uncensored/abliterated` × `sort=trendingScore`） | **likes≥30** で無名再配布を除外（新規実装） |

各テーマから「`seen` 未収録の最新1件」を選び、毎回 `main()` の先頭で最優先生成する。

## automations（OpenClaw）

| 役割 | ID | スケジュール | ターゲット |
|---|---|---|---|
| 収集（3テーマ生成→キュー投入） | `82543d01-e064-4973-86bb-c5b7a04b356b` | `30 5,17 * * *` (Asia/Tokyo) 毎日5:30/17:30 | isolated |
| 朝の承認（本日分をチャット提示→承認分のみ投稿） | `eec9453d-571a-4831-ada9-5bcb91daefe2` | `0 6 * * *` (Asia/Tokyo) 毎日6:00 | main / telegram |

収集automationは既存の朝承認automation（`plan.py` が本日分を選定）に載せる形。承認・投稿・外向きアクションは人間の承認を通らない限り出ない。

## パイプライン

```
5:30 / 17:30  収集 automation
   └─ generate.py: collect_topics()
        ├─ Claude Code / Codex  … collect_news() から最新1件
        └─ 無検閲LLM           … hf_uncensored() (likes≥30) から最新1件
   └─ summarize_*(): fcc(無料枠) → 失敗時 Opus(claude -p) フォールバック
   └─ queue.json に pending 追加（key: news:<id> / hfunc:<id>）

6:00  朝の承認 automation
   └─ plan.py: 本日分を選定 → Telegram にプラン提示
   └─ 人間が承認したものだけ run_due.py で自動投稿
```

## 関連ファイル

- `generate.snippet.py` — 本automationで追加した3関数の抜粋（`hf_uncensored` / `summarize_uncensored` / `collect_topics` と `main()` の最優先生成ブロック）。実体は `~/xpost-bot/generate.py`。
- 編集前バックアップ: `~/xpost-bot/generate.py.bak-20260901_070136`

## 投稿比率の調整（2026-09-01）

Codex / Claude Code 系の投稿が増えすぎたため、**arXiv論文の比率を上げる**方向に配分を変更。
コードは無改変、`~/xpost-bot/config.json` の数値のみで制御する。

| キー | 意味 | 変更前 | 変更後 |
|---|---|---|---|
| `posts_per_run` | arXiv論文の生成本数/回 | 4 | **7** |
| `news_per_run` | Claude Code/Codex ニュースの追加本数/回（`collect_topics` の固定分とは別の重複枠） | 2 | **1** |
| `trend_per_run` | HFトレンド（中立）本数/回 | 3 | 3（据え置き） |

1回あたりの内訳（変更後）: **論文7** : 固定テーマ3（Claude Code/Codex/無検閲）: ニュース1 : トレンド3。
`collect_topics()` の固定3テーマ（毎回最優先で確保）はそのまま。論文枠だけを厚くし、Codex/Claudeの重複ニュース枠を薄くした。

- 実証: 変更後に `generate.py` を実走 → `done: +7 drafts`、`[1]〜[7]` すべて arXiv論文であることを確認（旧設定は `+4`）。
- 編集前バックアップ: `~/xpost-bot/config.json.bak-ratio-20260901_113645`
- さらに論文中心にするなら `news_per_run:0` / `trend_per_run` を下げ、`posts_per_run` を上げる。逆に戻すならバックアップを復元。

## 失敗ルート台帳

- 2026-09-01 fcc(無料枠プロキシ `127.0.0.1:8082`)が時間帯によりタイムアウト → コードバグではない。設計通り `claude -p --model claude-opus-4-8` に自動フォールバックして生成完走。fccが死んでても止まらない。
- 2026-09-01 @reposapo の投稿比率は generate.py のコードではなく `config.json` の `posts_per_run`/`news_per_run`/`trend_per_run` で決まる。テーマ固定分（collect_topics）は毎回3件で不変なので、論文比率を上げるには論文枠(`posts_per_run`)を増やしニュース枠を減らすのが正解。
- 2026-09-01 HF無検閲モデルは likes/dl=0 の個人再配布ゴミが多い → `likes≥30` 下限＋trendingScore順で「いま話題」のみ拾う。
