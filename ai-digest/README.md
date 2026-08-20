# ai-digest

AIツール系の情報を定期収集し、**新着だけ**をLLMで要約して配信する、OpenClaw非依存の軽量bot（Python標準ライブラリのみ）。

## 流れ
1. **収集**：リリースのAtomフィード（Codex / Claude Code 等）＋ Hugging Face トレンドAPI を取得。
2. **新着判定**：`seen.json` に記録したIDと突き合わせ、新規だけ抽出。
3. **要約**：ローカルLLM（LM Studioの `llm()`）または外部ヘルパー（`brain()`）で、開発者向けに「何が変わったか＋意味」を日本語で要約。
4. **配信**：Telegram（必須）＋ Zennスクラップ追記（任意・ベストエフォート）。

## 使い方
```bash
python3 digest.py --dry-run   # 収集と新着判定だけ（安全）
python3 digest.py --no-post   # 要約まで（配信しない）
python3 digest.py             # 本番（新着があれば要約して配信）
```

## 設定（環境変数）
| 変数 | 用途 |
| --- | --- |
| `TG_BOT_TOKEN` | Telegram Bot トークン（または `TG_TOKEN_FILE` にパス） |
| `TG_CHAT` | 送信先チャットID |
| `DIGEST_HORDE_CMD` | （任意）`brain()` が呼ぶ外部LLMヘルパー。未設定なら既定パス |
| `DIGEST_ZENN_HELPER` | （任意）Zennスクラップ追記スクリプト。未設定ならZennはスキップ |

- ローカルLLMは LM Studio の OpenAI互換API（`http://localhost:1234/v1`）を想定。
- `seen.json` は状態ファイル（初回は空でOK。全部新着になるのを避けたい場合は一度 `--no-post` でシードしてから記録する運用でも可）。

## メモ
- **完全にOpenClaw非依存**（cron/launchdで単体運用可能）。
- トークン・チャットIDはコードに直書きせず、環境変数で渡す設計にしています。
