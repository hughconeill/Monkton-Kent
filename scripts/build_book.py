#!/usr/bin/env python3
"""Build the printable history book (.docx) from the site's own Markdown.

    python scripts/build_book.py

See scripts/README.md for the manifest format, caching, and how to add new
content (e.g. a new Farming Life instalment) without touching this script.
"""

import argparse
import datetime
import glob as globmod
import os
import posixpath
import sys
import time

import yaml

sys.path.insert(0, os.path.dirname(__file__))
from bookbuild import docxwrite, mdparse  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(REPO_ROOT, "source")


def load_manifest(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_part_files(part):
    """Return an ordered list of source/-relative posix paths for one part."""
    if "sources" in part:
        return list(part["sources"])
    if "glob" in part:
        pattern = os.path.join(SOURCE_DIR, part["glob"])
        matches = sorted(globmod.glob(pattern))
        return [os.path.relpath(m, SOURCE_DIR).replace(os.sep, "/") for m in matches]
    raise ValueError(f"Part {part.get('title')!r} has neither 'sources' nor 'glob'")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--manifest",
        default=os.path.join(os.path.dirname(__file__), "book_manifest.yaml"),
        help="path to the book manifest (default: scripts/book_manifest.yaml)",
    )
    args = ap.parse_args()

    t0 = time.time()
    manifest = load_manifest(args.manifest)

    # Resolve every part's file list up front, so we know the full set of
    # chapters before rendering anything - needed to build the bookmark map
    # that lets same-book cross-links (e.g. a war-memorial.md link to
    # clergy.md) become real internal hyperlinks.
    parts = []
    for part in manifest["parts"]:
        files = resolve_part_files(part)
        if not files:
            print(f"  ! part {part.get('title')!r} matched no files - skipping")
            continue
        parts.append({**part, "files": files})

    link_targets = {}
    bm = 0
    for part in parts:
        for relpath in part["files"]:
            link_targets[posixpath.normpath(relpath)] = f"bm_{bm}"
            bm += 1

    doc = docxwrite.new_document()
    image_cache_dir = os.path.join(REPO_ROOT, "build", ".book-cache", "images")

    cover = manifest.get("cover_image")
    cover_path = os.path.join(SOURCE_DIR, cover) if cover else None
    today = datetime.date.today().strftime("%B %Y")
    docxwrite.add_title_page(doc, manifest, cover_path, today)
    docxwrite.add_toc(doc)
    docxwrite.add_header_footer(doc, manifest.get("title", ""))

    file_count = 0
    for part in parts:
        print(f"Part: {part['title']} ({len(part['files'])} file(s))")
        docxwrite.add_part_heading(doc, part["title"], part.get("subtitle"))
        for relpath in part["files"]:
            abs_path = os.path.join(SOURCE_DIR, relpath)
            with open(abs_path, encoding="utf-8") as f:
                text = f.read()
            blocks = mdparse.parse_markdown(text)
            current_dir = posixpath.dirname(relpath)
            bookmark = link_targets[posixpath.normpath(relpath)]
            docxwrite.render_blocks(
                doc,
                blocks,
                level_offset=1,
                link_targets=link_targets,
                current_dir=current_dir,
                image_cache_dir=image_cache_dir,
                chapter_bookmark=bookmark,
                source_dir=SOURCE_DIR,
            )
            file_count += 1

    out_path = os.path.join(REPO_ROOT, manifest["output"])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc.save(out_path)

    cached_images = len(os.listdir(image_cache_dir)) if os.path.isdir(image_cache_dir) else 0
    elapsed = time.time() - t0
    print()
    print(f"Wrote {out_path}")
    print(f"{file_count} source files, {cached_images} image(s) cached, {elapsed:.1f}s")
    print('Open in Word and press Ctrl+A then F9 (or right-click the Contents field '
          'and choose "Update Field") to fill in the table of contents page numbers.')


if __name__ == "__main__":
    main()
