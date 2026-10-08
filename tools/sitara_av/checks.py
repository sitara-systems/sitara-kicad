"""Checks that KiCad's ERC cannot do: format mixing on a net, and PCIe lane / slot fit. Read the kicadxml netlist."""
import re
import xml.etree.ElementTree as ET

FORMAT_PREFIX = re.compile(r"^(SDI|HDMI2\.0|HDMI2\.1|HDMI|DP1\.4|DP|REF|GENLOCK|SYNC|TESSERA|FEED|FIBER|VID|LAN|RJ45|NET|PCIe|USB|PWR|AUDIO|RS232)")
FAMILY = {"HDMI2.0": "HDMI", "HDMI2.1": "HDMI", "DP1.4": "DP", "GENLOCK": "REF", "SYNC": "REF", "RJ45": "NET", "LAN": "NET",
          "TESSERA": "LED", "FEED": "LED"}
CONVERTER_REF_PREFIXES = ("ADAPTER", "EXT", "DA", "SW", "CONV")


def pin_family(pin_name):
    m = FORMAT_PREFIX.match(pin_name)
    if not m:
        return "?"
    p = m.group(1)
    return FAMILY.get(p, p)


def format_check(xml_path):
    """A net must carry one signal format unless a converter (adapter, extender, DA, switcher) sits on it."""
    root = ET.parse(xml_path).getroot()
    problems = []
    for net in root.iter("net"):
        name = net.get("name")
        nodes = [(n.get("ref"), n.get("pinfunction") or n.get("pin"), n.get("pintype") or "") for n in net.findall("node")]
        if name.startswith("unconnected-") or any("no_connect" in t for _, _, t in nodes):
            continue
        fams = {pin_family(p) for _, p, _ in nodes}
        fams.discard("?")
        if len(fams) > 1 and not any(r.startswith(CONVERTER_REF_PREFIXES) for r, _, _ in nodes):
            problems.append(f"{name}: mixed formats {sorted(fams)} across {[(r, p) for r, p, _ in nodes]}")
    return problems


def pcie_lane_check(xml_path):
    """Card lanes (PCIe-X<n>) must fit the chassis slot pin they claim (PCIe-Slot-<k>-G<gen>x<lanes>)."""
    root = ET.parse(xml_path).getroot()
    problems = []
    for net in root.iter("net"):
        slots, cards = [], []
        for n in net.findall("node"):
            pf = re.sub(r"_\d+$", "", n.get("pinfunction") or "")
            m = re.match(r"PCIe-Slot-(\d+)-G(\d)x(\d+)$", pf)
            c = re.match(r"PCIe-X(\d+)$", pf)
            if m:
                slots.append((n.get("ref"), int(m.group(1)), int(m.group(3))))
            elif pf == "PCIe-ADJ":
                cards.append((n.get("ref"), 0))
            elif c:
                cards.append((n.get("ref"), int(c.group(1))))
        for _, k, lanes in slots:
            for ref, need in cards:
                if need > lanes:
                    problems.append(f"{ref} needs x{need} but slot {k} is x{lanes}")
    return problems


def all_checks(xml_path):
    return format_check(xml_path) + pcie_lane_check(xml_path)
