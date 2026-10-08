"""Wire formats: color, line style, print style and legend order. One definition shared by every project.

Color is keyed to the signal FORMAT and is the same in every project (so a technician learns it once). Sitara's two
hero hues go to the most common digital video formats (HDMI = Asia Violet, DisplayPort = Pumpkin); rarer formats get
secondary hues; network, reference and PCIe are muted neutrals, with dashes marking network and reference. Every hue
is deepened for at least 3:1 contrast on the sheet and checked for color-vision confusion between formats that share a page.

The print variant draws every wire black and tells formats apart by line pattern and weight, so a photocopy,
a black-and-white laser print or a colorblind reader can still read the drawing.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Fmt:
    key: str            # key used by Sheet.wire / Sheet.bus
    label: str          # legend text
    rgb: tuple          # color-variant wire color
    dashed: bool        # color variant: dashed instead of solid
    group: str          # legend group: "video" | "audio" | "control"
    print_type: str     # print variant: KiCad stroke type
    print_width: float  # print variant: stroke width (mm)
    netclass_patterns: tuple = ()   # net-name patterns that map to this class in the project file


FORMATS = [
    Fmt("HDMI", "HDMI (2.0 / 2.1)", (105, 80, 225), False, "video", "solid", 0.30, ("HDMI*", "D8HDMI*", "PROC*")),
    Fmt("DP", "DisplayPort 1.4", (205, 103, 0), False, "video", "dash_dot", 0.30, ("DP*", "D8DP*")),
    Fmt("SDI", "12G-SDI", (185, 55, 125), False, "video", "dot", 0.40, ("SDI*",)),
    Fmt("LED", "Tessera / LED feed", (0, 100, 95), False, "video", "solid", 0.60, ("LED*",)),
    Fmt("AUDIO", "Audio (line level)", (40, 100, 190), False, "audio", "dash_dot_dot", 0.30, ("AUDIO*",)),
    Fmt("USB", "USB", (125, 75, 40), False, "audio", "dot", 0.20, ()),
    Fmt("NET", "Network / control", (110, 110, 110), True, "control", "dash", 0.15, ("NET-*",)),
    Fmt("REF", "Reference / genlock", (30, 30, 30), True, "control", "dash_dot", 0.15, ("REF",)),
    Fmt("PCIE", "PCIe (internal)", (80, 80, 80), False, "control", "solid", 0.15, ()),
    Fmt("FIBER", "Fiber", (205, 103, 0), False, "video", "dash", 0.40, ()),
]
BY_KEY = {f.key: f for f in FORMATS}
LEGEND_ORDER = ["HDMI", "DP", "SDI", "LED", "AUDIO", "USB", "NET", "REF", "PCIE"]


def rgb_str(key):
    r, g, b = BY_KEY[key].rgb
    return f"{r} {g} {b}"


def rgb_css(key):
    r, g, b = BY_KEY[key].rgb
    return f"rgb({r}, {g}, {b})"
