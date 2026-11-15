# The printable volumes (PDF downloads)

`build_book.py` turns the site's own content into three printable A4
volumes, offered on the site's Downloads page (`source/downloads.md`):

| Volume id | Volume | Contents |
|---|---|---|
| `church` | The Church of St Mary Magdalene | the church pages, then the churchyard survey as a reference section |
| `stuart` | Monkton: A Folk History, by Stuart Horsburgh | Stuart's Research |
| `terry` | Monkton Memories & A Farming Life, by Terry Marsh | both Monkton News columns |

Every volume gets a title page (crest, title, version), an "About this
volume" page (purpose, the volume's own credit line, notes on accuracy,
privacy and copyright, contact), a contents page with page numbers, the
chapters, and the site's Credits page at the back. Each page has the
volume's name in the header and the version plus "Page X of Y" in the
footer. Small photos from the site (`:figclass: photo-thumb` figures) are
laid out three to a row; larger figures (e.g. the zone maps) are full width.

It's a small, purpose-built converter (not a general Markdown/MyST tool),
written to handle exactly the syntax this project's content actually uses.
It builds a polished `.docx` per volume, then has LibreOffice fill in the
contents page and export it to PDF.

## Running it

```bash
source .venv/bin/activate        # same venv as the website
pip install -r requirements.txt  # installs python-docx/PyYAML/requests/pypdf too
make book                        # or: python scripts/build_book.py
python scripts/build_book.py --volume terry   # just one volume (repeatable)
python scripts/build_book.py --no-pdf         # .docx only, no LibreOffice needed
```

Output:

- `source/_static/downloads/*.pdf` — the PDFs. **These are committed**: the
  GitHub Actions deploy can't run LibreOffice, so the site serves whatever
  PDFs are in the repo. Rebuild and commit them when you release a new
  version (they're about 7 MB together, so don't rebuild them for every
  typo fix).
- `source/downloads.md` — the table between the `volumes:start` /
  `volumes:end` markers is rewritten with each volume's description, page
  count and file size. Don't edit inside the markers by hand; edit the
  volume `description` in the manifest instead.
- `build/book/*.docx` — the Word versions (gitignored), handy for checking
  or for someone who wants to edit a copy.

The **version** printed on the title page and in every footer is the
`version:` line at the top of `book_manifest.yaml`. Bump it together with
the version admonition on `index.md` and `version-history.md`.

### LibreOffice

The PDF step needs LibreOffice. The script looks, in order, for:

1. `$LIBREOFFICE_PYTHON` — the path to a Python that can `import uno`
   (e.g. LibreOffice's own `program/python.exe`);
2. a Windows LibreOffice seen from WSL (`/mnt/c/Program Files/LibreOffice`)
   — the maintainer's setup;
3. a native Linux LibreOffice (`soffice` on the PATH, with `python3-uno`).

It runs `bookbuild/lo_export.py` under that Python, which starts a hidden
LibreOffice for each volume, updates the contents page (twice, so the page
numbers settle), exports the PDF with bookmarks, then stops LibreOffice.
With a Windows LibreOffice the files are copied through a folder in the
Windows temp directory, because it can't reliably open files inside WSL.
Building all three volumes takes about half a minute.

## What's included, and what isn't

See `book_manifest.yaml` for the exact list. The volumes exclude
project/navigation pages (`about.md`, `index.md`, `mailing-list.md`,
`version-history.md`, `gallery.md`, `downloads.md`), the section index
pages, and the extra web-sourced pages (`history/origins.md`, `places.md`,
`other-monktons.md`); the "About this volume" text and disclaimers live in the manifest's
`front_matter`. The churchyard survey's long tables repeat their header row
on every page and don't split a row across a page break.

## Adding new content

- **A new Terry Marsh instalment** (Monkton Memories or A Farming Life):
  nothing to do here. Those two parts are defined by `glob` in the
  manifest (`history/monkton-memories/[0-9]*.md`,
  `history/farming-life/[0-9]*.md`), sorted alphabetically — which sorts
  correctly by number because the files are zero-padded (`01-`, `02-`,
  ... `25-`). Add the new file the way you normally would for the site,
  and the next `make book` picks it up automatically.
- **A new page or section**: add it to the right volume's `parts` in
  `book_manifest.yaml`, either as an explicit `sources:` list (for a
  one-off page, where order matters) or a `glob:` (for another numbered
  series).
- **A new volume**: add an entry under `volumes:` (id, PDF file name,
  title, subtitle, header, description, credit, parts). It appears on the
  Downloads page at the next build.
- **Reordering or renaming parts**: edit the manifest directly — it's the
  single source of truth for the volumes' structure, independent of the
  site's own navigation.

## How the conversion works

`scripts/bookbuild/mdparse.py` parses each source file's MyST Markdown
into a list of block dicts (headings, paragraphs, lists, tables, callouts,
figures, quotes) — handling the specific directives this content uses
(`{admonition}`, `{note}`/`{tip}`/`{warning}`/`{important}`/`{seealso}`,
`{epigraph}`, `{figure}`; `{toctree}` is dropped). A line ending in a
backslash (MyST's hard line break, used for the poems on the war memorial
page) becomes a line break in Word rather than being joined to the next
line with a space. It is not a general MyST
parser — if a page starts using syntax it doesn't recognise, it falls back
to a plain paragraph rather than failing the build, but the output for
that bit will look plain rather than styled. Check `make book`'s output
and the result if you add something syntactically new (a grid card, a
dropdown, a table inside an admonition) to a page that's in scope for the
book.

`scripts/bookbuild/docxwrite.py` turns those blocks into the actual
`.docx`: a title page, the "About this volume" page, a native Word
table-of-contents field, a part heading per manifest part (starting a
fresh page), a chapter heading per source file (also a fresh page, with a
bookmark), styled callout boxes, embedded images (consecutive
`photo-thumb` figures as a three-across grid), and real tables. Links that
point to another page *in the same volume* become clickable internal
cross-references; links to other site pages (in another volume, or not in
any, e.g. the Gallery) and to `_static` files like the 1926 walk's map PDF
become links to the live site (`https://monkton-kent.uk/...`); external
(`http`/`https`) links stay ordinary hyperlinks.

## Caching

Only images are cached — in `build/.book-cache/images/`, keyed by URL, so
re-running the build doesn't re-download the same Cloudinary images every
time. That's the only genuinely slow step (a network call); parsing and
writing the ~5,000 lines of content themselves take well under a second, so
there's no need for (and this doesn't do) per-chapter output caching —
the whole book rebuilds from scratch on every run, which is simpler and
has no staleness to reason about. Delete `build/.book-cache/` (or just
`build/`) to force every image to be re-downloaded.
