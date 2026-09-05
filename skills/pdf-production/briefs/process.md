# Process Line — Manipulate Existing PDFs

For operations on files that already exist: extract text/tables/images, merge, split,
rotate, crop, encrypt/decrypt, watermark, OCR scanned pages, fill forms, and convert
between PDF and other formats.

## Stack

- `pypdf` — structural operations (merge, split, rotate, encrypt, metadata)
- `pdfplumber` — content extraction (text, tables, layout-aware reading)
- Optional, install only when a task needs them:
  - `pdf2image` + `pytesseract` (+ Tesseract binary) — OCR
  - `pikepdf` — advanced watermark/repair when pypdf is insufficient
  - `libreoffice` CLI — Office↔PDF conversion

Check availability before use; install into the active environment if missing.

## Workflow

### 1. Inspect first

Before any operation, open the file and report what's inside:

```python
from pypdf import PdfReader
reader = PdfReader("input.pdf")
print(f"Pages: {len(reader.pages)}")
print(f"Encrypted: {reader.is_encrypted}")
print(f"Metadata: {reader.metadata}")
```

If `reader.is_encrypted` is true, ask the user for the password before proceeding.
Never try to brute-force.

### 2. Extract text

```python
from pypdf import PdfReader
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    print(f"--- Page {i+1} ---")
    print(text)
```

- Prefer `pdfplumber` when layout matters (columns, tables): `page.extract_text()`
  there is layout-aware and often cleaner for CJK documents.
- If `extract_text()` returns empty on all pages, the PDF is scanned → go to OCR.

### 3. Extract tables

```python
import pdfplumber
with pdfplumber.open("input.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        for j, table in enumerate(page.extract_tables()):
            print(f"Table {j+1} on page {i+1}:")
            for row in table:
                print(row)
```

Tables come back as nested lists with `None` for empty cells. Clean them before
presenting to the user (filter `None`, strip whitespace).

### 4. Extract images

`pypdf` does not reliably extract embedded images. Use `pdf2image` to rasterize pages
or `pdfimages` (poppler) when available. State the tool used in the report.

### 5. Merge

```python
from pypdf import PdfWriter, PdfReader
writer = PdfWriter()
for f in ["a.pdf", "b.pdf", "c.pdf"]:
    reader = PdfReader(f)
    for page in reader.pages:
        writer.add_page(page)
with open("merged.pdf", "wb") as out:
    writer.write(out)
```

Preserve the user's order. If the user names files loosely ("merge everything in this
folder"), sort alphabetically and say so.

### 6. Split

```python
from pypdf import PdfWriter, PdfReader
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1:03d}.pdf", "wb") as out:
        writer.write(out)
```

Support two modes: every page separately, or a page range (e.g. pages 1–5). Ask which
when the request is ambiguous.

### 7. Rotate / crop

```python
page.rotate(90)                    # clockwise degrees; negative for counterclockwise
page.mediabox = (l, b, r, t)        # crop to a rectangle in points
```

Confirm the direction — `rotate(90)` is clockwise, which surprises people who think
in printer terms.

### 8. Encrypt / decrypt

```python
writer.encrypt(user_password="user", owner_password="owner")
# decrypt:
reader.decrypt("password")
```

Report the passwords you used back to the user — they cannot be recovered later.

### 9. Watermark

Create a watermark page once and merge it onto every page:

```python
wm = PdfReader("watermark.pdf").pages[0]
for page in reader.pages:
    page.merge_page(wm)
```

Generate the watermark PDF itself with the Report line (see `report.md`) if it
contains Chinese text, so the OFL fonts are embedded correctly.

### 10. OCR (scanned PDFs)

Only when step 2 returns no text. Requires `pdf2image`, `pytesseract`, and the
Tesseract binary on PATH. Convert pages to images, OCR each, return plain text:

```python
from pdf2image import convert_from_path
import pytesseract
images = convert_from_path("scanned.pdf")
for i, img in enumerate(images):
    text = pytesseract.image_to_string(img, lang="chi_sim+eng")
    print(f"--- Page {i+1} ---")
    print(text)
```

Use `lang="chi_sim+eng"` for mixed Chinese-English documents. Warn the user that OCR
output contains errors and should be reviewed before reuse.

### 11. Fill forms

`pypdf` can fill AcroForm fields but has limits with some PDFs. Try:

```python
from pypdf import PdfReader, PdfWriter
reader = PdfReader("form.pdf")
fields = reader.get_fields()
# ... inspect field names, then:
writer = PdfWriter()
writer.append(reader)
writer.update_page_form_field_values(writer.pages[0], {"field_name": "value"})
```

If `get_fields()` returns `None` or the result is malformed, fall back to `pdf-lib`
(JavaScript) or tell the user the form isn't machine-fillable.

### 12. Convert formats

- **PDF → image**: `pdf2image.convert_from_path` (raster, lossless for text)
- **Office → PDF**: `libreoffice --headless --convert-to pdf file.docx` — requires
  LibreOffice installed; check with `libreoffice --version` first.
- **HTML → PDF**: this skill doesn't bundle an HTML engine; convert with `libreoffice --headless --convert-to pdf` for simple documents, or tell the user to print-to-PDF from a browser for rich layouts.

## Reporting

Every Process task ends by stating: input path(s), operation performed, output
path(s), and any limitations (e.g. "text extraction empty on page 3 — looks scanned").

## Anti-patterns

- Running OCR without first trying `extract_text()`.
- Assuming a PDF is unencrypted; check `is_encrypted` first.
- Merging without checking page order.
- Hardcoding passwords or leaving them in the output report.
- Re-encoding PDFs through a lossy pipeline when a structural operation would preserve
  quality.
