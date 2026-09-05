---
name: pdf-production
description: >
  PDF 生成与处理工具，三条生产线：Report（结构化文档）、Academic（学术论文/数学）、
  Process（已有 PDF 操作）。当用户想要"做一份报告/简历/合同/论文/试卷的 PDF"、
  "把 PDF 合并/拆分/提取/加水印/填表/转文字"、或任何"生成一个 PDF 文件"的需求时使用——
  即使用户没说 PDF 这个词。Also use for English requests about generating reports, papers,
  or manipulating PDFs. 支持中英文混排，内置免费可商用字体。
license: MIT
---

# PDF Production

A self-contained toolkit for generating and processing PDF documents, built entirely on
open-source libraries and open-licensed fonts. It organizes work into three production
lines and routes each request to the best one.

## Before anything: fonts

All three lines need Chinese + English fonts. They are **not bundled** in this skill to keep
the repository light — instead, fetch them on first use with the bundled helper:

```bash
python "<skill_dir>/scripts/ensure_fonts.py"
```

This downloads four families (Noto Serif SC, Noto Sans SC, Source Serif 4, Source Sans 3)
in Regular + Bold weights to a local cache and prints the cache directory. Never hardcode
font paths — always ask the helper for the location. See `references/fonts.md` for the full
font policy and why these families were chosen.

## Triage: how much to load

Before routing, judge task weight so you don't over-read on simple requests:

- **Light** — a named existing file plus one mechanical operation (extract, merge, split,
  rotate, metadata read). Load only `SKILL.md` + `briefs/process.md`. No font setup needed.
- **Standard** — anything that generates a document from scratch, or transforms content
  (reformat, redesign, convert with layout decisions). Load `SKILL.md`, `references/fonts.md`,
  `references/page-setup.md`, and the matched brief.

When in doubt, treat it as Standard — reading one extra reference is cheaper than
producing a PDF with wrong fonts or silent default margins.

## Routing

Read the user's request and pick exactly one production line:

| Line | For | Stack | Load |
|------|-----|-------|------|
| Process | Working with an existing PDF | pypdf + pdfplumber | `briefs/process.md` |
| Report | Structured documents: reports, proposals, resumes, contracts | ReportLab | `briefs/report.md` |
| Academic | Papers, theses, heavy math, slides | Tectonic (LaTeX) | `briefs/academic.md` |

### Quick decision guide

Match by intent first, keywords second. When several lines seem plausible, prefer the
one that matches the user's *output goal* rather than a single word in the request.

**Process** — the user already has a PDF and wants something done to it.

- Verbs: extract, merge, split, rotate, crop, encrypt, decrypt, watermark, fill, convert,
  compress, OCR, sign
- 中文动词: 提取, 合并, 拆分, 旋转, 裁剪, 加密, 解密, 水印, 填表, 转换, 压缩, 签字
- Signal: a named file plus one mechanical operation, no content authoring.

**Report** — structured text generated from scratch: multi-page, headings, paragraphs,
tables, page numbers.

- Nouns: report, proposal, contract, invoice, resume/CV, white paper, exam, worksheet,
  plan, receipt
- 中文名词: 报告, 分析, 提案, 合同, 简历, 发票, 收据, 白皮书, 试卷, 练习, 方案, 规划
- Signal: content outline provided or implied, formal business tone, tables of data.

**Academic** — scholarly or math-heavy output.

- Nouns: paper, thesis, dissertation, research, IEEE, ACM, Beamer, slides, algorithm,
  pseudocode
- 中文名词: 论文, 学术, 数学, 公式, 毕业论文, 开题报告, 学位论文, 研究, 幻灯片, 算法
- Signal: math notation, citations, strict formatting requirements, LaTeX already mentioned.

Ambiguous? Ask one short question or pick Report as the safe default for text documents.

Special rules:
- **CJK content**: never assume fonts exist; run the font helper first.
- **Emoji in content**: ReportLab and LaTeX render emoji poorly. Warn the user and suggest
  replacing emoji with words or embedded images instead.
- **Non-standard page sizes** (anything but A4/A3/Letter): define the size explicitly in
  ReportLab or LaTeX; never accept a library default silently.

## Cross-line quality rules

These apply to every line. The briefs expand on them with examples.

1. **Match the user's language.** A Chinese request produces a Chinese document.
2. **Respect explicit page or word counts** within ±20%. When unspecified, prefer completeness
   over brevity.
3. **Always set margins and page size explicitly.** Never trust a library default silently.
4. **Register the OFL fonts for every CJK document.** Rendering Chinese with a fallback font
   produces boxes or missing glyphs.
5. **Verify output before declaring done.** Run `scripts/verify.py` on the output — it is the
   authoritative quality check (page count, font embedding, CJK punctuation, tables, margins,
   metadata). Don't run a separate pypdf pre-check; verify.py already covers those basics.
   Use pypdf only when you need to assert a specific text string exists in the output. Report
   any warnings verify.py finds; don't silently skip them.
6. **Keep content substantial.** Before generating, re-read `references/content-depth.md` and
   make sure no section is starved, no paragraph is one line, and every list has a lead-in.

## Bundled resources

- `briefs/` — one file per production line with the full workflow.
- `references/fonts.md` — font policy, download table, registration snippets for each stack.
- `references/page-setup.md` — shared page size, margin, and grid conventions.
- `references/content-depth.md` — anti-shallow writing standards; read before generating any
  from-scratch document.
- `scripts/ensure_fonts.py` — idempotent font downloader (OFL fonts, local cache).
- `scripts/verify.py` — post-generation quality check (PyMuPDF engine, 11 checks: page
  structure, blank pages, font embedding, CJK punctuation, overflow, fill ratio, margin
  symmetry, tables, metadata, colors, TOC). Run it on every generated PDF before declaring
  success.
- `assets/` — optional template files; create as needed.

## Typical workflow

1. Route to a production line.
2. Run `scripts/ensure_fonts.py` if the document contains CJK text.
3. Read the matching brief and follow it.
4. Generate the PDF, then run `scripts/verify.py` before reporting success. (Reserve pypdf
   for asserting specific text strings, not as a general pre-check.)
5. Report the output path and any choices made (fonts, page size, stack).
