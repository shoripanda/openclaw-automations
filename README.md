# openclaw-automations

OpenClaw（AIエージェント）と一緒に作った自動化ワークフローの置き場です。実際に動かして得た知見と、そのまま再現できる構成を残しています。

## 収録

### 1. [keyword-monitor](./keyword-monitor) — キーワード監視 → Telegram通知（n8n）
GitHub / Hacker News / Hugging Face を指定キーワードで定期監視し、**前回との差分（新着）だけ**をTelegramに通知するn8nワークフロー。処理を1つのCodeノードに集約し、重複除去は `getWorkflowStaticData`、初回は洪水防止のため seed のみ、という設計。

### 2. [book-forge](./book-forge) — 対話で本を1冊つくるワークフロー
要件ヒアリング → 資料収集（URL裏取り）→ 著者インタビュー → 目次承認 → 執筆 → AI臭lint → 組版（LaTeX/PDF）まで一貫。状態は `project.json` に記録し、Claude Code / OpenClaw / ChatGPT で環境をまたいで再開できる。詳細は [book-forge/SKILL.md](./book-forge/SKILL.md)。

### 3. [ai-digest](./ai-digest) — 情報収集 → LLM要約 → 配信（Python単体）
AIツールのリリースフィードや Hugging Face トレンドを定期収集し、**新着だけ**をLLMで要約してTelegram（＋任意でZennスクラップ）へ配信する、OpenClaw非依存の軽量bot。標準ライブラリのみ。

## ライセンス
MIT
