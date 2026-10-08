"""Generic build pipeline for an AV drawing made with sitara_av.

    generate -> kicad-cli sch upgrade -> ERC -> netlist + BOM -> format / PCIe checks -> PDF + SVG + PNG exports
    (+ a black-and-white-safe "print" variant that tells formats apart by line pattern instead of color)

A project supplies a `generate(mode)` callback that writes its .kicad_sch files ("color" or "print") and a BuildConfig.
"""
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Callable

from . import checks, palette, theme


def kicad_cli():
    env = os.environ.get("KICAD_CLI")
    if env:
        return env
    found = shutil.which("kicad-cli")
    if found:
        return found
    for p in (r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe", "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"):
        if os.path.exists(p):
            return p
    raise SystemExit("kicad-cli not found: install KiCad 10 or set KICAD_CLI")


def run(args, quiet=False):
    r = subprocess.run([kicad_cli()] + args, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if not quiet:
        print("  $ kicad-cli", " ".join(args[:4]), "->", out.splitlines()[-1] if out else "ok")
    return r


@dataclass
class BuildConfig:
    proj_dir: str
    name: str                       # project name; the root sheet is <name>.kicad_sch
    sheets: list                    # every .kicad_sch filename in the project, root first
    generate: Callable              # generate(mode) writes the sheets
    rev: str = "A"
    worksheet: str = ""             # path (usually ${KIPRJMOD}-relative) of the drawing sheet .kicad_wks
    block_schs: list = field(default_factory=list)   # design block schematics to upgrade too
    modes: tuple = ("color", "print")
    theme_version: str = "10.0"
    png_dpi: int = 110

    @property
    def root_sch(self):
        return os.path.join(self.proj_dir, self.sheets[0])

    @property
    def out(self):
        return os.path.join(self.proj_dir, "exports", f"Rev{self.rev}")


def write_project(cfg):
    """Project file: Sitara drawing sheet + on-screen net classes (CLI plots use the explicit wire colors)."""
    pro = os.path.join(cfg.proj_dir, f"{cfg.name}.kicad_pro")
    data = {}
    if os.path.exists(pro):
        try:
            data = json.load(open(pro, encoding="utf-8"))
        except Exception:
            data = {}
    data.setdefault("meta", {"filename": f"{cfg.name}.kicad_pro", "version": 3})
    sch = data.setdefault("schematic", {})
    if cfg.worksheet:
        sch["page_layout_descr_file"] = cfg.worksheet
    sch.setdefault("legacy_lib_dir", "")
    sch.setdefault("legacy_lib_list", [])

    def cls(name, color, width=6, bus=12):
        return {"name": name, "schematic_color": color, "wire_width": width, "bus_width": bus, "line_style": 0, "clearance": 0.2,
                "track_width": 0.2, "via_diameter": 0.6, "via_drill": 0.3, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "pcb_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647}

    classes = [cls("Default", "rgba(0, 0, 0, 0.000)")]
    patterns = []
    for f in palette.FORMATS:
        if f.netclass_patterns:
            classes.append(cls(f.key, palette.rgb_css(f.key)))
            patterns += [{"netclass": f.key, "pattern": p} for p in f.netclass_patterns]
    data["net_settings"] = {"meta": {"version": 4}, "classes": classes, "netclass_patterns": patterns}
    with open(pro, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def upgrade_all(cfg):
    for s in cfg.sheets:
        run(["sch", "upgrade", os.path.join(cfg.proj_dir, s)], quiet=True)
    for b in cfg.block_schs:
        run(["sch", "upgrade", b], quiet=True)


def erc(cfg):
    out = cfg.out
    run(["sch", "erc", "--severity-all", "--format", "json", "-o", os.path.join(out, "erc.json"), cfg.root_sch], quiet=True)
    run(["sch", "erc", "--severity-all", "-o", os.path.join(out, "erc.txt"), cfg.root_sch], quiet=True)
    data = json.load(open(os.path.join(out, "erc.json"), encoding="utf-8"))
    counts = {}
    for sh in data["sheets"]:
        for v in sh["violations"]:
            counts[(v["severity"], v["type"])] = counts.get((v["severity"], v["type"]), 0) + 1
    return counts


def build(cfg, no_gen=False, strict=False):
    """Run the whole pipeline. Returns a summary dict; with strict=True exits non-zero on ERC violations or check problems."""
    os.makedirs(cfg.out, exist_ok=True)
    name = cfg.name
    if not no_gen:
        print("generate (color)")
        cfg.generate("color")
        write_project(cfg)
        upgrade_all(cfg)
    print("ERC")
    counts = erc(cfg)
    for k, v in sorted(counts.items()):
        print(f"  {v:4d} {k[0]:8s} {k[1]}")
    if not counts:
        print("  no violations")
    print("netlist / BOM / checks")
    xml = os.path.join(cfg.out, f"{name}.xml")
    run(["sch", "export", "netlist", "--format", "kicadxml", "-o", xml, cfg.root_sch], quiet=True)
    run(["sch", "export", "netlist", "--format", "kicadsexpr", "-o", os.path.join(cfg.out, f"{name}.net"), cfg.root_sch], quiet=True)
    run(["sch", "export", "bom", "--fields", "Reference,Value,Model,Role,Status,QUANTITY", "--group-by", "Value,Role,Status",
         "-o", os.path.join(cfg.out, "bom.csv"), cfg.root_sch], quiet=True)
    problems = checks.all_checks(xml)
    print(f"  format / PCIe checks: {'OK' if not problems else 'PROBLEMS'}")
    for p in problems:
        print("   !", p)
    print("exports")
    th = theme.install_theme(cfg.theme_version)
    targs = ["--theme", th] if th else []
    pdf = os.path.join(cfg.out, f"{name}.pdf")
    run(["sch", "export", "pdf", "--draw-hop-over"] + targs + ["-o", pdf, cfg.root_sch], quiet=True)
    svgdir = os.path.join(cfg.out, "svg")
    shutil.rmtree(svgdir, ignore_errors=True)
    run(["sch", "export", "svg", "--draw-hop-over"] + targs + ["-o", svgdir, cfg.root_sch], quiet=True)
    pngdir = os.path.join(cfg.out, "png")
    shutil.rmtree(pngdir, ignore_errors=True)
    os.makedirs(pngdir, exist_ok=True)
    if shutil.which("pdftoppm"):
        subprocess.run(["pdftoppm", "-r", str(cfg.png_dpi), "-png", pdf, os.path.join(pngdir, "sheet")])
    if "print" in cfg.modes and not no_gen:
        print("print variant (black and white, formats told apart by line pattern)")
        cfg.generate("print")
        upgrade_all(cfg)
        run(["sch", "export", "pdf", "--draw-hop-over", "--black-and-white"] + targs +
            ["-o", os.path.join(cfg.out, f"{name}-print.pdf"), cfg.root_sch], quiet=True)
        cfg.generate("color")          # leave the project files in their normal (color) state
        upgrade_all(cfg)
    print("done ->", cfg.out)
    summary = {"erc": {f"{k[0]}:{k[1]}": v for k, v in counts.items()}, "problems": problems}
    if strict and (counts or problems):
        sys.exit(1)
    return summary
