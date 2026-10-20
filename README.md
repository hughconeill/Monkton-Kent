# The History of Monkton — Sphinx Documentation Site

A Sphinx documentation site recording the history of Monkton (Thanet, Kent),
written in **Markdown** (via [MyST](https://myst-parser.readthedocs.io/)) with
the [Furo](https://pradyunsg.me/furo/) theme — see `CLAUDE.md` for what's
actually live on the site versus still in progress.

## Project layout

```
docs-site/
├── requirements.txt      # Python dependencies
├── Makefile / make.bat   # Build commands
└── source/
    ├── conf.py           # Sphinx configuration
    ├── index.md          # Home page
    ├── about.md           # About the project / how to contribute
    ├── history/            # Village history and reminiscence
    │   ├── index.md
    │   ├── monkton-1926.md    # Stuart Horsburgh's 1926 centenary walk + map
    │   ├── origins.md         # Anglo-Saxon/medieval Monkton, from web sources
    │   ├── monkton-memories/  # Terry Marsh's Monkton News column (numbered)
    │   └── farming-life/      # Terry Marsh's Monkton News column (numbered)
    ├── places.md            # Monkton's listed buildings (Historic England)
    ├── other-monktons.md     # Other places named Monkton, worldwide
    ├── gallery.md           # Photo gallery
    ├── credits.md            # Who's contributed, and what they've contributed
    ├── _static/images/    # Photos and scans go here (currently grey
    │                       # placeholder JPGs — swap these out)
    ├── _static/custom.css # Site-wide CSS overrides (loaded via html_css_files)
    └── _templates/         # Custom HTML template overrides (optional)
```

Earlier scaffold pages (`timeline.md`, `people/`, `sources.md`, `faq.md`,
`history/the-mill.md`, `history/twentieth-century.md`) were removed for being
unfinished placeholders rather than filled in — recreate them if the project
needs them again.

## Working with sources and images

- **Every factual claim should cite a source.** There's no `sources.md` in
  this project — pages sourced from the open web (`history/origins.md`,
  `places.md`, `history/monkton-1926.md`, `other-monktons.md`)
  cite with plain inline Markdown
  links to the original page, directly in the prose or in a trailing
  "Source(s):" line. Prefer the most authoritative source you can find (e.g.
  a building's own Historic England listing page over a Wikipedia mirror of
  it), and where two good sources disagree, say so on the page (see the
  `{admonition}` "Conflicting evidence" pattern in `history/origins.md`)
  rather than silently picking one.
- **Images** live in `source/_static/images/`. Keep web-sized copies
  (under ~1MB) in the repo and store full-resolution originals
  elsewhere — note where in `sources.md`. Reference them with the
  `{figure}` directive (adds a numbered caption) as shown throughout
  the `history/` and `people/` pages.
- **Downloadable documents** (e.g. PDFs) go directly in `source/_static/`.
  Link to them with a plain Markdown link (`[label](../_static/file.pdf)`,
  adjusting the relative path to the page); MyST/Sphinx automatically
  turns links to non-HTML files into proper downloads — see
  `history/index.md`'s Monkton 1926 map for an example.

## Setup

1. Create a virtual environment (recommended):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Build the site

```bash
make html
```

The built site will be in `build/html/index.html` — open it directly in
a browser, or serve it locally:

```bash
python3 -m http.server -d build/html 8000
```

Then visit `http://localhost:8000`.

## Live-reloading dev server (optional but recommended)

Install `sphinx-autobuild` once:

```bash
pip install sphinx-autobuild
```

Then run:

```bash
make livehtml
```

This opens a local server that automatically rebuilds and refreshes
your browser whenever you save a file — much faster for writing.

## Adding new pages

1. Create a new `.md` file (e.g. `source/guides/new-topic.md`).
2. Add it to the relevant `toctree` — e.g. in `source/guides/index.md`:

   ```markdown
   ```{toctree}
   :maxdepth: 1

   example-guide
   new-topic
   ```
   ```

3. Rebuild (`make html`).

## Useful MyST Markdown syntax

- **Admonitions**: `` ```{note} `` / `{warning}` / `{tip}` blocks
- **Tabs**: `` :::{tab-set} `` + `` :::{tab-item} Label `` (needs `sphinx-design`)
- **Cards/grids**: `` :::{grid-item-card} `` (needs `sphinx-design`)
- **Dropdowns**: `` ```{dropdown} Title ``
- **Cross-references**: plain Markdown links, e.g. `[Getting Started](getting-started.md)`
- **Task lists**: `- [ ] todo` / `- [x] done`

Full syntax reference: https://myst-parser.readthedocs.io/en/latest/syntax/typography.html

## Customizing the theme

Edit `html_theme_options` in `source/conf.py` — colors, adding a GitHub
link ("source_repository"), sidebar behavior, etc. Full option list:
https://pradyunsg.me/furo/customisation/

To add a logo or favicon, drop the image file in `source/_static/` and
uncomment the `html_logo` / `html_favicon` lines in `conf.py`.

For tweaks the theme options don't cover, `source/_static/custom.css`
is loaded on every page via `html_css_files` in `conf.py`. It currently
just left-aligns the sidebar logo (Furo centers it by default) —
add further overrides there rather than editing the theme itself.

## Publishing via GitHub Pages (automatic)

This repo includes `.github/workflows/deploy.yml`, which builds and
publishes the site automatically on every push to `main`.

One-time setup after pushing to GitHub:
1. Go to the repo's **Settings → Pages**.
2. Under "Build and deployment", set **Source** to **GitHub Actions**.
3. Push to `main` (or re-run the workflow from the **Actions** tab) —
   the site will be live at `https://<username>.github.io/<repo-name>/`.

After that, there's no manual deploy step: edit a page, commit, push,
and the live site updates in a minute or two. For this project, that's
`https://hughconeill.github.io/Monkton-Kent/`, which redirects to the
custom domain `https://monkton-kent.uk/` — share the custom domain,
not the `github.io` link.

## Deploying

Common free options:
- **Read the Docs** — connect your git repo, it builds automatically on push.
- **GitHub Pages** — build with `make html`, then publish `build/html/`
  (e.g. via a GitHub Action or the `gh-pages` branch).
- **Netlify / Vercel** — set the build command to
  `pip install -r requirements.txt && sphinx-build -b html source build/html`
  and the publish directory to `build/html`.
