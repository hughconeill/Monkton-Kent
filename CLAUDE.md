# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Sphinx documentation site recording the history of Monkton (Thanet, Kent) — led by
Stuart Horsburgh. It started focused on St Mary Magdalene church (architecture, clergy
back to 1291, bells, war memorial, and a full churchyard survey) and has since grown to
cover the village's Anglo-Saxon/medieval origins, Terry Marsh's reminiscence columns,
Stuart's research section (his 1926 centenary walk and more), listed buildings, other places named Monkton worldwide, a
photo gallery, a Credits page, a mailing-list sign-up page, and a version history page — see "Architecture" below for the current page list.
Content is Markdown via MyST, rendered with the Furo theme, and deployed to GitHub
Pages. See `PROJECT-BRIEF.md` for scope/handover and `README.md` for local setup.

## Commands

```bash
source .venv/bin/activate          # venv already exists at .venv/
pip install -r requirements.txt    # install/update deps

make html                          # build to build/html/
make clean                         # remove build/
make livehtml                      # live-reload dev server (needs sphinx-autobuild,
                                    #   not currently in requirements.txt — pip install it first)
python3 -m http.server -d build/html 8000   # serve a built site locally
make book                          # build the three printable PDF volumes (needs
                                    #   LibreOffice) - see scripts/README.md
```

There is no test suite or linter configured — "correctness" here means the site builds
without Sphinx warnings/errors and renders as expected.

## Architecture

- `source/conf.py` — Sphinx config: MyST + `sphinx_copybutton` + `sphinx_design`
  extensions, Furo theme, brand colors, logo/favicon. Also loads
  `source/_static/custom.css` (via `html_css_files`) for style tweaks the
  theme's `html_theme_options` can't express — currently just left-aligning
  the sidebar logo, which Furo centers by default. `html_js_files` loads
  GoatCounter analytics (`gc.zgo.at/count.js`, pointed at the
  `monkton-kent.goatcounter.com` account) on every page via the
  `data-goatcounter`/`async` attributes Sphinx attaches to the tag — no
  separate script file or template override needed.
- `source/index.md` — home page. Its `toctree` is the actual site nav; only pages
  listed there (directly or via a nested `toctree`) are reachable/built into the
  visible site. **When adding a new page, it must be added to a `toctree` or it
  won't appear in the sidebar.**
- **Live content**: `source/church/` and `source/history/` are linked from
  `index.md`. `source/church/index.md` has its own `toctree` fanning out to
  `short-guide.md`, `bells.md`, `clergy.md`, `churchyard/index.md` (which itself
  fans out to `names-alphabetical.md`, `numbered-stones.md`,
  `survey-by-location.md`, `register-appendix.md` — the churchyard survey data),
  `richard-culmer.md`, `war-memorial.md`, and `memorials-inside.md`.
  `memorials-inside.md` numbers the 19 memorials as a Markdown ordered list
  (location in `*\[ … \]*` after the number). Each inscription sits in a
  shaded serif panel: a contentless ```` ```{rst-class} inscription ```` block
  immediately before an ```` ```{epigraph} ```` block (styled by
  `blockquote.inscription` in `custom.css`; the book converter drops
  `rst-class` and prints the epigraph as an indented italic quote). Register
  notes go *below* the panel as a "**From the parish registers:**" bullet
  list (name in bold caps, who they are, then the register facts; flag
  disagreements with the stone in italics), plus "**Family links:**" bullets
  cross-referencing other memorials. Don't nest bullet lists there — the
  converter flattens them.
  `war-memorial.md` gives each man on the memorial a `###` subheading
  (rank, name, dates, age) followed by his short biography (from the Dec
  2026 "MONKTON WAR MEMORIAL" document), under `## 1914 – 1918`,
  `## 1939 – 1945` and `## Names added later`; then the two non-Monkton
  servicemen buried in the churchyard, and two poems (line breaks via MyST
  trailing-backslash hard breaks). Commonwealth War Graves Commission
  details are not a separate section: where a man has a CWGC record, a
  bold "**Official record:**" paragraph with the CWGC link (service no.,
  next of kin, grave number/position) follows his biography.
  `source/history/terry-marshs-memories/` ("Terry Marsh's Memories",
  structured like Stuart's Research: an `index.md` with an introduction and a
  plain contents table) holds Terry Marsh's two Monkton News series, extracted
  from scanned `.docx` copies and, for the last instalments, from the
  magazine's PDF issues: `monkton-memories/` (childhood/village-life
  reminiscences, `01-`…`22-`, Sept 2022–June 2024) and `farming-life/` (his
  working life on local farms from 1976 on, `01-`…`27-`, Sept 2024–Nov 2026).
  Each article page ends with a `*Terry Marsh*` byline and an "Originally
  published in the Monkton News (Month Year)." line. Both series are complete
  as of the November 2026 issue (the editor says Terry may return some day —
  if he does, add new numbered files and update the "complete" wording in the
  section index, `farming-life/index.md` and the book manifest's `credit`).
  These folders moved from `history/monkton-memories/` and
  `history/farming-life/` in v2.1; `conf.py`'s `MOVED_DIRS` +
  `build-finished` hook writes meta-refresh redirect pages at the old URLs —
  keep it (or extend it) if pages move again.
- `source/history/index.md` has a "Featured" table (not a `{grid}`) linking
  `source/history/stuarts-research/index.md` and
  `source/history/terry-marshs-memories/index.md`; its toctree also lists
  `source/history/origins.md` (Anglo-Saxon/medieval Monkton, sourced from
  British History Online's Hasted transcription and the Kent Archaeological
  Society journal). `source/places.md` (linked from the root `index.md`) lists
  Monkton's 22 Historic England-listed buildings.
  `source/other-monktons.md` lists other places named Monkton worldwide
  (England, Wales, Scotland, North America, plus one non-place curiosity),
  grouped into Markdown tables by region. Unlike the rest of the site, these
  pages cite external web sources with inline Markdown links directly in
  the prose, rather than the footnote-to-`sources.md` convention below — there
  is no `sources.md` in this project (an earlier placeholder version was
  removed; it hasn't been recreated).
- `source/history/stuarts-research/` ("Stuart's Research") is Stuart
  Horsburgh's folk history of Monkton, converted from his Word document
  `Stuarts_Monkton_History.docx` (Nov 2026). It replaced the earlier
  single `history/monkton-1926.md` page (now deleted — old links to
  `history/monkton-1926.html` 404). `index.md` holds his general
  introduction and a contents table (a plain table, not `{grid}` cards, so
  the page stays printable by the volume converter); `centenary-walk/index.md`
  has the walk introduction, "The world in 1926", "Monkton in 1926", the
  route summary and the map PDF download
  (`source/_static/monkton-1926-centenary-mile-walk-map.pdf`);
  `centenary-walk/zone-1.md`…`zone-4.md` each open with that zone's map
  image (`_static/images/monkton-1926-zone-N.jpg`) followed by one `##`
  heading per house ("Left:/Right:" marks the side of the street on the
  first house of a group), with census/directory/Parish Council guide
  records as bullets with a bold date label. Stuart's own uncertainties
  (the `???` in his document) are kept as `{admonition} Stuart's query`
  boxes or a trailing "(?)" in headings, and unplaced 1901 census entries
  sit in "1901 census – entries not yet matched to a house" boxes — don't
  silently resolve these. Sibling pages: `special-stories.md`,
  `bernard-cole-interviews.md`, `parish-council-chairmen.md`,
  `final-thoughts.md`. Stuart's text is kept close to verbatim, including
  his convention of SURNAMES in capitals. When he sends a revised document,
  diff it against these pages rather than re-converting from scratch.
- `source/mailing-list.md` embeds a Brevo sign-up form as an `<iframe>` inside
  a ```` ```{raw} html ```` block (the iframe was chosen over Brevo's HTML embed so
  Brevo's CSS/JS can't clash with Furo, and form edits made in Brevo show up
  without a redeploy). The same iframe is also embedded under a
  "Mailing list" heading in `about.md`, and `index.md` has a "Mailing list"
  heading with a one-line link to the page, followed by a "Tips on using the
  website" `{admonition}` (Search box, Downloads, mailing list), just above
  the Table of Contents (the mailing list is deliberately not a home-page
  card — the aim is for only interested visitors to sign up). If the form's length changes in Brevo, adjust the
  iframe's `height` in **both** `mailing-list.md` and `about.md` so there's
  no inner scrollbar (currently 650). Subscribers are managed in
  Brevo, not in this repo.
- `source/downloads.md` offers the printable PDF volumes (see "The printable volumes"
  below); its volume list is generated by `make book`.
- `source/version-history.md` is a newest-first table of site releases
  (1.0 launched in the November 2026 Monkton News; 1.1 on 5 Nov 2026; 2 in the December 2026 Monkton News; 2.1 shortly after, adding Terry Marsh's final articles), linked
  from the root `toctree` and from `about.md`. **Add a row (and bump the
  version admonition at the top of `index.md` to match) whenever a
  significant update goes live** — new pages, sections, features, or a
  substantial batch of new material such as photos or articles. (Exception:
  for the small 2.1 release the user chose to keep the home-page admonition
  summarising Version 2 — ask before bumping it for a point release.) Routine data
  corrections and typo fixes (e.g. the 7 Nov 2026 memorial/churchyard
  corrections) do not get an entry. When a change is significant, prompt the
  user to add the row before pushing to `main` — and to bump `version:` in
  `scripts/book_manifest.yaml` and rebuild the PDF volumes (`make book`).
- The original scaffold also included `source/history/the-mill.md`,
  `source/history/twentieth-century.md`, `source/people/`, `source/faq.md`,
  `source/timeline.md`, and an earlier placeholder `source/sources.md` —
  these were removed for being unfinished (bracketed placeholders, never
  wired into a `toctree`). They no longer exist; don't assume they're just
  unlinked. `source/news.md` ("In the News", press coverage of Monkton from
  the open web) existed briefly as a finished, linked page but was removed
  at the user's request — don't recreate it without being asked.
- Images referenced from `history/`/`people/`/church pages sometimes point at
  `_static/images/placeholder-*.jpg` (literal grey placeholders) — replace with real
  scans before treating a page as finished. Some newer pages (e.g. `index.md`,
  `church/index.md`) instead reference images hosted externally on Cloudinary
  (`res.cloudinary.com/monkton/...`). To find new uploads, load
  `~/.config/cloudinary.env` (holds `CLOUDINARY_URL`, outside the repo —
  never commit or echo it) and list resources with the `cloudinary` package
  in `.venv` (`cloudinary.api.resources`), then diff against the image IDs
  already referenced in `source/**/*.md`. Ignore Cloudinary's built-in demo
  assets (`sample`, `samples/...`, `cld-sample*`, `main-sample`); real uploads
  are in the `Monkton-general` asset folder. Gallery entries in `gallery.md`
  are `{grid-item-card}`s using a `w_500,c_limit,q_auto` thumbnail with a
  `:target:` to the full image.
  Article pages (currently Stuart's Research) embed gallery photos as small
  click-to-zoom thumbnails: a `{figure}` whose source is the Cloudinary URL
  with `w_800,c_limit,q_auto`, `:target:` the untransformed full image, and
  `:figclass: photo-thumb`. The `photo-thumb` rule in `custom.css` makes them
  inline-block at a third of the width (half on phones), so consecutive
  figures form a row of thumbnails. Use `{figure}`, not `{image}`/grids, on
  any page in the printable volumes — the converter only understands
  `{figure}`.

## Editorial conventions (from `README.md` / `PROJECT-BRIEF.md`)

- **Citations**: the project's original convention (from `PROJECT-BRIEF.md`) was a
  Markdown footnote (`[^label]` ... `[^label]: full citation`) linking back to a
  `source/sources.md` organized by record type — that file no longer exists (see
  above), so this isn't in active use. Pages sourced from the open web
  (`origins.md`, `places.md`,
  `other-monktons.md`) instead cite with inline
  Markdown links directly in the prose/a trailing "Source(s):" line, pointing at
  the original page (British History Online, Historic England, Wikipedia, etc.)
  — prefer the most authoritative/primary source available (e.g. link a listed
  building to Historic England's own listing page over a Wikipedia mirror, when
  you have the exact listing URL).
- **Dates**: `24-Jan-1934` style everywhere in tables, register notes and prose
  (adopted Nov 2026 for US visitors); unknown parts as `?` (`?-Oct-1855`,
  `?-?-????`, `?6-Dec-1810` = probably the 6th). Dates *transcribed from a stone
  or brass* stay as carved — on the churchyard survey that's anything outside
  the `*\[ … \]*` notes, on `memorials-inside.md` anything inside an
  `{epigraph}`, and on `register-appendix.md` the dot-dates in quoted
  inscriptions (#91, #237.5). Written-out prose dates ("3rd May 1915", e.g. the
  war memorial biographies) are fine as they are.
- **Disputed facts**: where sources disagree, say so on the page (see the
  `{admonition}` "Conflicting evidence" pattern) rather than silently picking one.
- **Placeholders**: unresearched sections should stay clearly marked as placeholders
  rather than left blank or invented.
- **Images**: web-sized copies (under ~1MB) go in `source/_static/images/`;
  full-resolution originals are kept outside the repo, noted in `sources.md`. Use the
  `{figure}` directive for numbered captions.

## MyST syntax in use

- `{admonition}` (note/warning/tip), `{figure}`, `{toctree}` — core Sphinx/MyST
- `{grid}` / `{grid-item-card}` (from `sphinx_design`) — the card layouts used on
  `index.md` and section index pages like `church/index.md`
- `{dropdown}`, `:::` colon-fence directives, `{{ }}` substitutions, `- [ ]` task
  lists — enabled via `myst_enable_extensions` in `conf.py`

## Deployment

`.github/workflows/deploy.yml` is active: every push to `main` (or a manual run from the
Actions tab) builds the site with `sphinx-build -b html source build/html` and publishes
it to GitHub Pages via `actions/deploy-pages`. Work on other branches does **not** go
live until it is merged to `main`. The repository is named `Monkton-Kent` on GitHub, so
the site builds to `https://hughconeill.github.io/Monkton-Kent/`, which redirects to the
project's custom domain, `https://monkton-kent.uk/` — that's the URL to share, not the
`github.io` one.

### Releases (versions)

Each release in `version-history.md` is a **git tag + GitHub Release** (`gh release`),
named `v<version>` — `v1.1` (live from 5–7 Nov 2026, tagged retrospectively at
`71fe3cb`; 1.0 was never tagged), `v2.0` (December 2026), and so on. A new version is
developed on its own branch (e.g. `Version_2_December`) and released by:

1. bumping the version in `index.md`'s admonition, `version-history.md` and
   `version:` in `scripts/book_manifest.yaml`, then `make book` and committing the
   refreshed PDFs on the branch;
2. a pull request into `main`, merged with a **merge commit** (`gh pr merge --merge`,
   not squash/rebase), so the whole release is one commit on `main`;
3. tagging that merge commit and creating the GitHub Release
   (`gh release create v2.0 --target main ...`) with short notes and the PDF volumes
   attached as release assets.

To roll back a release: `git revert -m 1 <merge commit>` on `main` and push (the site
redeploys); the tag of the previous version shows exactly what was live. Always confirm
with the user before merging or pushing to `main`.

## The printable volumes (Downloads page)

`scripts/build_book.py` (`make book`) converts the site's content into three A4 PDF
volumes, offered on `source/downloads.md` — see `scripts/README.md` for the full guide.
The volumes, defined in `scripts/book_manifest.yaml`: `church` (church pages, then the
churchyard survey as a reference section), `stuart` (Stuart's Research only — origins, places
and other Monktons are deliberately left out), `terry` (Monkton Memories and A Farming Life, by `glob`, so
new instalments are picked up with no manifest edit). Every volume ends with
`credits.md`, and opens with a title page and an "About this volume" page whose
disclaimer/copyright/contact text lives in the manifest's `front_matter`. Headers carry
the volume name; footers carry the manifest's `version:` and "Page X of Y".

It's a purpose-built Markdown→docx converter (not a general MyST parser, so new syntax on
a page in a volume may need the converter extending — the guide explains what it handles),
writing `build/book/*.docx` (gitignored), then `scripts/bookbuild/lo_export.py` runs under
LibreOffice's own Python (on this machine the Windows LibreOffice, reached from WSL) to
update the contents page and export the PDFs. **The PDFs in `source/_static/downloads/`
are committed** — GitHub Actions can't build them — and the build also rewrites the
generated block between the `volumes:start`/`volumes:end` markers in `downloads.md`
(page counts, sizes); don't hand-edit inside the markers. When releasing a new version:
bump `version:` in the manifest along with `index.md`/`version-history.md`, run
`make book`, and commit the refreshed PDFs. Skip rebuilding for routine typo fixes
(each rebuild adds ~7 MB to the git history).

## Keeping the other project docs current

This repo has three top-level docs, each for a different reader — when a change affects
what one of them promises, update it in the same turn as the change, not as a follow-up:

- **`CLAUDE.md`** (this file) — for Claude Code: what's actually live vs. scaffolded,
  file-by-file architecture, and editorial conventions as currently practiced.
- **`README.md`** — for a human contributor setting up the project locally: install
  steps, build commands, the project layout tree, and how to add a page.
- **`PROJECT-BRIEF.md`** — the project's own short brief: scope (what's in/out), who's
  responsible for what, and handover notes (repo, contacts, where originals are kept).
  It's meant to stay short enough that a new maintainer reads the whole thing.

In practice this means: adding, removing, or renaming a page updates README.md's
project-layout tree (and PROJECT-BRIEF.md's scope list, if it changes what the site
covers); a new contributor, a changed contact, or a changed repo/domain updates
PROJECT-BRIEF.md's handover notes; and a new convention, dependency, or build step
updates whichever of the three describes that area. Don't assume one file being right
means the others are — check all three against the file you're changing.
