"""Regenerate templates/sitara-av-project, the KiCad "New Project from Template" version of new_project.py.

    python tools/build_template.py

Use it in KiCad: copy (or point KiCad's template path at) templates/sitara-av-project, and define the path variable
SITARA_KICAD = the folder of this repository (Preferences > Configure Paths). The template carries the starter drawing
and library tables only; for the generator, ERC/checks/exports pipeline use tools/new_project.py instead.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import new_project  # noqa: E402

NAME = "sitara-av-project"
INFO = """<!DOCTYPE html>
<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"><title>Sitara AV signal flow</title></head>
<body>
<h2>Sitara AV signal flow</h2>
<p>A3 signal-flow sheet with the Sitara drawing sheet, symbol libraries (sitara-*) and design blocks (sitara-render-nodes, sitara-av-blocks).</p>
<p>Requires the path variable <b>SITARA_KICAD</b> pointing at the sitara-kicad repository folder.
Install the Sitara color theme from <i>themes/</i> for the intended look.</p>
</body></html>
"""


def main():
    out = os.path.join(REPO, "templates", NAME)
    tmp = tempfile.mkdtemp()
    try:
        proj = os.path.join(tmp, NAME)
        r = subprocess.run([sys.executable, os.path.join(HERE, "new_project.py"), proj, "--name", NAME, "--build"], capture_output=True, text=True)
        if r.returncode:
            print(r.stdout, r.stderr)
            raise SystemExit("scaffold failed")
        shutil.rmtree(out, ignore_errors=True)
        os.makedirs(os.path.join(out, "meta"))
        sym, blk = new_project.lib_tables("${SITARA_KICAD}")
        for fn, text in (("sym-lib-table", sym), ("design-block-lib-table", blk)):
            open(os.path.join(out, fn), "w", encoding="utf-8", newline="\n").write(text)
        shutil.copy(os.path.join(proj, NAME + ".kicad_sch"), os.path.join(out, NAME + ".kicad_sch"))
        shutil.copy(os.path.join(proj, "tbc.kicad_sch"), os.path.join(out, "tbc.kicad_sch"))
        pro = json.load(open(os.path.join(proj, NAME + ".kicad_pro"), encoding="utf-8"))
        pro["schematic"]["page_layout_descr_file"] = "${SITARA_KICAD}/worksheet_template/template.kicad_wks"
        json.dump(pro, open(os.path.join(out, NAME + ".kicad_pro"), "w", encoding="utf-8", newline="\n"), indent=2)
        open(os.path.join(out, "meta", "info.html"), "w", encoding="utf-8", newline="\n").write(INFO)
        icon = os.path.join(REPO, "worksheet_template", "sitara-logo.png")
        if os.path.exists(icon):
            shutil.copy(icon, os.path.join(out, "meta", "icon.png"))
        print("wrote", os.path.relpath(out, REPO))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
