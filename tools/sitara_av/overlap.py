"""Approximate text-overlap check for generated sheets.

Every text the sheet writer places (notes, titles, symbol reference/value/field text, sheet names) and every symbol body is recorded
as a rectangle. `check(sheet)` reports text that overlaps other text or a symbol body. It is an estimate (text width is about 0.82 x
text height per character), so it catches clear collisions, not 1 mm near-misses. It does not look at wires, pin names or net labels.
"""
WARNINGS = []

CHAR_W = 0.82      # character width as a fraction of text height
LINE_H = 1.15      # line height as a fraction of text size
TOL = 0.4          # mm of overlap ignored on either axis


def text_rect(t, x, y, size, anchor="bottom", bold=False):
    w = len(t) * size * CHAR_W * (1.08 if bold else 1.0)
    h = size * LINE_H
    y0, y1 = (y - h, y) if anchor == "bottom" else (y, y + h)
    return (x, y0, x + w, y1)


def _inter(a, b):
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    return dx, dy


def check(sheet):
    """sheet.rects: [(kind, label, (x0, y0, x1, y1))], kind is 'text', 'body' or 'box'."""
    out = []
    r = sheet.rects
    for i in range(len(r)):
        for j in range(i + 1, len(r)):
            ka, la, a = r[i]
            kb, lb, b = r[j]
            if ka != "text" and kb != "text":
                continue
            dx, dy = _inter(a, b)
            if dx > TOL and dy > TOL:
                out.append(f"{sheet.fname}: '{la[:40]}' overlaps '{lb[:40]}' near ({max(a[0], b[0]):.0f}, {max(a[1], b[1]):.0f}) mm")
    return out
