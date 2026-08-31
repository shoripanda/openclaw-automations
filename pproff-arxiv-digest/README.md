# pproff-arxiv-digest — arXiv論文ダイジェスト（@pproffbot）

`pproff` エージェントが毎朝 arXiv から新着論文を収集し、日本語要約を Telegram（@pproffbot）へ配信する automation。

- 対象bot: Telegram `@pproffbot`（エージェント `pproff`）
- automation ID: `bee4d379-5d91-43cb-909c-754b2cf954f4`（`arxiv-paper-digest:pproff`）
- スケジュール: cron `0 9 * * *`（Asia/Tokyo）毎日9:00
- 配信: announce → `telegram:6134177382`
- テーマ: (1) LLM/大規模言語モデル (2) 自動化/エージェント (3) 無検閲化・モデレーション除去

## モデル移行の記録（2026-09-01）

### 事象
@pproffbot が停止。原因は **DeepSeek 有料APIの課金切れ**。

### 実態
`pproff` エージェントのモデルが `deepseek/deepseek-v4-pro`（有料）に設定されていた一方、
`~/.openclaw/openclaw.json` の `models.providers` には **`freecc`（無料枠プロキシ）しか定義が無い**。
課金切れで DeepSeek プロバイダが機能せず、モデル参照が解決できずに停止していた。

### 対応
`~/.openclaw/openclaw.json` の `agents.entries.pproff.model` を
**`deepseek/deepseek-v4-pro` → `freecc/claude-sonnet-4-5`（無料枠）** に切替。

- 無料枠プロキシ: `http://127.0.0.1:8082`（FreeCC / Groq gpt-oss-120b →自動フォールバック、コスト0）
- 既存の `crow` エージェントも同じ `freecc/claude-sonnet-4-5` を使用中＝環境内で確立した無料枠。
- **1エントリのみ**をピンポイントで書き換え。`deepseek3` / `deepseek4`（別用途）は `deepseek/deepseek-v4-pro` のまま保持（全体置換しない）。
- 編集前バックアップ: `~/.openclaw/openclaw.json.bak-pproff-freecc-20260901_075717`

### 検証
- freecc プロキシ生存: `GET http://127.0.0.1:8082/v1/models` → `200`
- `openclaw agents list` で pproff の Model が `freecc/claude-sonnet-4-5` と表示されることを確認
- automation を手動実行（`openclaw cron run bee4d379-... --wait --expect-final`）して無料枠で完走することを確認

## 失敗ルート台帳
- 2026-09-01 pproff停止の原因は「automationのpayloadにモデル指定が無い」ため、**エージェント設定側の `model`** を見る必要があった → automation単体を見ても原因不明。`openclaw.json` の `agents.entries.<agent>.model` が真の配線。
- 2026-09-01 `deepseek/deepseek-v4-pro` は `models.providers` に定義が無く解決不能 → 有料課金が切れると即停止。無料枠 `freecc/claude-sonnet-4-5` は provider 定義済みでコスト0、フォールバックありで堅牢。
- 2026-09-01 `openclaw config reload` は存在しない → 設定反映は `openclaw agents list` で確認、実反映は automation 手動実行で検証。
