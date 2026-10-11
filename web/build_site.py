"""Builds the web page into _site/ (what GitHub Pages publishes).

  _site/index.html     the page
  _site/app.py         the glue the page runs in Pyodide
  _site/killsheet.zip  the killsheet package and the example wells, unpacked in the browser

Run it with:  python web/build_site.py
Try it with:  python -m http.server --directory _site   (then open http://localhost:8000)
"""

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
PACKAGE = ROOT / "src" / "killsheet"
EXAMPLES = ROOT / "examples"


def build():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    for name in ("index.html", "app.py"):
        shutil.copy(ROOT / "web" / name, SITE / name)
    with zipfile.ZipFile(SITE / "killsheet.zip", "w", zipfile.ZIP_DEFLATED) as package:
        for path in sorted(PACKAGE.glob("*.py")):
            package.write(path, f"killsheet/{path.name}")
        # The example wells (their WELL data) and the printer they import.
        for path in sorted(EXAMPLES.glob("*_well.py")) + [EXAMPLES / "kill_sheet_printer.py"]:
            package.write(path, path.name)
    print(f"Built {SITE}")


if __name__ == "__main__":
    build()
