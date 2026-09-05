# Page setup conventions

Shared page size, margin, and grid conventions used across production lines.

## Standard sizes

| Name | mm | pt |
|------|-----|-----|
| A4 | 210 × 297 | 595 × 842 |
| Letter | 216 × 279 | 612 × 792 |
| A3 | 297 × 420 | 842 × 1191 |

ReportLab uses points internally (`1 inch = 72 pt`, `1 cm = 28.35 pt`).
Tectonic uses LaTeX geometry package values.

## Default margins (A4/Letter documents)

- Body text documents (reports, resumes): 2 cm all sides
- Formal documents (contracts, cover letters): 2.5 cm top/bottom, 2 cm sides
- Dense data documents (tables, invoices): 1.5 cm all sides

Adjust only with a reason. Wide margins on dense tables waste space; narrow
margins on prose hurt readability.

## Grid convention

A simple 12-column grid for layout math:

- Content width = page width − left margin − right margin
- Column width = content width ÷ 12
- Common spans: full = 12, two-thirds = 8, half = 6, third = 4, quarter = 3

ReportLab tables: set `colWidths` from these spans explicitly rather than
letting the library guess — explicit widths prevent overflow and keep columns
aligned across tables.

## Typography baseline

- Body text: 12 pt (Chinese) / 11.5 pt (Latin)
- Line height: 1.5× to 1.6× body size for CJK
- Heading scale: H1 20–22 pt, H2 16–18 pt, H3 14–15 pt
- Paragraph spacing: 6 pt after body paragraphs, 12 pt before headings

CJK text needs more line height than Latin; 1.5× is the floor, not a
suggestion — tight CJK lines look cramped and reduce readability.

## Non-standard sizes

Anything outside A4/Letter/A3 should be defined explicitly rather than left
to a library default. In ReportLab:

```python
from reportlab.lib.pagesizes import landscape, A4
page = landscape(A4)  # or a (width_pt, height_pt) tuple
```

Never silently accept a library default page size — state it in the output
report so the user knows what they got.
