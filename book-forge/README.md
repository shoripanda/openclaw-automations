# book-forge

対話で本・小論文を1冊つくるワークフロー。詳細は [SKILL.md](./SKILL.md) と [PHASES.md](./PHASES.md)、守るべきルールは [FAILURE-LOG.md](./FAILURE-LOG.md) を参照。

- `scripts/pj.py` … 状態管理CLI（project.json）。
- `scripts/build.sh` … Markdown→LaTeX→PDF（判型・密度を環境変数で調整）。
- `scripts/lint.sh` … natural-japanese による「AI臭」検出。
- `chatgpt/` … ChatGPTプロジェクトへ持ち込むための一式。
- `examples/` … 生成物のサンプル。
