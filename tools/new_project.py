"""Create a new AV signal-flow project that uses the Sitara libraries, theme, drawing sheet and generator.

    python tools/new_project.py ..\\MyShow --name MyShow            # scaffold only
    python tools/new_project.py ..\\MyShow --name MyShow --build    # scaffold, then generate + ERC + checks + exports
    python tools/new_project.py ..\\MyShow --name MyShow --build --strict

The new folder gets: <name>.kicad_pro, sym-lib-table and design-block-lib-table (paths relative to this repo), and
_generator/{gen_schematic.py,build_all.py}. The starting drawing is one sheet with the render-node design block, a
placeholder reference generator and the house network placeholder. Edit gen_schematic.py, never the .kicad_sch files.
Also installs the Sitara KiCad color theme on first use (restart KiCad once to see it).
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from sitara_av import theme  # noqa: E402

LIBS = [("sitara-audio", "audio"), ("sitara-cameras", "cameras"), ("sitara-computers", "computers"), ("sitara-displays", "displays"),
        ("sitara-hardware", "hardware"), ("sitara-hid", "hid"), ("sitara-networking", "networking"), ("sitara-power", "power"),
        ("sitara-skies", "skies"), ("sitara-video", "video processing, distribution, media servers, sync")]
BLOCK_LIBS = [("sitara-render-nodes", "Sitara render node assemblies"), ("sitara-av-blocks", "Sitara AV assemblies (processing stacks, surveyor node, audio)")]


def lib_tables(base, symbols_root=None):
    """base: path prefix to the sitara-kicad repo as written in the table, e.g. ${KIPRJMOD}/../sitara-kicad or ${SITARA_KICAD}."""
    sym = ["(sym_lib_table", "  (version 7)"]
    for name, d in LIBS:
        sym.append(f'  (lib (name "{name}")(type "KiCad")(uri "{base}/av_components/{name}.kicad_sym")(options "")(descr "Sitara AV: {d}"))')
    sym.append(")")
    blk = ["(design_block_lib_table", "  (version 7)"]
    for name, d in BLOCK_LIBS:
        blk.append(f'  (lib (name "{name}")(type "KiCad")(uri "{base}/av_blocks/{name}.kicad_blocks")(options "")(descr "{d}"))')
    blk.append(")")
    return "\n".join(sym) + "\n", "\n".join(blk) + "\n"


GEN = '''"""Generate the {name} KiCad schematic with the sitara_av package from sitara-kicad.

Edit this file, then run build_all.py. Deterministic: UUIDs are uuid5 of stable keys, so unchanged content gives identical files.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
sys.path.insert(0, {tools_path})
from sitara_av import Context, Sheet, T, gr  # noqa: E402
from sitara_av import blocks  # noqa: E402

NS = "{namespace}"


def make_context(mode="color"):
    return Context(project="{name}", out_dir=PROJ, rev="A", date="{date}", company="{company}",
                   comment="Dashed outline = placeholder", namespace=NS, mode=mode)


def system(ctx):
    s = Sheet(ctx, "{name}.kicad_sch", "{name} - signal flow", "A3", ctx.uid("root"), "")
    s.page = "1"
    s.text("{name}: render node, reference and network (starting point - replace with the real system).", 20.32, 22.86, 3.2, True)
    # Reusable assembly; the same drawing is available in KiCad as the RENDER_NODE_A design block.
    blocks.render_node_a(s, usb_rear1_free=True, sdi_bus_end="label")
    # Placeholders for what the block's global labels connect to.
    ref = s.place("SYNC_GENERATOR_TBC", "REF1", (gr(360), gr(55)), show=("Model", "Status"))
    p = ref.pin("REF-OUT-1"); s.wire([p, (p[0] + 5.08, p[1])], "REF"); s.glabel("REF", p[0] + 5.08, p[1], 0, "output")
    for k in range(2, 5):
        s.nc(ref.pin("REF-OUT-" + str(k)))
    net = s.place("NETWORK_HOUSE_LAN_TBC", "NET1", (gr(375), gr(110)), show=("Model", "Status"))
    for pn in ("NET-MGMT", "NET-SHOW"):
        p = net.pin(pn); s.wire([p, (p[0] - 5.08, p[1])], "NET"); s.glabel(pn, p[0] - 5.08, p[1], 180, "bidirectional")
    s.nc(net.pin("NET-LED")); s.nc(net.pin("NET-UPLINK"))
    srv = s.place("MEDIASERVER_RESOLUME_HOUSE", "SRV1", (gr(370), gr(170)), {{"Role": "Primary"}}, show=("Role",))
    for k in range(1, 5):
        p = srv.pin("SDI-IN-" + str(k)); s.wire([p, (p[0] - 12.7, p[1])], "SDI"); s.label("SDI" + str(k), p[0] - 12.7, p[1])
    for pn in ("REF-IN", "LAN"):
        s.nc(srv.pin(pn))
    for k in range(1, 6):
        s.nc(srv.pin("DP-OUT-" + str(k))); s.nc(srv.pin("HDMI-OUT-" + str(k)))
    return s


def generate(mode="color"):
    """Write every sheet. mode = 'color' (normal) or 'print' (black wires told apart by line pattern)."""
    ctx = make_context(mode)
    root = system(ctx)
    root.write(root=True)
    return [root.fname]


if __name__ == "__main__":
    print("wrote", generate("color"))
'''

BUILD = '''"""Regenerate, upgrade, verify and export the {name} drawing with sitara_av.build.

  python build_all.py            -> generate + upgrade + ERC + netlist + checks + exports/RevA (color and print PDFs)
  python build_all.py --no-gen   -> verify / export the files as they are
  python build_all.py --strict   -> exit non-zero on ERC violations or check problems
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, {tools_path})
from sitara_av.build import BuildConfig, build  # noqa: E402
import gen_schematic  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-gen", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--rev", default="A")
    a = ap.parse_args()
    cfg = BuildConfig(proj_dir=PROJ, name="{name}", sheets=["{name}.kicad_sch"], generate=gen_schematic.generate, rev=a.rev,
                      worksheet={worksheet})
    build(cfg, no_gen=a.no_gen, strict=a.strict)


if __name__ == "__main__":
    main()
'''


def rel(dest, target):
    try:
        return os.path.relpath(target, dest).replace("\\", "/")
    except ValueError:  # different drive on Windows
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dest", help="folder to create")
    ap.add_argument("--name", required=True, help="project name (becomes <name>.kicad_pro / .kicad_sch)")
    ap.add_argument("--company", default="Sitara Systems")
    ap.add_argument("--build", action="store_true", help="run _generator/build_all.py afterwards")
    ap.add_argument("--strict", action="store_true", help="with --build: fail on ERC violations or check problems")
    ap.add_argument("--force", action="store_true", help="allow a non-empty destination")
    a = ap.parse_args()

    dest = os.path.abspath(a.dest)
    if os.path.exists(dest) and os.listdir(dest) and not a.force:
        raise SystemExit(f"{dest} is not empty (use --force to scaffold into it anyway)")
    name = a.name
    if not name.replace("_", "").replace("-", "").isalnum():
        raise SystemExit("project name: letters, digits, - and _ only")
    os.makedirs(os.path.join(dest, "_generator"), exist_ok=True)

    r = rel(dest, REPO)
    base = ("${KIPRJMOD}/" + r) if r else REPO.replace("\\", "/")
    sym, blk = lib_tables(base)
    tools_path = f"os.path.normpath(os.path.join(PROJ, {r!r}, 'tools'))" if r else repr(os.path.join(REPO, "tools"))
    ws = f'"${{KIPRJMOD}}/{r}/worksheet_template/template.kicad_wks"' if r else repr(os.path.join(REPO, "worksheet_template", "template.kicad_wks").replace("\\", "/"))

    import uuid
    ns = str(uuid.uuid5(uuid.NAMESPACE_URL, "sitara-av-project/" + name))
    import datetime
    files = {
        "sym-lib-table": sym,
        "design-block-lib-table": blk,
        os.path.join("_generator", "gen_schematic.py"): GEN.format(name=name, tools_path=tools_path, namespace=ns, company=a.company, date=datetime.date.today().isoformat()),
        os.path.join("_generator", "build_all.py"): BUILD.format(name=name, tools_path=tools_path, worksheet=ws),
    }
    for fn, text in files.items():
        with open(os.path.join(dest, fn), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    print(f"scaffolded {dest}")
    try:
        t = theme.install_theme()
        print(f"installed KiCad color theme '{t}' (restart KiCad once, then pick it in Preferences > Colors)")
    except Exception as e:  # theme is a nicety, never a blocker
        print(f"note: could not install the color theme ({e}); see themes/README.md")

    cmd = [sys.executable, os.path.join(dest, "_generator", "build_all.py")] + (["--strict"] if a.strict else [])
    if a.build:
        sys.exit(subprocess.run(cmd, cwd=dest).returncode)
    print(f"next: python {os.path.join(dest, '_generator', 'build_all.py')}   (then open {name}.kicad_pro in KiCad)")


if __name__ == "__main__":
    main()
