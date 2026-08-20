#!/bin/bash
# book-forge: 原稿(Markdown) -> LaTeX(.tex) -> PDF
# usage: build.sh <manuscript.md> <outdir>
# 出力: <outdir>/book.tex (出版社に渡せるLaTeX原稿) と <outdir>/book.pdf (組版プレビュー)
#
# 密度(1ページの文字数)は環境変数で調整できる:
#   PAPER=四六|A5|B5|A4         判型 (既定 四六=127x188mm)
#   FONTSIZE=9pt               本文フォント (小さいほど字数増)
#   MARGIN=14                  余白mm (小さいほど字数増)
#   LINESPREAD=1.05            行間 (小さいほど字数増)
# プリセット例: ゆったり=9pt/16/1.15  標準=9pt/14/1.05  ぎっしり=8pt/12/1.0
set -e
MD="$1"; OUT="$2"
[ -z "$MD" ] || [ -z "$OUT" ] && { echo "usage: build.sh <manuscript.md> <outdir>"; exit 1; }
SRCDIR="$(cd "$(dirname "$MD")" && pwd)"
mkdir -p "$OUT"

# --- 密度パラメータ (既定=標準) ---
PAPER="${PAPER:-四六}"
FONTSIZE="${FONTSIZE:-9pt}"
MARGIN="${MARGIN:-14}"
LINESPREAD="${LINESPREAD:-1.05}"
IN=$MARGIN; OUT_M=$((MARGIN-2)); [ "$OUT_M" -lt 8 ] && OUT_M=8
case "$PAPER" in
  四六) GEO="paperwidth=127mm,paperheight=188mm,top=${MARGIN}mm,bottom=${MARGIN}mm,inner=${IN}mm,outer=${OUT_M}mm" ;;
  A5)  GEO="a5paper,top=${MARGIN}mm,bottom=${MARGIN}mm,inner=${IN}mm,outer=${OUT_M}mm" ;;
  B5)  GEO="b5paper,top=${MARGIN}mm,bottom=${MARGIN}mm,inner=${IN}mm,outer=${OUT_M}mm" ;;
  A4)  GEO="a4paper,margin=${MARGIN}mm" ;;
  *)   GEO="paperwidth=127mm,paperheight=188mm,top=${MARGIN}mm,bottom=${MARGIN}mm,inner=${IN}mm,outer=${OUT_M}mm" ;;
esac

# 1) 図版を出力先へ複製（相対パス参照をtectonicが解決できるように）
find "$SRCDIR" -maxdepth 1 \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.pdf' \) \
  -exec cp {} "$OUT"/ \; 2>/dev/null || true

# 2) 体裁ヘッダ（見出しを詰める・ノンブル下中央・図キャプションは本文より小さく）
cat > "$OUT/_style.tex" <<STY
\usepackage{titlesec}
\titleformat{\chapter}[hang]{\bfseries\large}{}{0pt}{}
\titlespacing*{\chapter}{0pt}{2pt}{10pt}
\titleformat{\section}{\bfseries\normalsize}{}{0pt}{}
\titlespacing*{\section}{0pt}{8pt}{4pt}
\pagestyle{plain}
\linespread{${LINESPREAD}}
\usepackage{caption}
\captionsetup{font=footnotesize,labelfont=bf,skip=4pt}
STY

# 3) Markdown -> LaTeX（book クラス・日本語・図キャプション対応）
pandoc "$MD" -s -o "$OUT/book.tex" \
  --top-level-division=chapter \
  -V documentclass=book -V classoption=oneside \
  -V CJKmainfont="Hiragino Mincho ProN" \
  -V "geometry:${GEO}" \
  -V fontsize="${FONTSIZE}" -V lang=ja \
  -H "$OUT/_style.tex"

echo "[book-forge] LaTeX 生成: $OUT/book.tex  (判型=$PAPER 字=$FONTSIZE 余白=${MARGIN}mm 行間=$LINESPREAD)"

# 4) LaTeX -> PDF（tectonicがXeLaTeXで日本語組版）
( cd "$OUT" && tectonic book.tex >/dev/null 2>&1 )
echo "[book-forge] PDF 生成: $OUT/book.pdf"
