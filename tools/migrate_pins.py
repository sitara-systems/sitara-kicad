"""Rename the pins of the older (hand-drawn) symbols to the FORMAT-DIR-n convention used by the generated symbols.

    python tools/migrate_pins.py            # dry run: print the rename table and anything left alone
    python tools/migrate_pins.py --apply    # rewrite the libraries and record av_components/_migration/pin_renames.json

Only the text of each (name "...") changes. Pin numbers, positions, types and electrical roles are untouched, so wires on
existing schematics keep their connections (KiCad matches by pin number); only the visible pin labels change.
Symbols that are generated from av_components/_generator/symbols_spec.py are skipped (they are already in the convention).
PCIe slot pins are left for a person to decide: a slot's generation and lanes cannot be guessed from its old name.
"""
import argparse
import collections
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "av_components", "_generator"))
import symbols_spec  # noqa: E402
from build_symbols import top_level_symbols  # noqa: E402

PIN_RE = re.compile(r'(\(pin (\w+) \w+\s*\(at [^)]*\)\s*\(length [^)]*\)\s*(?:\(hide yes\)\s*)?\(name ")([^"]*)(")')
DIR = {"input": "IN", "output": "OUT"}


def _dir(etype, hint=None):
    if hint:
        return hint.upper()
    return DIR.get(etype)


def new_name(old, etype):
    """Return the converted pin name, or None to leave the pin alone."""
    # already in the convention (or deliberately special)
    if re.match(r"^(PCIe-|RJ45-\d+$|GND$|VCC$|VINT$|GPIO$|RS232$|I/O$|PoE\+?$)", old) or re.match(r"^[A-Z0-9]+(-[A-Z0-9.]+)+$", old) and not old.startswith("RJ45-"):
        return None
    m = re.match(r"^Mini-?DP[-_ ]?(\d+)$", old, re.I)
    if m:
        return f"MDP-{_dir(etype) or 'OUT'}-{m.group(1)}"
    m = re.match(r"^(?:DisplayPort|DP)(?:[-_ ]?(IN|OUT|MB))?(?:[-_ ]?(\d+))?$", old, re.I)
    if m:
        d = (m.group(1) or "").upper()
        if d == "MB":
            return f"DP-{_dir(etype) or 'OUT'}-MB"
        return f"DP-{_dir(etype, d) or 'OUT'}-{m.group(2) or 1}"
    m = re.match(r"^(HDMI|DVI)(?:[-_ ]?(IN|OUT))?(?:[-_ ]?(\d+))?$", old, re.I)
    if m:
        return f"{m.group(1).upper()}-{_dir(etype, m.group(2)) or 'OUT'}-{m.group(3) or 1}"
    m = re.match(r"^Audio[-_ ]?(In|Out)(?:[-_ ]?(\d+))?$", old, re.I)
    if m:
        return f"AUDIO-{m.group(1).upper()}-{m.group(2) or 1}"
    m = re.match(r"^RJ45-(\d+)\(PoE\)$", old)
    if m:
        return f"RJ45-{m.group(1)}-POE"
    if re.match(r"^(RJ45|RJ45_Ethernet|RJ45_Control|LAN)$", old, re.I):
        return "RJ45-1"
    m = re.match(r"^USB-([AC])-(Front|Rear)-?(\d+)?$", old, re.I)
    if m:
        return f"USB-{m.group(1).upper()}-{m.group(2).upper()}" + (f"-{m.group(3)}" if m.group(3) else "")
    m = re.match(r"^USB-([AC])-(\d+)$", old)
    if m:
        return None
    m = re.match(r"^USB-C$", old)
    if m:
        return "USB-C-1"
    if re.match(r"^USB(?:[-_ ]?[23]\.0)?$", old, re.I):
        return "USB-A-1"
    m = re.match(r"^USB[_ ](Hub|Touch|Dongle)$", old, re.I)
    if m:
        return f"USB-{m.group(1).upper()}"
    if re.match(r"^(Power|Power-Input|Power_Input)$", old, re.I):
        return "PWR-IN"
    m = re.match(r"^Power[_-](\d+V)$", old, re.I)
    if m:
        return f"PWR-{m.group(1).upper()}"
    if old == "AC-IN":
        return "PWR-AC-IN"
    return None


def migrate_text(text, skip_names):
    """Returns (new_text, [(symbol, old, new, etype)], [(symbol, old, etype)] left alone)."""
    renames, kept = [], []
    out = text
    for name, a, b in reversed(top_level_symbols(text)):
        if name in skip_names:
            continue
        block = out[a:b]
        pins = list(PIN_RE.finditer(block))
        used = {m.group(3) for m in pins}
        plan = []
        for m in pins:
            old, etype = m.group(3), m.group(2)
            nn = new_name(old, etype)
            if nn is None or nn == old:
                kept.append((name, old, etype))
                continue
            plan.append((m, old, nn, etype))
        taken = set(used)
        final = {}
        for m, old, nn, etype in plan:
            cand = nn
            while cand in taken and cand != old:
                mm = re.match(r"^(.*?)(\d+)$", cand)
                cand = f"{mm.group(1)}{int(mm.group(2)) + 1}" if mm else cand + "-2"
            taken.add(cand)
            final[m.start()] = cand
            renames.append((name, old, cand, etype))
        for m, old, nn, etype in reversed(plan):
            cand = final[m.start()]
            block = block[:m.start(3)] + cand + block[m.end(3):]
        out = out[:a] + block + out[b:]
    return out, list(reversed(renames)), kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    skip = set(symbols_spec.SYMBOLS)
    all_ren, all_kept = [], []
    for f in sorted(glob.glob(os.path.join(REPO, "av_components", "sitara-*.kicad_sym"))):
        raw = open(f, encoding="utf-8", newline="").read()
        crlf = "\r\n" in raw
        text = raw.replace("\r\n", "\n")
        new, ren, kept = migrate_text(text, skip)
        all_ren += [(os.path.basename(f),) + r for r in ren]
        all_kept += [(os.path.basename(f),) + k for k in kept]
        if a.apply and new != text:
            open(f, "w", encoding="utf-8", newline="").write(new.replace("\n", "\r\n") if crlf else new)
    tab = collections.Counter((o, n) for _, _, o, n, _ in all_ren)
    print(f"{len(all_ren)} pins renamed in {len(set(r[0] for r in all_ren))} libraries ({len(tab)} distinct renames)")
    for (o, n), c in sorted(tab.items()):
        print(f"  {c:3d}  {o:18s} -> {n}")
    left = collections.Counter(k[2] for k in all_kept)
    print(f"{sum(left.values())} pins left alone ({len(left)} distinct names), e.g.:", ", ".join(f"{n}x{c}" for n, c in left.most_common(14)))
    if a.apply:
        d = os.path.join(REPO, "av_components", "_migration")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "pin_renames.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump([{"library": l, "symbol": s, "old": o, "new": n, "type": t} for l, s, o, n, t in all_ren], fh, indent=1)
        print("recorded av_components/_migration/pin_renames.json")


if __name__ == "__main__":
    main()
