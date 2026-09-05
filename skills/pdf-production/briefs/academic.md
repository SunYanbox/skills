# Academic Line — LaTeX (Tectonic)

For scholarly and math-heavy documents: papers, theses, dissertations, math
worksheets/exams, IEEE/ACM formatted submissions, and Beamer slide decks.
LaTeX is the right tool when the document needs precise math typesetting,
citations, or strict academic formatting.

## Stack

`tectonic` — a self-contained LaTeX engine that downloads packages on demand.
Single binary, no full TeX Live install required.

Check availability:

```bash
tectonic --version
```

If missing, install from https://tectonic-typesetting.github.io/ (Windows: the
MSI installer or `winget install tectonic`).

## Workflow

### 1. Run the font helper

Academic documents with CJK need the OFL fonts. Run `scripts/ensure_fonts.py`
and capture the cache directory for `fontspec` paths.

### 2. Write the preamble

Load `fontspec` for font control and standard math packages:

```latex
\documentclass[11pt,a4paper]{article}
\usepackage{fontspec}
\usepackage{amsmath, amssymb}
\usepackage[margin=2.5cm]{geometry}

\setmainfont{NotoSerifSC-Regular.ttf}[
  Path = <cache_dir>/,
  BoldFont = NotoSerifSC-Bold.ttf,
  Extension = .ttf
]
\setsansfont{NotoSansSC-Regular.ttf}[
  Path = <cache_dir>/,
  BoldFont = NotoSansSC-Bold.ttf
]
\setmonofont{SourceSans3-Regular.ttf}[
  Path = <cache_dir>/
]

\begin{document}
...
\end{document}
```

Path note: `Path = <cache_dir>/` needs a trailing slash. On Windows, use forward
slashes or escape backslashes — forward slashes are safer across shells.

### 2b. Figures and diagrams

Figures are block-level elements — always inside a `figure` environment, never bare
`\includegraphics` in the text body. For dual-column layouts this matters even more;
a bare image in a narrow column will overflow or collide with text.

```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=\columnwidth]{diagram.png}
  \caption{...}
\end{figure}
```

For diagrams with many nodes (>12) or tangled connections, don't force one giant
figure. Split it into a simplified overview (≤8 nodes, top-level flow only) plus a
detail table, and cross-reference the two in their captions.

### 3. Math typesetting

Use `amsmath` environments:

```latex
\begin{equation}
  E = mc^2
\end{equation}

\begin{align}
  f(x) &= x^2 + 2x + 1 \\
       &= (x + 1)^2
\end{align}
```

Inline math with `$...$`, display math with `\[...\]` or the environments above.
Never try to fake math with Unicode symbols — LaTeX's typesetting engine exists
for this.

### 3b. Tables: column count tiers

Tables are the most common overflow source in LaTeX, especially in dual-column
papers. Match the column count to the layout before writing the table:

| Data columns | Single-column layout | Dual-column layout |
|--------------|---------------------|--------------------|
| ≤ 4 | `tabular` with `\columnwidth` | `tabular` with `\columnwidth` |
| 5–6 | `tabularx{\textwidth}` or `\small` | `\small` + `tabularx{\columnwidth}` |
| 7–8 | `tabularx{\textwidth}` | `\resizebox{\columnwidth}{!}` |
| ≥ 9 | `table*` full width, `tabularx{\textwidth}` | `table*` full width, `\resizebox{\textwidth}{!}` |

Rules:
- Prefer `tabularx` over bare `tabular` for wide tables — it can wrap columns.
- `\resizebox` is a last resort; after scaling, verify the smallest text is still
  ≥ 6pt or it becomes unreadable.
- In dual-column papers, a bare `tabular` with 8+ columns will guarantee overflow —
  always widen via `table*` or shrink via `\resizebox{\columnwidth}`.
- Never use `\textwidth` inside a single-column float of a dual-column layout;
  `\textwidth` is the full page width there. Use `\columnwidth` instead.

### 4. Chinese in LaTeX

With `fontspec` + the Noto SC fonts registered as main fonts, Chinese text works
directly:

```latex
\begin{document}
这是中文正文，数学公式 $a^2 + b^2 = c^2$ 混排正常。
\end{document}
```

No `ctex` package needed when you control the fonts explicitly. If the document
needs full Chinese typesetting conventions (chapter titles, spacing), consider
`ctex` — but it brings its own font assumptions, so prefer plain `fontspec` for
short documents.

### 5. Compile

```bash
tectonic document.tex
```

This produces `document.pdf`. First run downloads required packages (network
needed); subsequent runs are fast. Tectonic runs LaTeX enough passes
automatically for cross-references and TOC.

For continuous output to a specific file:

```bash
tectonic document.tex --outdir ./
```

### 6. Verify

```python
from pypdf import PdfReader
reader = PdfReader("document.pdf")
print(f"Pages: {len(reader.pages)}")
text = reader.pages[0].extract_text()
assert "<expected phrase>" in text
```

Note: math extracted by pypdf may appear garbled — verify with page count plus a
plain-text phrase, and visually confirm math rendering if possible.

## Document types

### Article / paper

```latex
\documentclass[11pt,a4paper]{article}
```

Standard for reports and short papers. Use `abstract` environment, `\section`
for structure.

### Thesis / dissertation

```latex
\documentclass[12pt,a4paper]{book}
```

Chapters become `\chapter{...}`. Add a table of contents with `\tableofcontents`.

### Beamer slides

```latex
\documentclass{beamer}
\usetheme{Madrid}  % or default, Berlin, etc.
\begin{document}
\begin{frame}{Slide Title}
  Content here
\end{frame}
\end{document}
```

For CJK in Beamer, the `fontspec` font setup in the preamble applies the same
way.

### Math exam / worksheet

Use the `exam` documentclass if available via Tectonic's package fetch, or
structure with `article` + numbered `\section*` blocks + `\vspace` for answer
areas.

**Answer space planning** — the same exam rules as report.md apply, adapted to
LaTeX:

- **Short-answer questions** (fill-in-blank, T/F): no space needed.
- **Problem-solving / proof questions**: allocate space per step — roughly
  `\vspace{2.5cm}` per expected step (3–4 lines). A 4-step problem gets
  `\vspace{10cm}`, not a single `\vspace{1cm}`.
- **When in doubt, over-allocate.** A mostly-blank final page is far better than
  a student forced to squeeze work into margins.
- **Never** put answer space in a `\vspace*{}` after a `\newpage` — reserve it
  *before* breaking to the next question.
- For Beamer slides, answer space is irrelevant; for handouts, use the printed
  exam rules above.

## Citations

For real academic work, prefer `biblatex` + BibTeX:

```latex
\usepackage[backend=biber]{biblatex}
\addbibresource{references.bib}
...
\printbibliography
```

Tectonic fetches `biblatex` and `biber` on first use. If a document doesn't need
citations, skip this entirely.

## Anti-patterns

- Using Unicode math symbols instead of LaTeX math mode.
- Hardcoding the font cache path without running `ensure_fonts.py`.
- Assuming `tectonic` is on PATH without checking `--version`.
- Faking a paper in Word/HTML when the user asked for academic formatting.
- Skipping the pypdf page-count verification after compile.
