"""Regenerate every design block in av_blocks/ from tools/sitara_av/blocks.py, upgrade them to the current KiCad format
and check that KiCad can open and plot each one.

    python tools/build_blocks.py            # write + upgrade + plot-check
    python tools/build_blocks.py --check    # fail if the files on disk differ from what the generator writes (for CI)
"""
import argparse
import filecmp
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from sitara_av import blocks  # noqa: E402
from sitara_av.build import run  # noqa: E402


def build(out_root, upgrade=True):
    paths = []
    for lib, name, fn, desc, kw in blocks.BLOCKS:
        lib_dir = os.path.join(out_root, lib + ".kicad_blocks")
        p = blocks.write_block(lib_dir, name, fn, desc, kw)
        if upgrade:
            run(["sch", "upgrade", p], quiet=True)
        paths.append(p)
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    dest = os.path.join(REPO, "av_blocks")
    if a.check:
        tmp = tempfile.mkdtemp()
        try:
            build(tmp)
            bad = []
            for lib, name, *_ in blocks.BLOCKS:
                for ext in (".kicad_sch", ".json"):
                    rel = os.path.join(lib + ".kicad_blocks", name + ".kicad_block", name + ext)
                    if not os.path.exists(os.path.join(dest, rel)) or not filecmp.cmp(os.path.join(tmp, rel), os.path.join(dest, rel), shallow=False):
                        bad.append(rel)
            if bad:
                print("design blocks out of date (run python tools/build_blocks.py):", *bad, sep="\n  ")
                sys.exit(1)
            print("design blocks up to date")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return
    paths = build(dest)
    scratch = tempfile.mkdtemp()
    try:
        for p in paths:
            r = run(["sch", "export", "pdf", "-o", os.path.join(scratch, os.path.basename(p) + ".pdf"), p], quiet=True)
            ok = r.returncode == 0
            print(("  ok   " if ok else "  FAIL ") + os.path.relpath(p, REPO))
            if not ok:
                sys.exit(1)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    main()
