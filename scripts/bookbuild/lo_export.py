"""Convert .docx volumes to PDF with LibreOffice, refreshing the contents page first.

This runs under *LibreOffice's own bundled Python* (which has the `uno`
module), not the project venv — scripts/build_book.py launches it:

    <LibreOffice>/program/python(.exe) lo_export.py IN.docx OUT.pdf [IN2.docx OUT2.pdf ...]

A plain `soffice --convert-to pdf` would leave Word's table-of-contents field
showing its placeholder text; driving LibreOffice over UNO lets us update the
document's indexes (contents page numbers) and fields (page X of Y) before
exporting, and export with PDF bookmarks.
"""

import os
import subprocess
import sys
import time

import uno
from com.sun.star.beans import PropertyValue


def _props(**kw):
    out = []
    for k, v in kw.items():
        p = PropertyValue()
        p.Name, p.Value = k, v
        out.append(p)
    return tuple(out)


def _file_url(path):
    return uno.systemPathToFileUrl(os.path.abspath(path))


def _start_office():
    program_dir = os.path.dirname(sys.executable)
    soffice = os.path.join(program_dir, "soffice.exe" if os.name == "nt" else "soffice")
    pipe = f"monkton_book_{os.getpid()}_{time.time_ns()}"
    profile = _file_url(os.path.join(os.environ.get("TEMP", "/tmp"), "monkton_book_lo_profile"))
    proc = subprocess.Popen([
        soffice, "--headless", "--invisible", "--nologo", "--norestore", "--nodefault",
        f"-env:UserInstallation={profile}",
        f"--accept=pipe,name={pipe};urp;StarOffice.ComponentContext",
    ])
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local)
    for _ in range(120):
        try:
            ctx = resolver.resolve(f"uno:pipe,name={pipe};urp;StarOffice.ComponentContext")
            return proc, ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
        except Exception:
            time.sleep(0.5)
    _stop_office(proc)
    sys.exit("could not connect to LibreOffice")


def _stop_office(proc):
    # Closing documents / terminating LibreOffice over the UNO bridge was
    # found to hang (Windows LibreOffice driven from WSL), so once the PDF is
    # written we simply stop the process tree we started.
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    else:
        proc.kill()
    try:
        proc.wait(timeout=20)
    except Exception:
        pass


def convert(src, dst):
    # A fresh LibreOffice per document - see _stop_office.
    proc, desktop = _start_office()
    try:
        doc = desktop.loadComponentFromURL(_file_url(src), "_blank", 0, _props(Hidden=True))
        # Twice: the first pass fills in the contents (which can change
        # page breaks); the second corrects the page numbers in it.
        for _ in range(2):
            idx = doc.getDocumentIndexes()
            for i in range(idx.getCount()):
                idx.getByIndex(i).update()
            doc.getTextFields().refresh()
        filter_data = uno.Any("[]com.sun.star.beans.PropertyValue", _props(
            ExportBookmarks=True,
            ExportNotes=False,
            UseTaggedPDF=True,
            Quality=85,
            ReduceImageResolution=True,
            MaxImageResolution=200,
        ))
        uno.invoke(doc, "storeToURL", (_file_url(dst), _props(
            FilterName="writer_pdf_Export", FilterData=filter_data)))
        print(f"  pdf written: {os.path.basename(dst)}", flush=True)
    finally:
        _stop_office(proc)


def main(pairs):
    for src, dst in pairs:
        convert(src, dst)


def _quietly(fn):
    try:
        fn()
    except Exception:
        pass


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or len(args) % 2:
        sys.exit(__doc__)
    main(list(zip(args[0::2], args[1::2])))
    sys.stdout.flush()
    os._exit(0)  # skip UNO bridge teardown, which can hang
