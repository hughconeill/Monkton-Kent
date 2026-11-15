#!/usr/bin/env python3
"""Build the printable history volumes (.docx, then A4 PDF) from the site's own Markdown.

    python scripts/build_book.py                 # all volumes, docx + PDF
    python scripts/build_book.py --volume terry  # just one (repeatable)
    python scripts/build_book.py --no-pdf        # .docx only (no LibreOffice needed)

See scripts/README.md for the manifest format, the LibreOffice requirement
for PDFs, and how to add new content (e.g. a new Farming Life instalment)
without touching this script.
"""

import argparse
import glob as globmod
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import time

import yaml

sys.path.insert(0, os.path.dirname(__file__))
from bookbuild import docxwrite, mdparse  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(REPO_ROOT, "source")
LO_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bookbuild", "lo_export.py")


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


def fill(text, values):
    for k, v in values.items():
        text = text.replace("{" + k + "}", v)
    return text


# ---------------------------------------------------------------------------
# One volume -> .docx
# ---------------------------------------------------------------------------

def build_docx(manifest, volume, out_path):
    if manifest.get("site_url"):
        docxwrite.SITE_BASE = "https://" + manifest["site_url"].strip("/") + "/"

    # Resolve every part's file list up front, so we know the volume's full
    # set of chapters before rendering anything - needed for the bookmark map
    # that turns same-volume cross-links into internal hyperlinks (links to
    # pages in other volumes go to the live website instead).
    parts = []
    for part in volume["parts"] + manifest.get("closing_parts", []):
        files = resolve_part_files(part)
        if not files:
            print(f"  ! part {part.get('title')!r} matched no files - skipping")
            continue
        parts.append({**part, "files": files})

    link_targets = {}
    for n, relpath in enumerate(f for part in parts for f in part["files"]):
        link_targets[posixpath.normpath(relpath)] = f"bm_{n}"

    image_cache_dir = os.path.join(REPO_ROOT, "build", ".book-cache", "images")
    version = manifest.get("version", "")
    series = manifest.get("series", "")
    site_url = manifest.get("site_url", "")

    def render(blocks, current_dir, bookmark=None, page_break=True):
        docxwrite.render_blocks(
            doc, blocks, level_offset=1, link_targets=link_targets,
            current_dir=current_dir, image_cache_dir=image_cache_dir,
            chapter_bookmark=bookmark, page_break_before_chapter=page_break,
            source_dir=SOURCE_DIR,
        )

    doc = docxwrite.new_document()
    cover = manifest.get("cover_image")
    docxwrite.add_title_page(
        doc, {**volume, "series": series, "site_url": site_url},
        os.path.join(SOURCE_DIR, cover) if cover else None, version)

    values = {
        "series": series,
        "site_url": site_url,
        "version": version,
        "version_lower": version[:1].lower() + version[1:],
        "volume_credit": " ".join((volume.get("credit") or "").split()),
    }
    docxwrite.add_front_matter(
        doc,
        [{"heading": s["heading"], "text": fill(s["text"], values)}
         for s in manifest.get("front_matter", [])],
        link_targets,
        lambda md: render(mdparse.parse_markdown(md), "", page_break=False),
    )
    docxwrite.add_toc(doc)
    docxwrite.add_header_footer(doc, volume.get("header", volume["title"]), version)

    file_count = 0
    for part in parts:
        print(f"  Part: {part['title']} ({len(part['files'])} file(s))")
        docxwrite.add_part_heading(doc, part["title"], part.get("subtitle"))
        for relpath in part["files"]:
            with open(os.path.join(SOURCE_DIR, relpath), encoding="utf-8") as f:
                blocks = mdparse.parse_markdown(f.read())
            render(blocks, posixpath.dirname(relpath),
                   bookmark=link_targets[posixpath.normpath(relpath)])
            file_count += 1

    doc.core_properties.title = volume["title"]
    doc.core_properties.subject = series
    doc.core_properties.author = "Monkton history project"
    doc.core_properties.comments = f"{version} – {site_url}"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc.save(out_path)
    return file_count


# ---------------------------------------------------------------------------
# .docx -> PDF via LibreOffice
# ---------------------------------------------------------------------------

def find_libreoffice_python():
    """LibreOffice's Python (it has the `uno` module), and whether it's Windows.

    Order: $LIBREOFFICE_PYTHON; Windows LibreOffice seen from WSL; a native
    Linux LibreOffice (whose system python3 has python3-uno).
    """
    env = os.environ.get("LIBREOFFICE_PYTHON")
    if env:
        return env, env.lower().endswith(".exe")
    for base in ("/mnt/c/Program Files/LibreOffice", "/mnt/c/Program Files (x86)/LibreOffice"):
        exe = os.path.join(base, "program", "python.exe")
        if os.path.exists(exe):
            return exe, True
    if shutil.which("soffice"):
        for py in ("/usr/bin/python3", sys.executable):
            if subprocess.run([py, "-c", "import uno"], capture_output=True).returncode == 0:
                return py, False
    return None, False


def windows_temp_dir():
    out = subprocess.run(["cmd.exe", "/c", "echo %TEMP%"], capture_output=True, text=True,
                         cwd="/mnt/c").stdout.strip()
    return subprocess.run(["wslpath", "-u", out], capture_output=True, text=True).stdout.strip()


def convert_to_pdf(jobs):
    """jobs: list of (docx_path, pdf_path). Converts them in one LibreOffice session."""
    lo_python, is_windows = find_libreoffice_python()
    if not lo_python:
        sys.exit("LibreOffice not found - install it (or set LIBREOFFICE_PYTHON), "
                 "or run with --no-pdf. See scripts/README.md.")

    # Windows LibreOffice can't reliably read files inside the WSL filesystem,
    # so work in a folder under the Windows temp directory.
    work = tempfile.mkdtemp(prefix="monkton_book_",
                            dir=windows_temp_dir() if is_windows else None)
    to_native = (lambda p: subprocess.run(["wslpath", "-w", p], capture_output=True,
                                          text=True).stdout.strip()) if is_windows else (lambda p: p)
    try:
        args = []
        shutil.copy(LO_SCRIPT, work)
        for docx_path, pdf_path in jobs:
            tmp_docx = os.path.join(work, os.path.basename(docx_path))
            shutil.copy(docx_path, tmp_docx)
            args += [to_native(tmp_docx), to_native(os.path.join(work, os.path.basename(pdf_path)))]
        print(f"Converting {len(jobs)} volume(s) to PDF with LibreOffice...")
        subprocess.run([lo_python, to_native(os.path.join(work, "lo_export.py")), *args],
                       check=True, timeout=1800)
        for _, pdf_path in jobs:
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            shutil.copy(os.path.join(work, os.path.basename(pdf_path)), pdf_path)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def pdf_page_count(path):
    from pypdf import PdfReader
    return len(PdfReader(path).pages)


def update_downloads_page(manifest, built):
    """Rewrite the volumes table on the Downloads page from the built PDFs."""
    page = os.path.join(REPO_ROOT, manifest["downloads_page"])
    if not os.path.exists(page):
        print(f"  ! {manifest['downloads_page']} not found - not updated")
        return
    pdf_rel = posixpath.relpath(manifest["pdf_dir"], posixpath.dirname(manifest["downloads_page"]))
    rows = []
    for vol in manifest["volumes"]:
        pdf = os.path.join(REPO_ROOT, manifest["pdf_dir"], vol["file"])
        if not os.path.exists(pdf):
            continue
        size_mb = os.path.getsize(pdf) / 1_000_000
        rows.append(
            f"### {vol['title']}\n\n"
            f"*{vol['subtitle']}*\n\n"
            f"{' '.join(vol['description'].split())}\n\n"
            f"[Download the PDF]({pdf_rel}/{vol['file']}) – "
            f"{pdf_page_count(pdf)} pages, {size_mb:.1f} MB\n"
        )
    block = (f"<!-- volumes:start (generated by scripts/build_book.py - don't edit by hand) -->\n\n"
             f"**{manifest['version']}**\n\n" + "\n".join(rows) +
             "\n<!-- volumes:end -->")
    with open(page, encoding="utf-8") as f:
        text = f.read()
    new, n = re.subn(r"<!-- volumes:start.*?<!-- volumes:end -->", lambda m: block, text, flags=re.S)
    if not n:
        print(f"  ! no volumes:start/end markers in {manifest['downloads_page']} - not updated")
        return
    with open(page, "w", encoding="utf-8") as f:
        f.write(new)
    print(f"Updated {manifest['downloads_page']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", default=os.path.join(os.path.dirname(__file__), "book_manifest.yaml"),
                    help="path to the book manifest (default: scripts/book_manifest.yaml)")
    ap.add_argument("--volume", action="append",
                    help="build only this volume id (repeatable; default: all)")
    ap.add_argument("--no-pdf", action="store_true", help="build the .docx files only")
    args = ap.parse_args()

    t0 = time.time()
    manifest = load_manifest(args.manifest)
    volumes = manifest["volumes"]
    if args.volume:
        unknown = set(args.volume) - {v["id"] for v in volumes}
        if unknown:
            sys.exit(f"unknown volume id(s): {', '.join(sorted(unknown))}")
        volumes = [v for v in volumes if v["id"] in args.volume]

    jobs = []
    for vol in volumes:
        print(f"Volume: {vol['title']}")
        docx_path = os.path.join(REPO_ROOT, manifest["docx_dir"], os.path.splitext(vol["file"])[0] + ".docx")
        n = build_docx(manifest, vol, docx_path)
        print(f"  wrote {os.path.relpath(docx_path, REPO_ROOT)} ({n} source files)")
        jobs.append((docx_path, os.path.join(REPO_ROOT, manifest["pdf_dir"], vol["file"])))

    if not args.no_pdf:
        convert_to_pdf(jobs)
        for _, pdf in jobs:
            print(f"  {os.path.relpath(pdf, REPO_ROOT)}: {pdf_page_count(pdf)} pages, "
                  f"{os.path.getsize(pdf) / 1_000_000:.1f} MB")
        update_downloads_page(manifest, jobs)

    print(f"Done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
