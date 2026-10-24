# Project Brief

*This file is the first thing a new contributor or maintainer should
read. Keep it short and current — update it when key decisions change.*

## What this project is

A documentation website recording the history of Monkton, a village
(civil parish) in Thanet, Kent, England — led by Stuart Horsburgh,
built with Sphinx and hosted on GitHub Pages. Content is written in
Markdown and lives in the `source/` folder.

## Scope

- **Geographic area covered:** the civil parish of Monkton, Thanet,
  which includes the hamlet of Gore Street, plus the wider Isle of
  Thanet where it's directly relevant (e.g. RAF Manston's wartime
  decoy site on Monkton Marshes).
- **Time period:** from the earliest evidence of settlement — an
  Anglo-Saxon cemetery dated to the 6th–7th centuries AD — through to
  the present day.
- **What's included:** the parish church (St Mary Magdalene —
  architecture, clergy back to 1291, bells, war memorial, and a full
  churchyard survey); village history and reminiscence (Terry Marsh's
  *Monkton Memories* and *A Farming Life* columns, originally
  published in the Monkton News); Stuart Horsburgh's 1926 Centenary
  Mile Walk; the village's Anglo-Saxon/medieval origins; its
  Historic England-listed buildings; a page on other places named
  Monkton worldwide; a photo gallery; and a Credits page naming
  contributors.
- **What's out of scope (for now):** a page of general local news
  coverage (`news.md`, "In the News") was built, published, and then
  deliberately removed at the project lead's request — don't
  recreate it without being asked again. Per the site's own privacy
  note (see `about.md`), content that could cause living people harm,
  embarrassment, or offence is also out of scope, even where accurate.

## Editorial standards

- **Citations:** there is no `source/sources.md` and no footnote
  convention in active use. Pages sourced from the open web
  (`history/origins.md`, `places.md`, `history/monkton-1926.md`,
  `other-monktons.md`) cite inline, with plain Markdown links to the
  original source directly in the prose or in a trailing "Source(s):"
  line — prefer the most authoritative source available (e.g. a
  listed building's own Historic England entry over a Wikipedia
  mirror of it). See `README.md`'s "Working with sources and images"
  section for the full convention.
- **Placeholders:** unresearched sections should stay clearly marked
  as placeholders rather than left silently blank or invented.
- **Disputed facts:** where sources disagree, say so on the page —
  see the "Conflicting evidence" admonition in `history/origins.md`
  for the pattern — rather than quietly picking one version.

## Images

- Store web-sized copies (under ~1MB) in `source/_static/images/`.
  Several newer pages instead embed images hosted externally on
  Cloudinary (`res.cloudinary.com/monkton/...`).
- Keep full-resolution originals outside the repo (external drive,
  family archive, etc.).
- Every image needs a caption with source/date/contributor, even if
  approximate.

## How the site is built and published

- Source files: Markdown in `source/`, built with Sphinx
  (MyST parser + Furo theme).
- `make book` additionally compiles the history/church content (not the
  churchyard survey database, not project/nav pages) into a single
  printable `.docx` book — see `scripts/README.md`.
- On every push to `main`, a GitHub Actions workflow
  (`.github/workflows/deploy.yml`) automatically builds the site and
  publishes it to GitHub Pages. No manual deploy step. Work on any
  other branch does **not** go live until it's merged to `main`.
- The site is published at `https://hughconeill.github.io/Monkton-Kent/`,
  which redirects to the project's custom domain,
  `https://monkton-kent.uk/` — link to the custom domain when sharing
  the site.
- To preview changes locally before pushing, see `README.md` for
  setup and `make html` / `make livehtml` instructions.

## Handover notes

- Repository: `https://github.com/hughconeill/Monkton-Kent` (renamed
  from `Monkton-Thanet-Folk-History-Sphinx`; GitHub redirects the old
  URL, but clones/remotes should be updated to the new one).
- Project lead (editorial decisions, source material, contact for
  contributors): **Stuart Horsburgh** — see `about.md` for current
  contact details.
- Website maintainer (build, hosting, technical issues): **Hugh
  O'Neill** — see `about.md` for current contact details.
- Original documents/photos held by: Stuart Horsburgh, plus an
  archive of village photographs and newspaper clippings held by
  Karen Wolstenhulme (being added to the site gradually — see
  `credits.md`).
