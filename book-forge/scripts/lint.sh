#!/bin/bash
# book-forge フェーズ5（推敲）: 原稿のAI臭を機械検出する。
# natural-japanese スキルの lint.py をそのまま利用（車輪の再発明をしない）。
# usage: lint.sh <manuscript.md> [essay|tech|business]   (--json で機械可読)
MD="$1"; GENRE="${2:-essay}"; shift 2 2>/dev/null
[ -z "$MD" ] && { echo "usage: lint.sh <manuscript.md> [essay|tech|business] [--json]"; exit 1; }
NJ=$(ls -d "$HOME"/.claude/plugins/cache/natural-japanese/natural-japanese/*/skills/natural-japanese 2>/dev/null | sort -V | tail -1)
[ -z "$NJ" ] && { echo "natural-japanese スキルが見つかりません（未インストール）"; exit 1; }
MD_ABS="$(cd "$(dirname "$MD")" && pwd)/$(basename "$MD")"
( cd "$NJ" && uv run scripts/lint.py --genre "$GENRE" "$@" "$MD_ABS" )
# 検出が出たら natural-japanese の判断台帳（§4）に沿って「直す/残す」を判断し、収束するまで再lintする。
