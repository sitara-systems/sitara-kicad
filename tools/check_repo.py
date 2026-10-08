"""Run every repository check (same list CI runs).

    python tools/check_repo.py            # all checks
    python tools/check_repo.py --fast     # skip the scaffold smoke test

1. generated symbols are up to date and every library loads in kicad-cli
2. generated design blocks are up to date
3. spec symbols follow the FORMAT-DIR-n pin convention and the palette knows every format
4. public-repo leak scan
5. (unless --fast) tools/new_project.py scaffolds a project that builds with a clean ERC and passing checks
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "av_components", "_generator"))

SINGLE_WORD_OK = {"LAN", "RS232"}  # control ports that carry no direction or index
PIN_OK = re.compile(r"^[A-Z0-9]+(?:\.[0-9])?(?:-[A-Z0-9.]+)+$")


def step(name, argv):
    print(f"== {name}")
    r = subprocess.run(argv, cwd=REPO)
    if r.returncode:
        print(f"   FAILED: {name}")
    return r.returncode == 0


def pin_convention():
    import symbols_spec
    bad = [(n, p[0]) for n, s in symbols_spec.SYMBOLS.items() for p in s["pins"] if not PIN_OK.match(p[0]) and not p[0].startswith("PCIe-") and p[0] not in SINGLE_WORD_OK]
    names = [(n, [p[0] for p in s["pins"]]) for n, s in symbols_spec.SYMBOLS.items()]
    dup = [(n, x) for n, ps in names for x in set(ps) if ps.count(x) > 1]
    for n, p in bad:
        print(f"   {n}: pin '{p}' is not FORMAT-DIR-n style")
    for n, p in dup:
        print(f"   {n}: duplicate pin name '{p}'")
    return not bad and not dup


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    a = ap.parse_args()
    py = sys.executable
    ok = True
    ok &= step("symbols up to date + libraries load", [py, "av_components/_generator/build_symbols.py", "--check"])
    ok &= step("design blocks up to date", [py, "tools/build_blocks.py", "--check"])
    print("== pin naming convention")
    good = pin_convention()
    ok &= good
    ok &= step("leak scan", [py, "tools/leak_scan.py"])
    if not a.fast:
        tmp = tempfile.mkdtemp()
        try:
            ok &= step("scaffold smoke test", [py, "tools/new_project.py", os.path.join(tmp, "SmokeTest"), "--name", "SmokeTest", "--build", "--strict"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    print("\nALL CHECKS PASSED" if ok else "\nCHECKS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
