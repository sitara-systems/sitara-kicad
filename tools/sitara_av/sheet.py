"""Deterministic KiCad schematic writer for AV signal-flow drawings.

Writes KiCad 8-era syntax; `sitara_av.build` upgrades every sheet with `kicad-cli sch upgrade`. UUIDs are uuid5 of stable
keys, so regenerating gives byte-identical files. Sizes (text 1.78 mm, pin pitch 3.81 mm) come from the symbol writer.
"""
import math
import os
import sys
import uuid
from dataclasses import dataclass, field, replace

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
LIBGEN = os.path.join(REPO, "av_components", "_generator")
if LIBGEN not in sys.path:
    sys.path.insert(0, LIBGEN)
from kicad_sym_writer import symbol_text, pin_pos, pin_number, body_half_height, TEXT as T  # noqa: E402
from symbols_spec import SYMBOLS  # noqa: E402

from . import overlap, palette  # noqa: E402

UNIT = 1.27
NOTE = 2.29  # comment / note text: 1.3x the symbol text size T, so notes stay readable when a sheet is printed on A4 or Letter


def gr(x):
    """Snap a coordinate to the 1.27 mm connection grid."""
    return round(round(x / UNIT) * UNIT, 2)


def q(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


@dataclass
class Context:
    """Per-project settings shared by all sheets of one drawing."""
    project: str
    out_dir: str
    rev: str = "A"
    date: str = ""
    company: str = ""
    comment: str = ""
    namespace: str = "6f1d4d2a-5b7e-4c7e-9b1c-0000000a0001"   # change per project; keeps UUIDs stable
    mode: str = "color"          # "color" or "print"
    uuids: dict = field(default_factory=dict)

    def uid(self, key):
        return str(uuid.uuid5(uuid.UUID(self.namespace), key))

    def variant(self, **kw):
        return replace(self, **kw)


class Sheet:
    def __init__(self, ctx, fname, title, paper, path_uuid, parent_path="/"):
        self.ctx = ctx
        self.fname, self.title, self.paper = fname, title, paper
        self.uuid = path_uuid
        self.path = parent_path.rstrip("/") + "/" + path_uuid  # instance path; the root overrides to "/<root>"
        self.page = "1"
        self.items = []
        self.used_libs = set()
        self.rects = []    # (kind, label, rect) for the overlap check
        self.placed = []   # (ref, symbol name, merged fields) of every symbol placed, for power.budget()
        self.n = 0

    def key(self, s):
        self.n += 1
        return self.ctx.uid(f"{self.fname}:{s}:{self.n}")

    # --- symbols
    def place(self, name, ref, at, fields=None, show=("PreferredModel",), lib=None):
        spec = SYMBOLS[name]
        lib = lib or spec["lib"]
        self.used_libs.add((lib, name))
        x, y = at
        hw, hh = spec["w"] / 2, body_half_height(spec)
        fh = f"(effects (font (size {T} {T})) hide)"
        props = [f'(property "Reference" "{ref}" (at {x - hw:.2f} {y - hh - 0.76:.2f} 0) (effects (font (size {T} {T})) (justify left bottom)))',
                 f'(property "Value" "{name}" (at {x - hw:.2f} {y + hh + 0.76:.2f} 0) (effects (font (size {T} {T})) (justify left top)))',
                 f'(property "Footprint" "" (at {x} {y} 0) {fh})', f'(property "Datasheet" "" (at {x} {y} 0) {fh})',
                 f'(property "Description" "{q(spec.get("desc", ""))}" (at {x} {y} 0) {fh})']
        allf = dict(spec.get("fields", {}))
        allf.update(fields or {})
        self.placed.append((ref, name, dict(allf), bool(spec.get("exclude_bom"))))
        self.rects.append(("body", f"{ref} body", (x - hw, y - hh, x + hw, y + hh)))
        self.rects.append(("text", f"{ref} reference", overlap.text_rect(ref, x - hw, y - hh - 0.76, T, "bottom")))
        self.rects.append(("text", f"{ref} {name}", overlap.text_rect(name, x - hw, y + hh + 0.76, T, "top")))
        for _row, _k in enumerate([k for k in allf if k in show], 1):
            self.rects.append(("text", f"{ref} {_k}", overlap.text_rect(str(allf[_k]), x - hw, y + hh + 0.76 + 3.0 * _row, T, "top")))
        row = 1
        for k, v in allf.items():
            if k in show:
                props.append(f'(property "{k}" "{q(v)}" (at {x - hw:.2f} {y + hh + 0.76 + 3.0 * row:.2f} 0) (effects (font (size {T} {T})) (justify left top)))')
                row += 1
            else:
                props.append(f'(property "{k}" "{q(v)}" (at {x} {y} 0) {fh})')
        pins = " ".join(f'(pin "{pin_number(spec, p[0])}" (uuid "{self.key(ref + p[0])}"))' for p in spec["pins"])
        self.items.append(f'(symbol (lib_id "{lib}:{name}") (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom {"no" if spec.get("exclude_bom") else "yes"}) (on_board yes) (dnp no) (uuid "{self.key(ref)}")\n'
                          + "\n".join(props) + f'\n{pins}\n(instances (project "{self.ctx.project}" (path "{self.path}" (reference "{ref}") (unit 1)))))')
        return Inst(name, at)

    # --- primitives
    def _stroke(self, fmt):
        f = palette.BY_KEY[fmt]
        if self.ctx.mode == "print":
            return f"(stroke (width {f.print_width}) (type {f.print_type}) (color 0 0 0 1))"
        dash = " (type dash)" if f.dashed else " (type default)"
        return f"(stroke (width 0){dash} (color {palette.rgb_str(fmt)} 1))"

    def wire(self, pts, fmt="PCIE"):
        for a, b in zip(pts, pts[1:]):
            self.items.append(f'(wire (pts (xy {a[0]:.2f} {a[1]:.2f}) (xy {b[0]:.2f} {b[1]:.2f})) {self._stroke(fmt)} (uuid "{self.key("w")}"))')

    def bus(self, pts, fmt=None):
        if fmt is None:
            col, wid, typ = "", 0, "default"
        elif self.ctx.mode == "print":
            f = palette.BY_KEY[fmt]
            col, wid, typ = " (color 0 0 0 1)", f.print_width, f.print_type
        else:
            col, wid, typ = f" (color {palette.rgb_str(fmt)} 1)", 0, "default"
        for a, b in zip(pts, pts[1:]):
            self.items.append(f'(bus (pts (xy {a[0]:.2f} {a[1]:.2f}) (xy {b[0]:.2f} {b[1]:.2f})) (stroke (width {wid}) (type {typ}){col}) (uuid "{self.key("b")}"))')

    def entry(self, x, y, dx=2.54, dy=2.54):
        self.items.append(f'(bus_entry (at {x:.2f} {y:.2f}) (size {dx} {dy}) (stroke (width 0) (type default)) (uuid "{self.key("e")}"))')

    def junction(self, x, y):
        self.items.append(f'(junction (at {x:.2f} {y:.2f}) (diameter 0) (color 0 0 0 0) (uuid "{self.key("j")}"))')

    def label(self, t, x, y, ang=0):
        j = "left" if ang == 0 else "right"
        self.items.append(f'(label "{t}" (at {x:.2f} {y:.2f} {ang}) (fields_autoplaced yes) (effects (font (size {T} {T})) (justify {j} bottom)) (uuid "{self.key("l")}"))')

    def glabel(self, t, x, y, ang=180, shape="input"):
        j = "left" if ang == 0 else "right"
        self.items.append(f'(global_label "{t}" (shape {shape}) (at {x:.2f} {y:.2f} {ang}) (fields_autoplaced yes) (effects (font (size {T} {T})) (justify {j})) (uuid "{self.key("g")}"))')

    def hlabel(self, t, x, y, ang=180, shape="input"):
        j = "left" if ang == 0 else "right"
        self.items.append(f'(hierarchical_label "{t}" (shape {shape}) (at {x:.2f} {y:.2f} {ang}) (fields_autoplaced yes) (effects (font (size {T} {T})) (justify {j})) (uuid "{self.key("h")}"))')

    def nc(self, pt):
        self.items.append(f'(no_connect (at {pt[0]:.2f} {pt[1]:.2f}) (uuid "{self.key("n")}"))')

    def text(self, t, x, y, size=T, bold=False, color=None):
        size = NOTE if size == T else size
        b = " bold" if bold else ""
        c = f" (color {color} 1)" if color else ""
        self.rects.append(("text", t, overlap.text_rect(t, x, y, size, "bottom", bold)))
        self.items.append(f'(text "{q(t)}" (exclude_from_sim no) (at {x:.2f} {y:.2f} 0) (effects (font (size {size} {size}){b}{c}) (justify left bottom)) (uuid "{self.key("t")}"))')

    def text_box(self, t, x, y, w, h, size=T, frame=False):
        size = NOTE if size == T else size
        if frame:   # a titled frame that other text is placed inside: only its heading counts
            self.rects.append(("text", t, overlap.text_rect(t, x + 0.8, y + 0.8, size, "top")))
        else:
            self.rects.append(("box", t, (x, y, x + w, y + h)))
        """Single paragraph (KiCad wraps it); embedded newlines are not accepted by the parser."""
        self.items.append(f'(text_box "{q(t)}" (exclude_from_sim no) (at {x:.2f} {y:.2f} 0) (size {w} {h}) (stroke (width 0.2) (type solid)) (fill (type none)) '
                          f'(effects (font (size {size} {size})) (justify left top)) (uuid "{self.key("tb")}"))')

    def notes(self, paragraphs, x, y, w, size=T):
        size = NOTE if size == T else size
        """Stack of auto-wrapping boxes, one per paragraph. Returns the bottom y."""
        cpl = max(20, int(w / (size * 1.02)))
        for t in paragraphs:
            lines = max(1, math.ceil(len(t) / cpl))
            h = round(lines * size * 1.75 + 2.2, 2)
            self.text_box(t, x, y, w, h, size)
            y += h
        return y

    def line(self, pts, color, dash=False, width=0.6, stroke_type=None):
        pts_s = " ".join(f"(xy {x:.2f} {y:.2f})" for x, y in pts)
        typ = stroke_type or ("dash" if dash else "default")
        self.items.append(f'(polyline (pts {pts_s}) (stroke (width {width}) (type {typ}) (color {color} 1)) (uuid "{self.key("pl")}"))')

    def legend(self, x, y, w=95.0, formats=None):
        """Legend box for the wire formats, grouped video | audio + USB | network, reference, PCIe. Returns the bottom y."""
        keys = formats or palette.LEGEND_ORDER
        self.text_box("LEGEND", x, y, w, 60.0, T, frame=True)
        prev = None
        extra = 0.0
        for i, k in enumerate(keys):
            f = palette.BY_KEY[k]
            if prev is not None and f.group != prev:
                extra += 1.5
            prev = f.group
            yy = y + 8.0 + i * 5.4 + extra
            if self.ctx.mode == "print":
                self.line([(x + 3.0, yy), (x + 18.0, yy)], "0 0 0", width=f.print_width, stroke_type=f.print_type)
            else:
                self.line([(x + 3.0, yy), (x + 18.0, yy)], palette.rgb_str(k), f.dashed)
            self.text(f.label, x + 21.0, yy + 1.2, T)
        return y + 60.0

    def subsheet(self, sub, at, size, pins):
        """pins: [(name, 'input'|'output', side 'L'|'R', y_offset)]"""
        x, y = at
        w, h = size
        ps = []
        for name, shape, side, dy in pins:
            px = x if side == "L" else x + w
            ang, j = (180, "left") if side == "L" else (0, "right")
            ps.append(f'(pin "{name}" {shape} (at {px:.2f} {y + dy:.2f} {ang}) (effects (font (size {T} {T})) (justify {j})) (uuid "{self.key("sp" + name)}"))')
        self.rects.append(("body", f"sheet {sub.title}", (x, y, x + w, y + h)))
        self.rects.append(("text", f"sheet name {sub.title}", overlap.text_rect(sub.title, x, y - 0.76, 2.4, "bottom", True)))
        self.rects.append(("text", f"sheet file {sub.fname}", overlap.text_rect("File: " + sub.fname, x, y + h + 0.76, T, "top")))
        self.items.append(f'''(sheet (at {x:.2f} {y:.2f}) (size {w} {h}) (fields_autoplaced yes) (stroke (width 0.25) (type solid)) (fill (color 0 0 0 0.0000)) (uuid "{sub.uuid}")
(property "Sheetname" "{sub.title}" (at {x:.2f} {y - 0.76:.2f} 0) (effects (font (size 2.4 2.4) bold) (justify left bottom)))
(property "Sheetfile" "{sub.fname}" (at {x:.2f} {y + h + 0.76:.2f} 0) (effects (font (size {T} {T})) (justify left top)))
{chr(10).join(ps)}
(instances (project "{self.ctx.project}" (path "{self.path}" (page "{sub.page}")))))''')

    # --- file
    def write(self, root=False, out_dir=None):
        c = self.ctx
        overlap.WARNINGS.extend(overlap.check(self))
        lib_syms = "\n".join(symbol_text(n, SYMBOLS[n], lib_prefix=f"{lib}:") for lib, n in sorted(self.used_libs))
        head = (f'(kicad_sch (version 20231120) (generator "sitara_schgen") (generator_version "8.0")\n(uuid "{self.uuid}")\n(paper "{self.paper}")\n'
                f'(title_block (title "{q(self.title)}") (date "{c.date}") (rev "{c.rev}") (company "{q(c.company)}") (comment 1 "{q(c.comment)}"))\n'
                f'(lib_symbols\n{lib_syms}\n)')
        tail = '(sheet_instances (path "/" (page "1")))\n)' if root else ")"
        d = out_dir or c.out_dir
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, self.fname), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join([head] + self.items + [tail]) + "\n")


class Inst:
    def __init__(self, name, at):
        self.spec, self.at = SYMBOLS[name], at

    def pin(self, pname):
        px, py = pin_pos(self.spec, pname)
        return (round(self.at[0] + px, 2), round(self.at[1] - py, 2))
