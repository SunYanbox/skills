# Font policy

This skill uses **only SIL OFL 1.1 fonts** so every generated PDF can be freely shared,
printed, and embedded without licensing risk. Font files are downloaded on first use and
cached locally rather than committed to the repository.

## The four families

| Purpose | Serif | Sans |
|---------|-------|------|
| Chinese | Noto Serif SC | Noto Sans SC |
| Latin | Source Serif 4 | Source Sans 3 |

Two weights per family: **Regular (400)** and **Bold (700)**. Subset files (SC = simplified
Chinese) keep the download reasonable while covering everyday documents.

Why these: Noto SC and Source are from the same design lineage (Adobe/Google), so mixed
Chinese-English text looks consistent across serif and sans styles. All are available as
static TTF files, which ReportLab needs (it cannot register OTF/CFF fonts).

## Font cache

`scripts/ensure_fonts.py` downloads the 8 TTF files to a local cache and prints the
directory. The default cache location follows the user cache convention:

- Windows: `%LOCALAPPDATA%/pdf-production/fonts`
- macOS / Linux: `~/.cache/pdf-production/fonts`

Do not hardcode the cache path in documents. Run the helper and capture its stdout — it
prints the resolved directory so the skill works across machines.

## Registration snippets

### ReportLab

```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR = "<cache_dir>"  # from ensure_fonts.py stdout
pdfmetrics.registerFont(TTFont("NotoSerifSC", f"{FONT_DIR}/NotoSerifSC-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoSerifSC-Bold", f"{FONT_DIR}/NotoSerifSC-Bold.ttf"))
pdfmetrics.registerFont(TTFont("NotoSansSC", f"{FONT_DIR}/NotoSansSC-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoSansSC-Bold", f"{FONT_DIR}/NotoSansSC-Bold.ttf"))
# Latin fonts only needed when mixing styles explicitly
```

Then use these names in `registerFontFamily` so `<b>` tags switch weight correctly.

### Tectonic / LaTeX

Use XeLaTeX-style font loading with fontspec and absolute paths to the TTF files:

```latex
\usepackage{fontspec}
\setmainfont{NotoSerifSC-Regular.ttf}[
  Path = <cache_dir>/,
  BoldFont = NotoSerifSC-Bold.ttf,
  Extension = .ttf
]
\setsansfont{NotoSansSC-Regular.ttf}[
  Path = <cache_dir>/,
  BoldFont = NotoSansSC-Bold.ttf
]
```

Note: Tectonic compiles with XeTeX engine by default, so fontspec works directly.

## Adding new weights or families

If a document genuinely needs another weight (e.g., Light 300 for poster titles), extend
`ensure_fonts.py`'s download table rather than hardcoding a new path. Keep every addition
on the SIL OFL license and prefer the static TTF form.
