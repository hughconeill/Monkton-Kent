"""Render parsed blocks (see mdparse.py) into a polished python-docx Document."""

import hashlib
import os
import posixpath

import requests
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor, Twips

BRAND_BLUE = RGBColor(0x25, 0x63, 0xEB)  # matches the site's brand-primary colour
GREY = RGBColor(0x55, 0x55, 0x55)
CALLOUT_FILL = "EAF2FF"


# ---------------------------------------------------------------------------
# Document setup
# ---------------------------------------------------------------------------

def new_document():
    doc = Document()

    section = doc.sections[0]
    section.page_height, section.page_width = Inches(11.69), Inches(8.27)  # A4
    for attr in ("top_margin", "bottom_margin"):
        setattr(section, attr, Inches(1))
    for attr in ("left_margin", "right_margin"):
        setattr(section, attr, Inches(1.1))

    styles = doc.styles

    normal = styles["Normal"]
    normal.font.name = "Georgia"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(8)
    normal.paragraph_format.line_spacing = 1.15

    for level, size in ((1, 24), (2, 18), (3, 14), (4, 12)):
        h = styles[f"Heading {level}"]
        h.font.name = "Georgia"
        h.font.bold = True
        h.font.size = Pt(size)
        h.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
        h.paragraph_format.space_before = Pt(18 if level <= 2 else 12)
        h.paragraph_format.space_after = Pt(8)

    # Pin the font on every style we use: Word's built-in heading styles take
    # their font from the document theme, which LibreOffice substitutes.
    for name in ("Normal", "Heading 1", "Heading 2", "Heading 3", "Heading 4", "Title",
                 "List Bullet", "Header", "Footer", "Caption"):
        try:
            _pin_font(styles[name], "Georgia")
        except KeyError:
            pass
    for name in ("Header", "Footer"):
        try:
            styles[name].font.size = Pt(9)
            styles[name].font.color.rgb = GREY
        except KeyError:
            pass

    if "Byline" not in [s.name for s in styles]:
        byline = styles.add_style("Byline", styles["Normal"].type)
        byline.base_style = normal
        byline.font.italic = True
        byline.font.size = Pt(10)
        byline.font.color.rgb = GREY

    if "Caption" not in [s.name for s in styles]:
        styles.add_style("Caption", styles["Normal"].type)
    cap = styles["Caption"]
    cap.base_style = normal
    cap.font.bold = False
    cap.font.italic = True
    cap.font.size = Pt(9.5)
    cap.font.color.rgb = GREY

    return doc


def _pin_font(style, name):
    style.font.name = name
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rfonts.get(qn(attr)) is not None:
            del rfonts.attrib[qn(attr)]
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(attr), name)


def add_title_page(doc, volume, cover_image_path, version):
    """Volume title page: crest, title, subtitle, volume number, version."""
    for _ in range(3):
        doc.add_paragraph()
    if cover_image_path and os.path.exists(cover_image_path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(cover_image_path, width=Inches(1.6))
        doc.add_paragraph()

    if volume.get("series"):
        s = doc.add_paragraph()
        s.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = s.add_run(volume["series"].upper())
        r.font.size = Pt(11)
        r.font.color.rgb = BRAND_BLUE
        r.bold = True

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(volume.get("title", "Untitled"))
    run.font.size = Pt(32)
    run.font.bold = True
    run.font.name = "Georgia"

    if volume.get("subtitle"):
        sub = doc.add_paragraph()
        sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = sub.add_run(volume["subtitle"])
        r.font.size = Pt(16)
        r.font.color.rgb = GREY
        r.font.name = "Georgia"

    for _ in range(7):
        doc.add_paragraph()

    for line, size in ((version, 11), (volume.get("site_url", ""), 10)):
        if not line:
            continue
        foot = doc.add_paragraph()
        foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
        foot.paragraph_format.space_after = Pt(2)
        r = foot.add_run(line)
        r.font.size = Pt(size)
        r.font.color.rgb = GREY
        r.italic = True

    doc.add_page_break()


def add_front_matter(doc, sections, link_targets, render_md):
    """'About this volume' page(s): disclaimer, credits summary, how to help.

    `sections` is a list of {"heading": str, "text": markdown str} from the
    manifest; `render_md` renders a markdown string into the document.
    """
    for sec in sections:
        h = doc.add_paragraph()
        r = h.add_run(sec["heading"])
        r.bold = True
        r.font.size = Pt(14)
        r.font.color.rgb = BRAND_BLUE
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.keep_with_next = True
        render_md(sec["text"])
    doc.add_page_break()


def add_toc(doc):
    # Deliberately not a Heading style, so "Contents" doesn't list itself.
    heading = doc.add_paragraph()
    r = heading.add_run("Contents")
    r.bold = True
    r.font.size = Pt(24)
    r.font.name = "Georgia"
    heading.paragraph_format.space_after = Pt(12)

    p = doc.add_paragraph()
    run = p.add_run()
    fld_char_begin = OxmlElement("w:fldChar")
    fld_char_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-2" \\h \\z \\u'
    fld_char_sep = OxmlElement("w:fldChar")
    fld_char_sep.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "Right-click and choose “Update Field” to generate the contents."
    fld_char_end = OxmlElement("w:fldChar")
    fld_char_end.set(qn("w:fldCharType"), "end")

    r_element = run._r
    r_element.append(fld_char_begin)
    r_element.append(instr)
    r_element.append(fld_char_sep)
    r_element.append(placeholder)
    r_element.append(fld_char_end)

    doc.add_page_break()


def add_header_footer(doc, title, version):
    """Header: the volume's name. Footer: version, and "Page X of Y".

    The title page (first page) has neither.
    """
    section = doc.sections[-1]
    section.different_first_page_header_footer = True
    # explicit, empty first-page header/footer (LibreOffice otherwise falls
    # back to the default ones on the title page)
    section.first_page_header.is_linked_to_previous = False
    section.first_page_footer.is_linked_to_previous = False
    section.first_page_header.paragraphs[0].text = ""
    section.first_page_footer.paragraphs[0].text = ""

    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    # right-aligned tab stop at the text width, for the page number
    text_width = section.page_width - section.left_margin - section.right_margin
    tabs = fp.paragraph_format.tab_stops
    for pos in (4680, 9360):  # the Footer style's built-in tabs, in twips
        tabs.add_tab_stop(Twips(pos), WD_TAB_ALIGNMENT.CLEAR)
    tabs.add_tab_stop(text_width, WD_TAB_ALIGNMENT.RIGHT)
    _grey_run(fp, version + "\t")
    _grey_run(fp, "Page ")
    _add_field(fp, "PAGE")
    _grey_run(fp, " of ")
    _add_field(fp, "NUMPAGES")

    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = hp.add_run(title)
    r.font.size = Pt(9)
    r.font.color.rgb = GREY
    r.italic = True


def _grey_run(paragraph, text):
    r = paragraph.add_run(text)
    r.font.size = Pt(9)
    r.font.color.rgb = GREY
    return r


def _add_field(paragraph, instr_text):
    run = paragraph.add_run()
    for kind, text in (("begin", None), ("instr", instr_text), ("separate", None),
                       ("text", "1"), ("end", None)):
        if kind == "instr":
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
        elif kind == "text":
            el = OxmlElement("w:t")
            el.text = text
        else:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
        run._r.append(el)
    run.font.size = Pt(9)
    run.font.color.rgb = GREY


def add_part_heading(doc, title, subtitle=None):
    doc.add_page_break()
    doc.add_heading(title, level=1)
    if subtitle:
        p = doc.add_paragraph()
        r = p.add_run(subtitle)
        r.italic = True
        r.font.color.rgb = GREY
        p.paragraph_format.space_after = Pt(16)


# ---------------------------------------------------------------------------
# Block rendering
# ---------------------------------------------------------------------------

def render_blocks(doc, blocks, *, level_offset, link_targets, current_dir, image_cache_dir,
                   chapter_bookmark=None, page_break_before_chapter=True, source_dir):
    first_heading = True
    i = 0
    while i < len(blocks):
        block = blocks[i]
        t = block["type"]
        i += 1

        if t == "figure" and block.get("thumb"):
            # gather this run of consecutive thumbnails into one row/grid
            group = [block]
            while i < len(blocks) and blocks[i]["type"] == "figure" and blocks[i].get("thumb"):
                group.append(blocks[i])
                i += 1
            _render_thumbnails(doc, group, current_dir, image_cache_dir, source_dir)
            continue

        if t == "heading":
            level = min(block["level"] + level_offset, 4)
            if first_heading and page_break_before_chapter:
                doc.add_page_break()
            h = doc.add_heading(level=level)
            if first_heading and chapter_bookmark:
                _start_bookmark(h, chapter_bookmark)
            add_runs(h, block["runs"], link_targets, current_dir)
            if first_heading and chapter_bookmark:
                _end_bookmark(h)
            first_heading = False

        elif t == "para":
            p = doc.add_paragraph()
            add_runs(p, block["runs"], link_targets, current_dir)
            _style_if_byline(p)

        elif t == "list":
            for item in block["items"]:
                if block["ordered"] and item["marker"]:
                    # explicit reference numbers (e.g. tablet/plot numbers,
                    # not necessarily sequential) - kept as literal text
                    # rather than handed to Word's auto-numbering.
                    p = doc.add_paragraph()
                    p.paragraph_format.left_indent = Inches(0.25)
                    r = p.add_run(item["marker"] + " ")
                    r.bold = True
                else:
                    p = doc.add_paragraph(style="List Bullet")
                add_runs(p, item["runs"], link_targets, current_dir)

        elif t == "table":
            _render_table(doc, block)

        elif t == "callout":
            _render_callout(doc, block, level_offset, link_targets, current_dir, image_cache_dir, source_dir)

        elif t == "quote":
            for inner in block["blocks"]:
                if inner["type"] == "para":
                    p = doc.add_paragraph()
                    p.paragraph_format.left_indent = Inches(0.4)
                    add_runs(p, inner["runs"], link_targets, current_dir, force_italic=True)

        elif t == "figure":
            _render_figure(doc, block, current_dir, image_cache_dir, source_dir)


def _style_if_byline(paragraph):
    text = paragraph.text.strip()
    if text.startswith("*") is False and len(paragraph.runs) == 1 and paragraph.runs[0].italic and not paragraph.runs[0].bold:
        # A lone italicised line (byline, e.g. "*Terry Marsh*") - style smaller/grey.
        for r in paragraph.runs:
            r.font.color.rgb = GREY
            r.font.size = Pt(10)
    if text.startswith("Originally published in the Monkton News"):
        for r in paragraph.runs:
            r.font.size = Pt(9.5)
            r.font.color.rgb = GREY


def _render_table(doc, block):
    n_cols = len(block["header"])
    table = doc.add_table(rows=1, cols=n_cols)
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # Repeat the header row at the top of every page the table spans - the
    # churchyard reference tables run to hundreds of rows / many pages.
    trPr = table.rows[0]._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    trPr.append(tbl_header)
    hdr_cells = table.rows[0].cells
    for cell, runs in zip(hdr_cells, block["header"]):
        p = cell.paragraphs[0]
        for run in runs:
            r = p.add_run(run["text"])
            r.bold = True
    for row in block["rows"]:
        new_row = table.add_row()
        # Keep each row on one page rather than splitting it across a break.
        new_row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        cells = new_row.cells
        for cell, runs in zip(cells, row):
            p = cell.paragraphs[0]
            for run in runs:
                r = p.add_run(run["text"])
                r.bold = run["bold"]
                r.italic = run["italic"]
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def _render_callout(doc, block, level_offset, link_targets, current_dir, image_cache_dir, source_dir):
    table = doc.add_table(rows=1, cols=1)
    table.autofit = True
    cell = table.rows[0].cells[0]
    _shade_cell(cell, CALLOUT_FILL)
    cell.paragraphs[0].text = ""
    title_p = cell.paragraphs[0]
    r = title_p.add_run(block["title"])
    r.bold = True
    r.font.color.rgb = BRAND_BLUE

    for inner in block["blocks"]:
        if inner["type"] == "para":
            p = cell.add_paragraph()
            add_runs(p, inner["runs"], link_targets, current_dir)
        elif inner["type"] == "list":
            for item in inner["items"]:
                p = cell.add_paragraph(style="List Bullet")
                add_runs(p, item["runs"], link_targets, current_dir)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def _shade_cell(cell, hex_fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hex_fill)
    tc_pr.append(shd)


def _render_figure(doc, block, current_dir, image_cache_dir, source_dir):
    local_path = resolve_image(block["src"], current_dir, image_cache_dir, source_dir)
    if local_path and os.path.exists(local_path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        try:
            p.add_run().add_picture(local_path, width=Inches(5.5))
        except Exception:
            pass
    if block["caption_runs"]:
        cap = doc.add_paragraph(style="Caption")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_runs(cap, block["caption_runs"], {}, current_dir)


THUMB_COLS = 3
THUMB_WIDTH = Inches(1.85)


def _render_thumbnails(doc, figures, current_dir, image_cache_dir, source_dir):
    """Small photos (site `photo-thumb` figures) as a borderless grid, 3 across."""
    rows = (len(figures) + THUMB_COLS - 1) // THUMB_COLS
    table = doc.add_table(rows=rows, cols=THUMB_COLS)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for n, fig in enumerate(figures):
        cell = table.rows[n // THUMB_COLS].cells[n % THUMB_COLS]
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True
        local_path = resolve_image(fig["src"], current_dir, image_cache_dir, source_dir)
        if local_path and os.path.exists(local_path):
            try:
                p.add_run().add_picture(local_path, width=THUMB_WIDTH)
            except Exception:
                pass
        if fig["caption_runs"]:
            cap = cell.add_paragraph(style="Caption")
            cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
            cap.paragraph_format.space_after = Pt(6)
            add_runs(cap, fig["caption_runs"], {}, current_dir)
    for row in table.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


# ---------------------------------------------------------------------------
# Runs, links, bookmarks
# ---------------------------------------------------------------------------

def add_runs(paragraph, runs, link_targets, current_dir, force_italic=False):
    for run in runs:
        if not run["text"]:
            continue
        link = run["link"]
        if link:
            kind, target = resolve_link(link, current_dir, link_targets)
        else:
            kind, target = None, None

        if kind == "internal":
            _add_internal_hyperlink(paragraph, run["text"], target, run, force_italic)
        elif kind == "external":
            _add_external_hyperlink(paragraph, run["text"], target, run, force_italic)
        else:
            # "\n" in run text is a hard line break (see mdparse's handling
            # of lines ending in a backslash)
            parts = run["text"].split("\n")
            for part in parts[:-1]:
                r = paragraph.add_run(part)
                r.bold = run["bold"]
                r.italic = run["italic"] or force_italic
                r.add_break()
            r = paragraph.add_run(parts[-1])
            r.bold = run["bold"]
            r.italic = run["italic"] or force_italic
            if run["sup"]:
                r.font.superscript = True
            if run["code"]:
                r.font.name = "Consolas"


# Base URL of the live site. Links to pages that aren't in the volume being
# built (e.g. from the war memorial to the churchyard survey in another
# volume, or to the gallery) point here instead of being dropped.
SITE_BASE = "https://monkton-kent.uk/"


def resolve_link(url, current_dir, link_targets):
    if url.startswith(("http://", "https://", "mailto:")):
        return "external", url
    # normalise a relative markdown link to a source/-rooted posix path
    path, _, frag = url.partition("#")
    joined = posixpath.normpath(posixpath.join(current_dir, path))
    if joined in link_targets:
        return "internal", link_targets[joined]
    if SITE_BASE and not joined.startswith(".."):
        if joined.endswith(".md"):
            web = joined[:-3] + ".html"
            return "external", SITE_BASE + web + (f"#{frag}" if frag else "")
        if joined.startswith("_static/"):
            return "external", SITE_BASE + joined
    return "plain", None


def _add_external_hyperlink(paragraph, text, url, run, force_italic):
    part = paragraph.part
    r_id = part.relate_to(
        url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    new_run = _styled_run_element(text, run, force_italic, color="2563EB", underline=True)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)


def _add_internal_hyperlink(paragraph, text, bookmark_name, run, force_italic):
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("w:anchor"), bookmark_name)
    new_run = _styled_run_element(text, run, force_italic, color="2563EB", underline=True)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)


def _styled_run_element(text, run, force_italic, color=None, underline=False):
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    if run["bold"]:
        rpr.append(OxmlElement("w:b"))
    if run["italic"] or force_italic:
        rpr.append(OxmlElement("w:i"))
    if underline:
        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single")
        rpr.append(u)
    if color:
        c = OxmlElement("w:color")
        c.set(qn("w:val"), color)
        rpr.append(c)
    if run["sup"]:
        vert = OxmlElement("w:vertAlign")
        vert.set(qn("w:val"), "superscript")
        rpr.append(vert)
    r.append(rpr)
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    return r


_bookmark_id = [0]


def _start_bookmark(paragraph, name):
    _bookmark_id[0] += 1
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(_bookmark_id[0]))
    start.set(qn("w:name"), name)
    # w:pPr, if present, must stay the first child of w:p - insert just after it.
    p_el = paragraph._p
    ppr = p_el.find(qn("w:pPr"))
    insert_at = 1 if ppr is not None else 0
    p_el.insert(insert_at, start)
    paragraph._bookmark_id = _bookmark_id[0]


def _end_bookmark(paragraph):
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(getattr(paragraph, "_bookmark_id", _bookmark_id[0])))
    paragraph._p.append(end)


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------

def resolve_image(src, current_dir, image_cache_dir, source_dir):
    if src.startswith(("http://", "https://")):
        return download_cached(src, image_cache_dir)
    path = os.path.normpath(os.path.join(source_dir, current_dir, src))
    return path


def download_cached(url, image_cache_dir):
    os.makedirs(image_cache_dir, exist_ok=True)
    ext = os.path.splitext(url.split("?")[0])[1] or ".img"
    digest = hashlib.sha256(url.encode()).hexdigest()[:24]
    cache_path = os.path.join(image_cache_dir, digest + ext)
    if os.path.exists(cache_path):
        return cache_path
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        with open(cache_path, "wb") as f:
            f.write(resp.content)
        return cache_path
    except Exception as exc:
        print(f"  ! image download failed, skipping: {url} ({exc})")
        return None
