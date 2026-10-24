# The printable history book

`build_book.py` turns the site's own history/church content into a single
polished `.docx` — a printable book, not a site export. It's a small,
purpose-built converter (not a general Markdown/MyST tool), written to
handle exactly the syntax this project's content actually uses.

## Running it

```bash
source .venv/bin/activate        # same venv as the website
pip install -r requirements.txt  # installs python-docx/PyYAML/requests too
make book                        # or: python scripts/build_book.py
```

Output: `build/book/the-history-of-monkton.docx` (gitignored, like the rest
of `build/` — this is generated output, not something to commit).

Open it in Word, then press **Ctrl+A, F9** (or right-click the Contents
page and choose **Update Field**) once — that's a standard Word step for
any generated document and fills in the table of contents' page numbers.
Everything else (headings, images, tables, callout boxes, cross-links) is
ready as generated.

## What's included, and what isn't

The book covers the church and history sections, Places, Other Monktons,
and Credits — see `book_manifest.yaml` for the exact list. It deliberately
**excludes** the churchyard survey pages (survey-by-location,
numbered-stones, names-alphabetical, register-appendix) — together those
are a ~3,000-line genealogical reference database, not something that
reads as a book chapter. It also excludes project/navigation pages
(`about.md`, `index.md`).

## Adding new content

- **A new Terry Marsh instalment** (Monkton Memories or A Farming Life):
  nothing to do here. Those two parts are defined by `glob` in the
  manifest (`history/monkton-memories/[0-9]*.md`,
  `history/farming-life/[0-9]*.md`), sorted alphabetically — which sorts
  correctly by number because the files are zero-padded (`01-`, `02-`,
  ... `25-`). Add the new file the way you normally would for the site,
  and the next `make book` picks it up automatically.
- **A new page or section** (e.g. a new church page, or a whole new part
  of the book): add it to `book_manifest.yaml`, either as an explicit
  `sources:` list (for a one-off page, where order matters and won't
  change) or a `glob:` (for another numbered series).
- **Reordering or renaming parts**: edit the manifest directly — it's the
  single source of truth for the book's structure, independent of the
  site's own navigation.

## How the conversion works

`scripts/bookbuild/mdparse.py` parses each source file's MyST Markdown
into a list of block dicts (headings, paragraphs, lists, tables, callouts,
figures, quotes) — handling the specific directives this content uses
(`{admonition}`, `{note}`/`{tip}`/`{warning}`/`{important}`/`{seealso}`,
`{epigraph}`, `{figure}`; `{toctree}` is dropped). It is not a general MyST
parser — if a page starts using syntax it doesn't recognise, it falls back
to a plain paragraph rather than failing the build, but the output for
that bit will look plain rather than styled. Check `make book`'s output
and the result if you add something syntactically new (a grid card, a
dropdown, a table inside an admonition) to a page that's in scope for the
book.

`scripts/bookbuild/docxwrite.py` turns those blocks into the actual
`.docx`: a title page, a native Word table-of-contents field, a part
heading per manifest part (starting a fresh page), a chapter heading per
source file (also a fresh page, with a bookmark), styled callout boxes,
embedded images, and real tables. Links that point to another page
*included in the book* become clickable internal cross-references; links
to pages outside the book (e.g. a churchyard reference) or to local
files like the 1926 walk's PDF render as plain, unlinked text rather than
a broken link; external (`http`/`https`) links become ordinary clickable
hyperlinks.

## Caching

Only images are cached — in `build/.book-cache/images/`, keyed by URL, so
re-running the build doesn't re-download the same Cloudinary images every
time. That's the only genuinely slow step (a network call); parsing and
writing the ~1,850 lines of prose themselves take well under a second, so
there's no need for (and this doesn't do) per-chapter output caching —
the whole book rebuilds from scratch on every run, which is simpler and
has no staleness to reason about. Delete `build/.book-cache/` (or just
`build/`) to force every image to be re-downloaded.
