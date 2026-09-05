"""Verify generated PDFs for common quality issues.

Comprehensive quality checker powered by PyMuPDF. Covers page structure, font
embedding, CJK typography rules, content overflow, fill ratio, margin symmetry,
table centering, metadata, color analysis, and TOC quality.

Works across all three production lines. Checks are independent — one failure
doesn't stop the others.

Usage:
    python verify.py document.pdf [--json]

Exit codes:
    0 = no errors
    1 = errors found
    2 = script failure (bad args, missing file)
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import pymupdf

# CJK punctuation that must not start a line (closing/joining marks)
LINE_START_FORBIDDEN = set("。、，；：！？）】」』》〉，")
# CJK punctuation that must not end a line (opening marks)
LINE_END_FORBIDDEN = set("（【《〈「")

# Minimum fill ratio per page (text/image/drawing coverage) before warning
MIN_FILL_RATIO = 0.15
# Margin asymmetry threshold in points before warning
MARGIN_ASYMMETRY_PT = 30


def _issue(level: str, check: str, msg: str) -> dict:
    return {"level": level, "check": check, "msg": msg}


def check_page_structure(doc) -> list:
    """Page count and size consistency."""
    issues = []
    if doc.page_count == 0:
        issues.append(_issue("error", "page_count", "PDF has no pages"))
        return issues

    sizes = set()
    for page in doc:
        r = page.rect
        sizes.add((round(r.width, 1), round(r.height, 1)))
    if len(sizes) > 1:
        issues.append(_issue("warning", "page_size", f"Mixed page sizes: {sorted(sizes)}"))
    return issues


def check_blank_pages(doc) -> list:
    """Pages with no text, no images, and no vector drawings."""
    blank = []
    for page in doc:
        has_text = bool(page.get_text().strip())
        has_images = bool(page.get_images())
        has_drawings = bool(page.get_drawings())
        if not has_text and not has_images and not has_drawings:
            blank.append(page.number + 1)
    if blank:
        return [_issue("warning", "blank_pages", f"Blank pages: {blank}")]
    return []


STANDARD_14 = {
    "helvetica", "helvetica-bold", "helvetica-oblique", "helvetica-boldoblique",
    "times-roman", "times-bold", "times-italic", "times-bolditalic",
    "courier", "courier-bold", "courier-oblique", "courier-boldoblique",
    "symbol", "zapfdingbats",
}


def check_fonts(doc) -> list:
    """Font embedding and family inventory.

    Embedding heuristic: subset-prefixed fonts (e.g. "AAAAAA+NotoSerifSC") are
    definitively embedded; standard 14 fonts need no embedding. Anything else
    without a subset prefix is flagged.
    """
    issues = []
    unembedded = set()
    families = set()
    for page in doc:
        for font in page.get_fonts(full=True):
            # full=True returns (xref, ext, type, basefont, name, encoding, ...)
            basefont = (font[3] or "").strip()
            if not basefont:
                continue
            normalized = basefont.strip("/").lower().rsplit("+", 1)[-1]
            families.add(basefont)
            has_subset_prefix = "+" in basefont
            if not has_subset_prefix and normalized not in STANDARD_14:
                unembedded.add(basefont)

    if families:
        issues.append(_issue("info", "fonts", f"Fonts ({len(families)}): {sorted(families)}"))
    if unembedded:
        issues.append(_issue(
            "error", "font_embedding",
            f"Non-embedded fonts ({len(unembedded)}): {sorted(unembedded)}",
        ))
    return issues


def check_cjk_punctuation(doc) -> list:
    """CJK line-start/end punctuation rules, with text context."""
    violations = []
    for page in doc:
        for line in page.get_text().split("\n"):
            s = line.strip()
            if len(s) < 2:
                continue
            first, last = s[0], s[-1]
            if first in LINE_START_FORBIDDEN:
                violations.append(f"p{page.number + 1} line-start '{first}': {s[:20]}…")
            elif last in LINE_END_FORBIDDEN:
                violations.append(f"p{page.number + 1} line-end '{last}': …{s[-20:]}")

    if violations:
        shown = violations[:8]
        more = f" …{len(violations) - 8} more" if len(violations) > 8 else ""
        return [_issue(
            "warning", "cjk_punctuation",
            f"CJK punctuation violations ({len(violations)}): " + " | ".join(shown) + more,
        )]
    return []


def check_overflow(doc) -> list:
    """Text blocks extending beyond page boundaries."""
    overflow_pages = []
    for page in doc:
        w, h = page.rect.width, page.rect.height
        for block in page.get_text("blocks"):
            x0, y0, x1, y1 = block[:4]
            if x1 > w + 1 or y1 > h + 1 or x0 < -1 or y0 < -1:
                overflow_pages.append(page.number + 1)
                break
    if overflow_pages:
        return [_issue(
            "warning", "content_overflow",
            f"Content exceeds page bounds on pages: {overflow_pages}",
        )]
    return []


def check_fill_ratio(doc) -> list:
    """Per-page content coverage; warn when sparse."""
    sparse = []
    for page in doc:
        w, h = page.rect.width, page.rect.height
        if w * h == 0:
            continue
        covered = 0.0
        for block in page.get_text("blocks"):
            x0, y0, x1, y1 = block[:4]
            covered += max(0, min(x1, w) - max(x0, 0)) * max(0, min(y1, h) - max(y0, 0))
        ratio = covered / (w * h)
        if ratio < MIN_FILL_RATIO:
            sparse.append((page.number + 1, round(ratio * 100, 1)))
    if sparse:
        return [_issue(
            "warning", "fill_ratio",
            f"Sparse pages (fill < {int(MIN_FILL_RATIO * 100)}%): "
            + ", ".join(f"p{n}={r}%" for n, r in sparse),
        )]
    return []


def check_margin_symmetry(doc) -> list:
    """Left/right text margin asymmetry (detects off-center layouts)."""
    violations = []
    for page in doc:
        blocks = page.get_text("blocks")
        if not blocks:
            continue
        w = page.rect.width
        left = min(b[0] for b in blocks)
        right = max(b[2] for b in blocks)
        l_margin, r_margin = left, w - right
        if abs(l_margin - r_margin) > MARGIN_ASYMMETRY_PT:
            violations.append(
                f"p{page.number + 1}: L={l_margin:.0f}pt, R={r_margin:.0f}pt "
                f"(diff {abs(l_margin - r_margin):.0f}pt)"
            )
    if violations:
        return [_issue(
            "warning", "margin_symmetry",
            "Asymmetric margins: " + "; ".join(violations[:5])
            + (f" …{len(violations) - 5} more" if len(violations) > 5 else ""),
        )]
    return []


def check_tables(doc) -> list:
    """Table detection and centering check."""
    table_count = 0
    off_center = []
    for page in doc:
        try:
            tabs = page.find_tables()
        except Exception:
            continue
        for tab in tabs.tables:
            table_count += 1
            if page.rect.width > 0:
                bbox = tab.bbox
                l_margin = bbox[0]
                r_margin = page.rect.width - bbox[2]
                if abs(l_margin - r_margin) > MARGIN_ASYMMETRY_PT:
                    off_center.append(page.number + 1)
    issues = []
    if table_count:
        issues.append(_issue("info", "tables", f"Detected {table_count} table(s)"))
    if off_center:
        issues.append(_issue(
            "warning", "table_centering",
            f"Off-center tables on pages: {sorted(set(off_center))}",
        ))
    return issues


def check_metadata(doc) -> list:
    """Title/author/creator metadata presence."""
    issues = []
    meta = doc.metadata or {}
    for key in ("title", "author", "creator", "subject"):
        if not meta.get(key):
            issues.append(_issue("info", "metadata", f"Missing metadata: {key}"))
    return issues


def check_colors(doc) -> list:
    """Informational color inventory from text spans."""
    colors = Counter()
    for page in doc:
        d = page.get_text("dict")
        for block in d.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    color = span.get("color")
                    if color:
                        colors[color] += 1
    issues = []
    if colors:
        top = [f"#{c:06x}({n})" for c, n in colors.most_common(8)]
        issues.append(_issue("info", "colors", f"Text colors (top {len(top)}): " + ", ".join(top)))
    return issues


def check_toc(doc) -> list:
    """Detect an empty or placeholder table of contents."""
    issues = []
    toc = doc.get_toc()
    if not toc:
        return issues  # no TOC is fine for most documents
    # Check the page most likely to hold the TOC (first TOC target page)
    try:
        first_toc_page = min(t[2] for t in toc) - 1
    except (ValueError, TypeError):
        return issues
    if 0 <= first_toc_page < doc.page_count:
        text = doc[first_toc_page].get_text().strip()
        if len(text) < 40:
            issues.append(_issue(
                "warning", "toc_placeholder",
                f"TOC on page {first_toc_page + 1} appears empty or placeholder",
            ))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a generated PDF (PyMuPDF)")
    parser.add_argument("pdf", help="Path to the PDF")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    path = Path(args.pdf)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2

    try:
        doc = pymupdf.open(str(path))
    except Exception as e:
        print(f"Error: cannot open PDF: {e}", file=sys.stderr)
        return 2

    if doc.needs_pass:
        print("Error: PDF is encrypted — decrypt before verifying", file=sys.stderr)
        doc.close()
        return 2

    page_count = doc.page_count

    checks = []
    checks += check_page_structure(doc)
    checks += check_blank_pages(doc)
    checks += check_fonts(doc)
    checks += check_cjk_punctuation(doc)
    checks += check_overflow(doc)
    checks += check_fill_ratio(doc)
    checks += check_margin_symmetry(doc)
    checks += check_tables(doc)
    checks += check_metadata(doc)
    checks += check_colors(doc)
    checks += check_toc(doc)
    doc.close()

    errors = [c for c in checks if c["level"] == "error"]
    warnings = [c for c in checks if c["level"] == "warning"]
    infos = [c for c in checks if c["level"] == "info"]

    if args.json:
        result = {
            "file": str(path),
            "pages": page_count,
            "errors": errors,
            "warnings": warnings,
            "info": infos,
            "summary": f"{len(errors)} error(s), {len(warnings)} warning(s), {len(infos)} info",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Verified: {path}")
        print(f"Pages: {page_count}")
        if errors:
            print("\nERRORS:")
            for e in errors:
                print(f"  [error] {e['msg']}")
        if warnings:
            print("\nWARNINGS:")
            for w in warnings:
                print(f"  [warn]  {w['msg']}")
        if infos:
            print("\nINFO:")
            for i in infos:
                print(f"  [info]  {i['msg']}")
        print(f"\nSummary: {len(errors)} error(s), {len(warnings)} warning(s), {len(infos)} info")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
