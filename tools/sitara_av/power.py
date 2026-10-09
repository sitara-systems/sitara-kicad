"""Power budget from symbol fields, so the numbers are never typed by hand on a drawing.

Symbol fields (set in av_components/_generator/symbols_spec.py):
    PowerW            maximum draw in watts, a number as text ("300")
    PowerBasis        where it comes from: "vendor spec ..." or "estimate ..."
    PowerTypicalW     optional typical draw, with PowerTypicalBasis
    PowerIncludedIn   "host" for a part powered through another device (slot card, bus-powered USB gear);
                      it is listed but not added to the total

    from sitara_av import power
    b = power.budget(sheet)                       # after the symbols are placed
    power.note(sheet, x, y, volts=120)            # writes the lines and prints a warning for parts with no number

Placeholders (dashed, excluded from the BOM) are skipped. Only active devices that need a number to size circuits, PDUs, a UPS or
cooling should carry PowerW; skip parts under a few watts.
"""
from .sheet import T


def _num(v):
    try:
        return float(str(v).split()[0])
    except (ValueError, IndexError):
        return None


def budget(sheet):
    total, typical, rows, missing = 0.0, 0.0, [], []
    for ref, name, f, placeholder in sheet.placed:
        if placeholder:
            continue
        if f.get("PowerIncludedIn"):
            rows.append((ref, name, _num(f.get("PowerW")), f["PowerIncludedIn"], f.get("PowerBasis", "")))
            continue
        w = _num(f.get("PowerW"))
        if w is None:
            missing.append(f"{ref} ({name})")
            continue
        total += w
        t = _num(f.get("PowerTypicalW"))
        typical += t if t is not None else w
        basis = f.get("PowerBasis", "")
        if f.get("PowerTypicalBasis"):
            basis += "; typical " + f["PowerTypicalBasis"]
        rows.append((ref, name, w, "", basis))
    return {"max_w": total, "typical_w": typical, "rows": rows, "missing": missing}


def note(sheet, x, y, volts=120, size=T, pitch=6.0):
    """Write the power lines. Returns the budget. Missing numbers print a warning (they never reach the drawing)."""
    b = budget(sheet)
    amps = lambda w: w / volts
    line = f"Power (from symbol fields): max {b['max_w']:.0f} W = {amps(b['max_w']):.1f} A at {volts} V"
    if b["typical_w"] != b["max_w"]:
        line += f"; typical about {b['typical_w']:.0f} W = {amps(b['typical_w']):.1f} A"
    sheet.text(line + ".", x, y, size)
    bases = sorted({r[4] for r in b["rows"] if r[4] and not r[3]})
    if bases:
        sheet.text("Basis: " + "; ".join(bases) + ".", x, y + pitch, size)
    if b["missing"]:
        print("  power: no PowerW for " + ", ".join(b["missing"]) + " (not counted)")
    return b
