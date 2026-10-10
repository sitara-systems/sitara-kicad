"""Open-items ("to be confirmed") register for an AV drawing.

One list of items drives two things: a register sheet (item, owner, expected date, note) and a short summary box on the root sheet.

    from sitara_av import tbc
    ITEMS = [tbc.Item("SDI card model", "DeckLink or AJA", "Sitara", "", "decides slot use"), ...]
    page = tbc.register_sheet(ctx, ids["tbc"], ids["root"], ITEMS, page="7")     # write it with page.write()
    root.subsheet(page, (223.52, 40.64), (73.66, 25.4), [])                      # box on the root sheet
    tbc.summary(root, ITEMS, 125.73, 198.12, 275.0, page="7")                    # count box on the root sheet

Owners are free text (a person or company). Leave `expected` blank until a date is known.
"""
from dataclasses import dataclass

from .sheet import Sheet, T

INK = "88 62 210"
MAX_ROWS = 18        # rows that fit on an A3 sheet with the detail line (row pitch shrinks above 14 and above 16)


@dataclass(frozen=True)
class Item:
    item: str
    detail: str = ""
    owner: str = ""
    expected: str = ""
    note: str = ""


def register_sheet(ctx, uuid, root_uuid, items, page, fname="tbc.kicad_sch", title="To be confirmed"):
    if len(items) > MAX_ROWS:
        raise ValueError(f"{len(items)} items do not fit one register sheet (max {MAX_ROWS}); split the list or add a second sheet")
    s = Sheet(ctx, fname, title, "A3", uuid, "/" + root_uuid)
    s.path = "/" + root_uuid + "/" + uuid
    s.page = str(page)
    s.text(f"TO BE CONFIRMED - {len(items)} open items, with owner and date when known.", 20.32, 22.86, 3.2, True)
    cols = [("#", 22.0), ("ITEM", 34.0), ("OWNER", 190.0), ("EXPECTED", 226.0), ("NOTE", 268.0)]
    x0, x1, y = 20.32, 399.0, 36.0
    s.line([(x0, y), (x1, y)], INK, width=0.3)
    for name, cx in cols:
        s.text(name, cx, y + 7.0, T, True)
    y += 10.0
    s.line([(x0, y), (x1, y)], INK, width=0.3)
    pitch = 13.0 if len(items) <= 14 else (11.6 if len(items) <= 16 else 11.0)
    for i, it in enumerate(items):
        top = y + i * pitch
        s.text(f"{i + 1}", cols[0][1], top + pitch * 0.62, T)
        s.text(it.item, cols[1][1], top + pitch * (0.46 if it.detail else 0.62), T)
        if it.detail:
            s.text(it.detail, cols[1][1], top + pitch * 0.86, 1.78)
        s.text(it.owner or "-", cols[2][1], top + pitch * 0.62, T)
        s.text(it.expected or "-", cols[3][1], top + pitch * 0.62, T)
        if it.note:
            s.text(it.note, cols[4][1], top + pitch * 0.62, T)
        s.line([(x0, top + pitch), (x1, top + pitch)], INK, width=0.15)
    s.text("Expected date is left blank until it is known.", 20.32, y + len(items) * pitch + 9.0, T)
    return s


def summary(s, items, x, y, w=275.0, h=40.0, page="7"):
    """Count box for the root sheet: how many are open, per owner, and which have a date."""
    owners = {}
    for it in items:
        owners[it.owner or "unassigned"] = owners.get(it.owner or "unassigned", 0) + 1
    s.text_box(f"TO BE CONFIRMED (TBC): {len(items)} open", x, y, w, h, T, frame=True)
    s.text(f"Full register with owner and expected date: sheet {page}.", x + 4.0, y + 16.0, T)
    s.text("   ".join(f"{k}: {v}" for k, v in sorted(owners.items())), x + 4.0, y + 22.0, T)
    dated = [str(i + 1) for i, it in enumerate(items) if it.expected]
    if dated:
        s.text("Items with a known date: " + ", ".join(dated) + ".", x + 4.0, y + 28.0, T)
