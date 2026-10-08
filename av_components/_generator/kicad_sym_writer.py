"""Minimal, dependency-free writer for KiCad symbol text (AV signal-flow conventions).

Writes KiCad 8-era syntax (version 20231120); `kicad-cli sym upgrade --force` normalizes it
to the current KiCad 10 format. Also used by schematic generators to compute pin positions.

Conventions (pin names FORMAT-DIR-n; electrical type = role in the drawing):
  - inputs on the LEFT (pin angle 0), outputs on the RIGHT (pin angle 180)
  - pins stacked at 2.54 mm pitch, centred on the body; all geometry on the 1.27 mm grid
  - pin name = <FORMAT>-<DIR>-<n>; electrical type = role in the drawing
  - TBC placeholders get a dashed body outline
"""
import math

GRID = 2.54
FONT = "(effects (font (size 1.27 1.27)))"
FONT_HIDE = "(effects (font (size 1.27 1.27)) hide)"
STD_FIELDS = ("Reference", "Value", "Footprint", "Datasheet", "Description")


def _q(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def side_pins(spec, side):
    return [p for p in spec["pins"] if p[1] == side]


def body_half_height(spec):
    n = max(len(side_pins(spec, "L")), len(side_pins(spec, "R")), 1)
    return math.ceil((n * GRID + GRID) / GRID) * GRID / 2


def pin_pos(spec, name):
    """Connection point of pin `name` in symbol coordinates (y up)."""
    for side, sign in (("L", -1), ("R", 1)):
        col = side_pins(spec, side)
        top = (len(col) - 1) * GRID / 2
        for i, p in enumerate(col):
            if p[0] == name:
                return (sign * (spec["w"] / 2 + GRID), top - i * GRID)
    raise KeyError(name)


def pin_number(spec, name):
    for i, p in enumerate(spec["pins"], start=1):
        if p[0] == name:
            return str(i)
    raise KeyError(name)


def symbol_text(name, spec, lib_prefix=""):
    """Full (symbol ...) block. `lib_prefix` ('lib:') is used for schematic lib_symbols caches."""
    hh = body_half_height(spec)
    hw = spec["w"] / 2
    fields = dict(spec.get("fields", {}))
    desc = _q(spec.get("desc", ""))
    out = [f'(symbol "{lib_prefix}{name}" (exclude_from_sim no) (in_bom {"no" if spec.get("exclude_bom") else "yes"}) (on_board yes)']
    out.append(f'(property "Reference" "{spec["ref"]}" (at {-hw:.2f} {hh + 1.27:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))')
    out.append(f'(property "Value" "{name}" (at {-hw:.2f} {-(hh + 1.27):.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))')
    out.append(f'(property "Footprint" "" (at 0 0 0) {FONT_HIDE})')
    out.append(f'(property "Datasheet" "" (at 0 0 0) {FONT_HIDE})')
    out.append(f'(property "Description" "{desc}" (at 0 0 0) {FONT_HIDE})')
    visible = spec.get("visible", ())
    row = 2
    for k, v in fields.items():
        if k in STD_FIELDS:
            continue
        if k in visible:
            out.append(f'(property "{k}" "{_q(v)}" (at {-hw:.2f} {-(hh + 1.27 + 2.54 * (row - 1)):.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))')
            row += 1
        else:
            out.append(f'(property "{k}" "{_q(v)}" (at 0 0 0) {FONT_HIDE})')
    stroke_type = "dash" if spec.get("dashed") else "default"
    out.append(f'(symbol "{name}_0_1" (rectangle (start {-hw:.2f} {hh:.2f}) (end {hw:.2f} {-hh:.2f}) '
               f'(stroke (width 0.254) (type {stroke_type})) (fill (type background))))')
    out.append(f'(symbol "{name}_1_1"')
    for (pname, side, etype) in spec["pins"]:
        x, y = pin_pos(spec, pname)
        ang = 0 if side == "L" else 180
        out.append(f'(pin {etype} line (at {x:.2f} {y:.2f} {ang}) (length {GRID}) '
                   f'(name "{_q(pname)}" {FONT}) (number "{pin_number(spec, pname)}" {FONT}))')
    out.append("))")
    return "\n".join(out)


def library_text(symbols, generator="sitara_symgen"):
    body = "\n".join(symbol_text(n, s) for n, s in symbols.items())
    return f'(kicad_symbol_lib (version 20231120) (generator "{generator}") (generator_version "8.0")\n{body}\n)\n'
