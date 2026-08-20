# keyword-monitor（n8n）

指定キーワードの新着を **GitHub / Hacker News / Hugging Face** から拾い、**新着だけ**をTelegramに通知するn8nワークフローです。

## 仕組み
- **スケジュール（4時間ごと）→ Codeノード1つ** で完結。
- 各ソースをキーワードで検索 → `getWorkflowStaticData` に「見たID」を貯めて**重複除去**。
- **初回は seed のみ**（既存を全部既読化し、セットアップ通知だけ送る）。以降は新着だけ通知。
- 通知は Telegram Bot API を直接呼び出し（認証情報ノード不要）。

## セットアップ
1. n8n を用意（`npm i -g n8n && n8n start`、または Docker）。
2. `workflow.json` を n8n にインポート（Editor → Import from File）。
3. Codeノード内の資格情報を設定：**環境変数** `TG_BOT_TOKEN` と `TG_CHAT_ID` を渡す（`monitor.code.js` 参照）。
   - トークンは [@BotFather](https://t.me/BotFather) で発行。`TG_CHAT_ID` は自分のチャットID。
4. 一度 **Execute workflow**（初回 seed）→ 有効化（新しいUIでは **Publish**）。

## ファイル
- `workflow.json` … n8nワークフロー（トークン等はプレースホルダ済み）。
- `monitor.code.js` … Codeノードの中身（可読性のため単体でも掲載）。

## 実装メモ（実際にハマった点）
- **npm 11** はネイティブ拡張のビルドを既定で保留する。導入後は `n8n start` で起動確認を。
- CLIでの `import:workflow` はトップレベルに `id` が無いと `NOT NULL constraint failed` で落ちる。
- **スケジュールtrigger は `n8n execute` で起動できない**（手動実行はGUIの Execute workflow）。
- 新しいUIには「Active」トグルが無く **Publish** ボタンに変わっている。
- Node標準の `fetch`(undici) が Telegram にだけIPv6でタイムアウトすることがある。`curl`/axios（n8nの `httpRequest`）は通る。

## 注意
- `workflow.json` の Telegram トークン・chat_id は **プレースホルダ**です。自分の値に置き換えてください。実トークンを含んだままエクスポートして公開しないこと。
