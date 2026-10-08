"""Build/refresh generated symbols into the sitara-* libraries. Deterministic and re-runnable.

  python build_symbols.py [--build-dir DIR] [--check]

For each target library in symbols_spec.LIBS:
  1. write the generated symbols as a temporary library (KiCad 8 syntax) in the build dir
  2. `kicad-cli sym upgrade --force` normalizes it to the current KiCad 10 format
  3. splice each normalized (symbol ...) block into the target library:
       - existing symbols that are NOT in the spec are preserved byte-for-byte (CRLF kept),
         except symbols named in symbols_spec.RETIRED, which are removed
       - symbols with the same name as a spec entry are replaced (re-run safe)
       - a missing target library is created with a KiCad 10 header
  4. `kicad-cli sym export svg` of every target library proves it still loads.
--check only reports what would change.
"""
import argparse, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from kicad_sym_writer import library_text  # noqa: E402
from symbols_spec import SYMBOLS, LIBS  # noqa: E402
try:
    from symbols_spec import RETIRED
except ImportError:
    RETIRED = []

KICAD_CLI = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
HEADER = "(kicad_symbol_lib\r\n\t(version 20251024)\r\n\t(generator \"kicad_symbol_editor\")\r\n\t(generator_version \"10.0\")\r\n"


def top_level_symbols(text):
    """Return list of (name, start, end) for top-level (symbol "NAME" ...) blocks in a library."""
    out = []
    i = 0
    while True:
        m = re.compile(r'\(symbol "([^"]+)"').search(text, i)
        if not m:
            return out
        # only top-level: depth 1 relative to the library's opening paren
        depth = 0
        j = m.start()
        while True:
            c = text[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        out.append((m.group(1), m.start(), j + 1))
        i = j + 1


def normalized_blocks(lib_name, symbols, build_dir):
    tmp = os.path.join(build_dir, f"{lib_name}.generated.kicad_sym")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(library_text(symbols))
    r = subprocess.run([KICAD_CLI, "sym", "upgrade", "--force", tmp], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"kicad-cli sym upgrade failed for {tmp}: {r.stdout} {r.stderr}")
    text = open(tmp, encoding="utf-8", newline="").read()
    # kicad writes LF; indent blocks one tab and convert to CRLF to match the existing libraries
    blocks = {}
    for name, a, b in top_level_symbols(text):
        blk = text[a:b].replace("\r\n", "\n")
        blk = "\t" + blk.replace("\n", "\r\n") + "\r\n"
        blocks[name] = blk
    return blocks


def splice(target_path, blocks, check=False):
    if os.path.exists(target_path):
        orig = open(target_path, encoding="utf-8", newline="").read()
    else:
        orig = HEADER + ")\r\n"
    assert orig.rstrip().endswith(")"), target_path
    # remove previously generated copies of our symbols (re-run), preserving everything else
    text = orig
    for name, a, b in reversed(top_level_symbols(orig)):
        if name in blocks or name in RETIRED:
            # include the preceding indentation and following newline
            a0 = text.rfind("\n", 0, a) + 1
            b0 = b
            if text[b0:b0 + 2] == "\r\n":
                b0 += 2
            elif text[b0:b0 + 1] == "\n":
                b0 += 1
            text = text[:a0] + text[b0:]
    close = text.rstrip()
    assert close.endswith(")")
    body = close[:-1].rstrip("\r\n") + "\r\n"
    new = body + "".join(blocks[n] for n in blocks) + ")\r\n"
    changed = new != orig
    if changed and not check:
        with open(target_path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
    return changed


def verify_loads(lib_path, build_dir):
    out = os.path.join(build_dir, "svg", os.path.basename(lib_path))
    os.makedirs(out, exist_ok=True)
    r = subprocess.run([KICAD_CLI, "sym", "export", "svg", "-o", out, lib_path], capture_output=True, text=True)
    n = len([f for f in os.listdir(out) if f.endswith(".svg")])
    return r.returncode == 0 and n > 0, n, (r.stdout + r.stderr).strip()[-200:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-dir", default=os.path.join(tempfile.gettempdir(), "sitara_symgen_build"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.build_dir, exist_ok=True)
    for lib in LIBS:
        syms = {n: s for n, s in SYMBOLS.items() if s["lib"] == lib}
        blocks = normalized_blocks(lib, syms, a.build_dir)
        target = os.path.join(LIB_DIR, f"{lib}.kicad_sym")
        changed = splice(target, blocks, a.check)
        state = ("would change" if changed else "up to date") if a.check else ("updated" if changed else "unchanged")
        print(f"{lib}: {len(blocks)} generated symbols; {state}")
        if not a.check:
            ok, n, msg = verify_loads(target, a.build_dir)
            print(f"  loads in kicad-cli: {'OK' if ok else 'FAILED'} ({n} symbols exported) {msg if not ok else ''}")
            if not ok:
                raise SystemExit(1)


if __name__ == "__main__":
    main()
