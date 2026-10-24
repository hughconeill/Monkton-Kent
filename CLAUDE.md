# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Sphinx documentation site recording the history of Monkton (Thanet, Kent) — led by
Stuart Horsburgh. It started focused on St Mary Magdalene church (architecture, clergy
back to 1291, bells, war memorial, and a full churchyard survey) and has since grown to
cover the village's Anglo-Saxon/medieval origins, Terry Marsh's reminiscence columns,
Stuart's 1926 centenary walk, listed buildings, other places named Monkton worldwide, a
photo gallery, and a Credits page — see "Architecture" below for the current page list.
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
  `source/history/index.md` fans out to two columns by Terry Marsh, originally
  published in the Monkton News parish magazine and extracted from scanned
  `.docx` copies: `monkton-memories/` (childhood/village-life reminiscences,
  numbered `01-`…`06-`) and `farming-life/` (his working life on local farms
  from 1976 on, numbered `01-`…`22-`). Each article page ends with a
  `*Terry Marsh*` byline and an "Originally published in the Monkton News
  (Month Year)." line. New issues of the magazine will surface more instalments
  of both columns later — renumbering/re-titling them then is expected.
- `source/history/index.md` also has a "Featured" table (not a `{grid}`, so it
  reads as one-off rather than a permanent column like Terry Marsh's) linking
  `source/history/monkton-1926.md` (Stuart Horsburgh's 1926 centenary-walk
  article and 4-zone map, plus a downloadable PDF built from the same images —
  see `source/_static/monkton-1926-centenary-mile-walk-map.pdf`) and
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
  (`res.cloudinary.com/monkton/...`).

## Editorial conventions (from `README.md` / `PROJECT-BRIEF.md`)

- **Citations**: the project's original convention (from `PROJECT-BRIEF.md`) was a
  Markdown footnote (`[^label]` ... `[^label]: full citation`) linking back to a
  `source/sources.md` organized by record type — that file no longer exists (see
  above), so this isn't in active use. Pages sourced from the open web
  (`origins.md`, `places.md`, `monkton-1926.md`,
  `other-monktons.md`) instead cite with inline
  Markdown links directly in the prose/a trailing "Source(s):" line, pointing at
  the original page (British History Online, Historic England, Wikipedia, etc.)
  — prefer the most authoritative/primary source available (e.g. link a listed
  building to Historic England's own listing page over a Wikipedia mirror, when
  you have the exact listing URL).
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
live until it is merged to `main` — Version 2 was developed on `Version_2_Terry` and
went live when PR #1 was merged. The repository is named `Monkton-Kent` on GitHub, so
the site builds to `https://hughconeill.github.io/Monkton-Kent/`, which redirects to the
project's custom domain, `https://monkton-kent.uk/` — that's the URL to share, not the
`github.io` one.

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
