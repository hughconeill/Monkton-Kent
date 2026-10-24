"""A small, purpose-built Markdown/MyST parser for this project's book content.

This is deliberately NOT a general MyST parser. It understands exactly the
subset of syntax actually used in the site's history/church pages (checked
by hand when this was written): ATX headings, bold/italic, inline links,
<sup> tags, backslash-escapes, pipe tables, bullet and explicitly-numbered
lists, and the directives {admonition}/{note}/{tip}/{warning}/{important}/
{seealso}/{epigraph}/{figure}/{toctree}. Anything else falls back to a plain
paragraph rather than crashing — "good enough to not break the build" beats
"perfectly general" for a converter with one corpus to serve.

Output is a list of block dicts (see module docstring sections below for
shapes); scripts/bookbuild/docxwrite.py turns those into a python-docx
document. Keeping this as plain dicts (not a parser-specific class) made the
two stages easy to develop and test independently.
"""

import re

# ---------------------------------------------------------------------------
# Inline parsing: markdown text -> list of "runs"
# {"text": str, "bold": bool, "italic": bool, "sup": bool, "code": bool,
#  "link": str|None}
# ---------------------------------------------------------------------------

_INLINE_TOKEN = re.compile(
    r"""(?P<esc>\\[\\`*_\[\]()#+\-.!{}])
      | (?P<sup_open><sup>)
      | (?P<sup_close></sup>)
      | (?P<bold>\*\*)
      | (?P<code>`)
      | (?P<link>\[(?P<linktext>[^\]]*)\]\((?P<linkurl>[^)]+)\))
      | (?P<italic>\*)
    """,
    re.VERBOSE,
)


def parse_inline(text):
    """Turn one line/paragraph of markdown into a list of styled runs."""
    runs = []
    bold = italic = sup = code = False
    buf = []

    def flush():
        if buf:
            runs.append(
                {
                    "text": "".join(buf),
                    "bold": bold,
                    "italic": italic,
                    "sup": sup,
                    "code": code,
                    "link": None,
                }
            )
            buf.clear()

    pos = 0
    for m in _INLINE_TOKEN.finditer(text):
        if m.start() > pos:
            buf.append(text[pos : m.start()])
        pos = m.end()

        if m.group("esc"):
            buf.append(m.group("esc")[1])
        elif m.group("sup_open"):
            flush()
            sup = True
        elif m.group("sup_close"):
            flush()
            sup = False
        elif m.group("bold"):
            flush()
            bold = not bold
        elif m.group("code"):
            flush()
            code = not code
        elif m.group("link"):
            flush()
            runs.append(
                {
                    "text": m.group("linktext"),
                    "bold": bold,
                    "italic": italic,
                    "sup": sup,
                    "code": code,
                    "link": m.group("linkurl").strip(),
                }
            )
        elif m.group("italic"):
            flush()
            italic = not italic

    if pos < len(text):
        buf.append(text[pos:])
    flush()
    return runs


def runs_plain_text(runs):
    return "".join(r["text"] for r in runs)


# ---------------------------------------------------------------------------
# Block parsing
# ---------------------------------------------------------------------------

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_TABLE_ROW = re.compile(r"^\|(.+)\|\s*$")
_TABLE_SEP = re.compile(r"^\|?[\s:|-]+\|?$")
_BULLET = re.compile(r"^(\s*)-\s+(.*)$")
_NUMBERED = re.compile(r"^(\s*)(\d+(?:\.\d+)?)\.\s+(.*)$")
_FENCE_OPEN = re.compile(r"^```\{(\w+)\}\s*(.*)$")
_ATTRS_BLOCK = re.compile(r"^\{\.[\w-]+\}\s*$")
_OPTION = re.compile(r"^:(\w+):\s*(.*)$")


def _split_table_row(line):
    inner = line.strip()[1:-1] if line.strip().endswith("|") else line.strip()[1:]
    cells = []
    cell = []
    escaped = False
    for ch in inner:
        if escaped:
            cell.append(ch)
            escaped = False
        elif ch == "\\":
            cell.append(ch)
            escaped = True
        elif ch == "|":
            cells.append("".join(cell).strip())
            cell = []
        else:
            cell.append(ch)
    cells.append("".join(cell).strip())
    return cells


def parse_markdown(text):
    """Parse a whole file's markdown content into a list of block dicts."""
    lines = text.replace("\r\n", "\n").split("\n")
    blocks = []
    i = 0
    n = len(lines)

    def peek(offset=0):
        j = i + offset
        return lines[j] if 0 <= j < n else None

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if _ATTRS_BLOCK.match(stripped):
            i += 1
            continue

        m = _HEADING.match(stripped)
        if m:
            blocks.append(
                {"type": "heading", "level": len(m.group(1)), "runs": parse_inline(m.group(2).strip())}
            )
            i += 1
            continue

        fence = _FENCE_OPEN.match(stripped)
        if fence:
            name, title = fence.group(1), fence.group(2).strip()
            body_lines = []
            i += 1
            while i < n and lines[i].strip() != "```":
                body_lines.append(lines[i])
                i += 1
            i += 1  # consume closing fence
            block = _parse_directive(name, title, body_lines)
            if block is not None:
                blocks.append(block)
            continue

        if _TABLE_ROW.match(stripped) and peek(1) and _TABLE_SEP.match(peek(1).strip()):
            header = _split_table_row(stripped)
            i += 2  # header + separator
            rows = []
            while i < n and _TABLE_ROW.match(lines[i].strip()):
                rows.append(_split_table_row(lines[i].strip()))
                i += 1
            blocks.append(
                {
                    "type": "table",
                    "header": [parse_inline(c) for c in header],
                    "rows": [[parse_inline(c) for c in r] for r in rows],
                }
            )
            continue

        if _BULLET.match(line) or _NUMBERED.match(line):
            items = []
            ordered = bool(_NUMBERED.match(line))
            while i < n:
                cur = lines[i]
                bm = _BULLET.match(cur)
                nm = _NUMBERED.match(cur)
                if not bm and not nm:
                    break
                marker = nm.group(2) + "." if nm else None
                text_part = (nm.group(3) if nm else bm.group(2)).rstrip()
                i += 1
                # soft-wrapped continuation lines: indented, non-blank,
                # not themselves a new list item
                while (
                    i < n
                    and lines[i].strip()
                    and not _BULLET.match(lines[i])
                    and not _NUMBERED.match(lines[i])
                    and (len(lines[i]) - len(lines[i].lstrip())) >= 2
                ):
                    text_part += " " + lines[i].strip()
                    i += 1
                items.append({"marker": marker, "runs": parse_inline(text_part)})
            blocks.append({"type": "list", "ordered": ordered, "items": items})
            continue

        # plain paragraph: gather soft-wrapped lines until blank/structural line
        para_lines = [stripped]
        i += 1
        while i < n and lines[i].strip() and not _is_structural(lines[i]):
            para_lines.append(lines[i].strip())
            i += 1
        blocks.append({"type": "para", "runs": parse_inline(" ".join(para_lines))})

    return blocks


def _is_structural(line):
    s = line.strip()
    return bool(
        _HEADING.match(s)
        or _FENCE_OPEN.match(s)
        or _BULLET.match(line)
        or _NUMBERED.match(line)
        or _TABLE_ROW.match(s)
        or _ATTRS_BLOCK.match(s)
    )


def _parse_directive(name, title, body_lines):
    # strip leading :option: value lines (and one blank line after them)
    content = list(body_lines)
    while content and (_OPTION.match(content[0].strip()) or not content[0].strip()):
        if _OPTION.match(content[0].strip()):
            content.pop(0)
        elif content and not content[0].strip():
            content.pop(0)
        else:
            break
    # re-trim any now-leading blank lines
    while content and not content[0].strip():
        content.pop(0)
    while content and not content[-1].strip():
        content.pop()

    if name == "toctree":
        return None

    if name == "figure":
        # the image path is on the opening fence line: ```{figure} <path>
        src = title.strip()
        alt = ""
        for l in body_lines:
            om = _OPTION.match(l.strip())
            if om and om.group(1) == "alt":
                alt = om.group(2)
        caption_text = " ".join(l.strip() for l in content if l.strip())
        return {
            "type": "figure",
            "src": src,
            "alt": alt,
            "caption_runs": parse_inline(caption_text) if caption_text else [],
        }

    if name == "epigraph":
        inner = parse_markdown("\n".join(body_lines))
        return {"type": "quote", "blocks": inner}

    if name in ("admonition", "note", "tip", "warning", "important", "seealso", "danger", "attention"):
        default_titles = {
            "note": "Note",
            "tip": "Tip",
            "warning": "Warning",
            "important": "Important",
            "seealso": "See also",
            "danger": "Danger",
            "attention": "Attention",
        }
        callout_title = title if (name == "admonition" and title) else default_titles.get(name, "Note")
        inner = parse_markdown("\n".join(content))
        return {"type": "callout", "title": callout_title, "blocks": inner}

    # unknown directive: best-effort render its content as plain blocks
    return {"type": "callout", "title": title or name.title(), "blocks": parse_markdown("\n".join(content))}
