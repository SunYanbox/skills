# Report Line — Structured Documents (ReportLab)

For text-heavy structured documents: reports, proposals, resumes/CVs, contracts,
invoices, exam papers, and similar multi-page documents with headings, paragraphs,
and tables.

## Prerequisites

1. Run `scripts/ensure_fonts.py` and capture the cache directory (stdout).
2. Read `references/fonts.md` for registration snippets.
3. Read `references/page-setup.md` for sizes and margins.

## Stack

`reportlab` (Platypus: SimpleDocTemplate + flowables). Check availability first:

```python
import reportlab
```

If missing, `pip install reportlab`.

## Workflow

### 1. Register fonts

Use the OFL families from `references/fonts.md`. Register Chinese fonts with
`TTFont` and wire weights with `registerFontFamily` so `<b>` works:

```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping

FONT_DIR = "<cache_dir>"  # from ensure_fonts.py stdout
pdfmetrics.registerFont(TTFont("NotoSerifSC", f"{FONT_DIR}/NotoSerifSC-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoSerifSC-Bold", f"{FONT_DIR}/NotoSerifSC-Bold.ttf"))
pdfmetrics.registerFont(TTFont("NotoSansSC", f"{FONT_DIR}/NotoSansSC-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoSansSC-Bold", f"{FONT_DIR}/NotoSansSC-Bold.ttf"))

pdfmetrics.registerFontFamily(
    "NotoSerifSC", normal="NotoSerifSC", bold="NotoSerifSC-Bold",
    italic="NotoSerifSC", boldItalic="NotoSerifSC-Bold",
)
pdfmetrics.registerFontFamily(
    "NotoSansSC", normal="NotoSansSC", bold="NotoSansSC-Bold",
    italic="NotoSansSC", boldItalic="NotoSansSC-Bold",
)
```

> CJK fonts rarely have true italic variants; mapping italic back to the
> regular face is standard practice and avoids missing-glyph errors.

### 2. Set up the document

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate

doc = SimpleDocTemplate(
    "output.pdf",
    pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm,
    title="<document title>",   # PDF metadata
    author="<author>",
    creator="pdf-production skill",
    subject="<one-line summary>",
)
```

### 3. Define styles

Create a `ParagraphStyle` hierarchy rather than inline formatting. Use the
registered font families by name:

```python
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

body = ParagraphStyle("body", fontName="NotoSerifSC", fontSize=12, leading=19)
h1 = ParagraphStyle("h1", parent=body, fontName="NotoSansSC", fontSize=20, leading=28,
                    spaceBefore=12, spaceAfter=12)
h2 = ParagraphStyle("h2", parent=body, fontName="NotoSansSC", fontSize=16, leading=24,
                    spaceBefore=10, spaceAfter=8)
```

Body text in CJK needs `leading` at least 1.5× `fontSize` — see page-setup.md.
Use Noto Sans SC for headings (UI-like, scannable) and Noto Serif SC for body
prose when a formal tone matters; all-sans is fine for business documents.

**CJK alignment rule**: use `TA_LEFT` (left-align) for body paragraphs — never
`TA_JUSTIFY`. Justified alignment has no word spaces to stretch in Chinese text,
so the engine pulls apart the gaps *between* CJK and Latin characters instead,
producing visibly uneven spacing. Left alignment is the standard for CJK body
text and avoids this artifact entirely.

### 4. Build content as flowables

```python
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak

story = []
story.append(Paragraph("<title text>", h1))
story.append(Paragraph("<body text>", body))
story.append(Spacer(1, 0.5*cm))
story.append(PageBreak())
```

Rules:

- Use `Paragraph` for all text — it handles wrapping and inline tags (`<b>`, `<i>`,
  `<font size=...>`). Never lay out body text with `canvas.drawString`, which does
  not wrap.
- Use `Spacer(width, height)` for vertical gaps instead of empty paragraphs.
- Use `PageBreak()` explicitly; do not rely on content naturally spilling to
  create section breaks.

### 4b. Figures and diagrams

Images go into the story as standalone `Image` flowables — never embedded inside a
`Paragraph`. Block-level figures prevent text wrapping around them and keep layout
predictable:

```python
from reportlab.platypus import Image
img = Image("diagram.png", width=450)   # height auto-scales from aspect ratio
story.append(img)
```

For diagrams with many nodes (>12) or tangled connections, don't force one giant
figure. Split it into a simplified overview (≤8 nodes, top-level flow only) plus a
detail table, and cross-reference the two in their captions. This keeps text
readable and avoids the engine shrinking everything to fit.

### 5. Tables

Wrap cell content in `Paragraph` so it wraps inside the cell:

```python
from reportlab.platypus import Table

data = [
    [Paragraph("<b>Header</b>", cell_style), Paragraph("<b>Header 2</b>", cell_style)],
    [Paragraph("row 1", cell_style), Paragraph("row 1 b", cell_style)],
]
table = Table(data, colWidths=[8*cm, 8*cm])
```

Set `colWidths` explicitly (see the 12-column grid in page-setup.md). Before building
any table, compute the usable width and make the columns fit it — this is the single
most common overflow bug:

```python
available = A4[0] - doc.leftMargin - doc.rightMargin   # ~ 595 - 2*56.7 ≈ 482pt
assert sum(colWidths) <= available                       # verify, don't assume
```

Long text cells must hold `Paragraph` objects, never bare strings — bare strings do
not wrap and will blow past the cell width. For CJK text budget roughly 12pt per
character at 10pt font size when estimating column needs. Style with `TableStyle` —
grid lines, padding, background shading for header rows:

```python
from reportlab.platypus import TableStyle
from reportlab.lib import colors

table.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.92, 0.92, 0.92)),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
]))
```

### 6. Page numbers (header/footer)

Use `onPage` callbacks, not a flowable in the story:

```python
def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("NotoSerifSC", 9)
    canvas.drawCentredString(A4[0] / 2, 1 * cm, f"第 {doc.page} 页")
    canvas.restoreState()

doc = SimpleDocTemplate(..., onFirstPage=footer, onLaterPages=footer)
```

### 7. Build and verify

```python
doc.build(story)
```

After building, verify with pypdf:

```python
from pypdf import PdfReader
reader = PdfReader("output.pdf")
assert len(reader.pages) > 0, "empty PDF"
text = reader.pages[0].extract_text()
assert "<expected phrase>" in text, "content missing"
```

Never declare success without this check. Report the page count, file size, and
output path in the final message.

## Exam mode

When the user asks for an exam paper, quiz, or worksheet, follow these additions
on top of the core workflow. The most common failure is leaving too little
answer space for long-form questions — plan space *before* writing content, not
as an afterthought.

1. **Classify each question by type** before building the story:
   - Fill-in-blank / multiple-choice / true-false → no answer space needed.
   - Short answer (1–2 sentences) → leave 2–3 blank lines.
   - Long answer / problem-solving / proof / essay → leave **generous** space,
     at least 5–8 blank lines, more if the question asks for multiple steps.
2. **Quantify answer space per step**: a multi-step problem with 4 steps needs
   roughly 4 × (2–3 lines) = 8–12 blank lines, not 3 lines. When in doubt,
   over-allocate — a half-empty page is better than an unanswerable cramped one.
3. **Implement blank space in ReportLab**: use `Spacer(1, n * cm)` between the
   question text and the next question, or reserve a fixed-height empty `Table`
   cell. Never rely on `Paragraph` trailing newlines — they collapse.
4. **Let long questions flow to the next page**: use `KeepTogether` on the
   question *text* only, never on question + answer space, so the blank area can
   break across pages naturally.

## Resume mode

When the user asks for a resume/CV, follow these additions on top of the core
workflow:

1. **One page is a hard goal** for early-career roles; two pages only if content
   genuinely overflows after tightening.
2. **Layout**: name (H1) at top, followed by contact line, then sections: Summary,
   Skills, Experience, Projects, Education. Order by relevance to the target JD.
3. **Use a two-column table for Skills** to save space; single-column flow for
   everything else.
4. **Quantify achievements** (numbers, impact) — same standard as the project's
   resume guidelines. Do not pad skills with irrelevant tech stacks.
5. **Output location**: if the user's project convention places tailored resumes
   in a per-role subdirectory, write the PDF and the generation script into that
   subdirectory, not a shared folder (see project AGENTS.md if present).
6. ATS consideration: keep the file text-based (ReportLab produces extractable
   text); avoid relying on images or complex layout for critical content.

## Anti-patterns

- Hardcoding font paths instead of capturing `ensure_fonts.py` stdout.
- Using the default Helvetica for CJK text — renders as boxes.
- Using `drawString` for body paragraphs.
- Leaving `colWidths` unset on tables.
- Skipping the pypdf verification step.
- Setting margins or page size implicitly and not mentioning the choice.
