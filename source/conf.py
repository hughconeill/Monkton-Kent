# Configuration file for the Sphinx documentation builder.
# For a full list of options: https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------

project = "The History of Monkton"
copyright = "2026, Monkton Local History Project"
author = "Monkton Local History Project"
release = "0.1"

# -- General configuration ----------------------------------------------------

extensions = [
    "myst_parser",           # Markdown support
    "sphinx_copybutton",     # Adds a "copy" button to code blocks
    "sphinx_design",         # Cards, tabs, grids, dropdowns, badges
]

# Let Sphinx build from both .rst and .md files
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# MyST Markdown extensions - these turn on extra Markdown syntax
myst_enable_extensions = [
    "colon_fence",      # ::: fenced directives (cleaner than ```{})
    "deflist",           # Definition lists
    "linkify",            # Auto-link bare URLs
    "substitution",      # {{ variable }} substitutions
    "tasklist",           # - [ ] checkboxes
    "attrs_inline",      # {.class} attributes on inline elements
    "attrs_block",       # {.class} attributes on the preceding block (e.g. tables)
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_css_files = ["custom.css"]

# GoatCounter analytics (privacy-friendly, no cookies) - https://www.goatcounter.com/
html_js_files = [
    ("https://gc.zgo.at/count.js", {"data-goatcounter": "https://monkton-kent.goatcounter.com/count", "async": "async"}),
]

# -- Options for HTML output ---------------------------------------------------

html_theme = "furo"
html_static_path = ["_static"]
html_title = "The History of Monkton"

# Furo theme options
html_theme_options = {
    "sidebar_hide_name": False,
    "light_css_variables": {
        "color-brand-primary": "#2563eb",
        "color-brand-content": "#2563eb",
    },
    "dark_css_variables": {
        "color-brand-primary": "#60a5fa",
        "color-brand-content": "#60a5fa",
    },
    # Uncomment and edit if you have a repo:
    # "source_repository": "https://github.com/yourname/yourrepo/",
    # "source_branch": "main",
    # "source_directory": "docs/source/",
}

# Optional: add your own logo/favicon by dropping files in _static/
html_logo = "_static/logo_trans_red.png"
html_favicon = "_static/monkton_coa.ico"
