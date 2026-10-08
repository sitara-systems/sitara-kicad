"""Reusable assemblies. Each builder places symbols on a Sheet and returns its instances, so a project sheet can reuse the
same assembly and add its own overlays, and `tools/build_blocks.py` can save the assembly as a KiCad design block.

A design block holds only the generic assembly (devices, internal wiring, interface labels): no project notes or titles.
"""
import json
import os

from .sheet import Context, Sheet, SYMBOLS, T, gr

BLOCK_NAMESPACE = "b7d1a9c2-3e4f-4a56-8b7c-5a1e0d2c9f01"


# =============================================================== RENDER_NODE_A
def render_node_a(s, usb_rear1_free=True, sdi_bus_end="label"):
    """Dell Precision 7875 + RTX PRO 6000 Max-Q (dual width) + 12G-SDI card + RTX PRO Sync, PCIe slots wired as claims.

    Slot numbers follow the Dell owner's manual rear view. Assignment: GPU in slot 2 (also uses 3), SDI card 4, Sync 6;
    slots 1 and 5 free. Interface: net labels NET-MGMT / NET-SHOW (the two integrated jacks), REF (SDI card reference
    input) and the SDI1..4 outputs on an SDI[1..4] bus. `sdi_bus_end` is "label" (design block) or "hlabel" (sheet pin).
    """
    cpu = s.place("DELL_PRECISION_7875_TOWER", "CPU1", (gr(85), gr(135)), show=("PreferredModel", "Processor", "RAM"))
    gpu = s.place("GPU_NVIDIA_RTX_PRO_6000_BLACKWELL_MAXQ", "GPU1", (gr(250), gr(70)), show=("PreferredModel", "VRAM"))
    sdi = s.place("CAPTURE_CARD_SDI_12G_4CH", "SDI1", (gr(250), gr(162)), show=("Model", "Status"))
    sync = s.place("CARD_NVIDIA_RTX_PRO_SYNC", "SYNC1", (gr(250), gr(207)), show=("Model", "Usage"))
    S1, S2, S3, S4, S5, S6 = (f"PCIe-Slot-{k}-" + g for k, g in zip(range(1, 7), ("G5x8", "G5x16", "G4x4", "G4x8", "G4x16", "G4x8")))
    xa, xb, xc, xd = 157.48, 165.1, 180.34, 172.72
    a, b = cpu.pin(S2), gpu.pin("PCIe-X16")
    s.wire([a, (xa, a[1]), (xa, b[1]), b], "PCIE"); s.text("PCIe x16 (slot 2)", xa + 1.27, b[1] - 1.0, T)
    a, b = cpu.pin(S3), gpu.pin("PCIe-ADJ")
    s.wire([a, (xb, a[1]), (xb, b[1]), b], "PCIE"); s.text("dual width: slot 3 too", xb + 2.54, b[1] + 4.2, T)
    a, b = cpu.pin(S4), sdi.pin("PCIe-X8")
    s.wire([a, (xc, a[1]), (xc, b[1]), b], "PCIE"); s.text("PCIe x8 (slot 4)", xc + 1.27, b[1] - 1.0, T)
    a, b = cpu.pin(S6), sync.pin("PCIe-X4")
    s.wire([a, (xd, a[1]), (xd, b[1]), b], "PCIE"); s.text("PCIe (slot 6)", xd + 1.27, b[1] - 1.0, T)
    for sl in (S1, S5):
        s.nc(cpu.pin(sl))
    for pn, _side, _etype in SYMBOLS["DELL_PRECISION_7875_TOWER"]["pins"]:
        if pn.startswith("PCIe-Slot") or pn in ("RJ45-1G", "RJ45-10G"):
            continue
        if pn == "USB-A-REAR-1" and not usb_rear1_free:
            continue
        s.nc(cpu.pin(pn))
    a = cpu.pin("RJ45-10G"); s.wire([a, (a[0] + 5.08, a[1])], "NET"); s.glabel("NET-SHOW", a[0] + 5.08, a[1], 0, "bidirectional")
    a = cpu.pin("RJ45-1G"); s.wire([a, (a[0] + 5.08, a[1])], "NET"); s.glabel("NET-MGMT", a[0] + 5.08, a[1], 0, "bidirectional")
    s.nc(sync.pin("GENLOCK-IN")); s.nc(sync.pin("GENLOCK-LOOP"))
    s.text("PCIe slots (Dell manual numbering): 1 Gen5 x8, 2 Gen5 x16, 3 Gen4 x8 at x4, 4 Gen4 x8, 5 Gen4 x16, 6 Gen4 x8.", 22.86, 240.0, T)
    for k in range(1, 5):
        s.nc(gpu.pin(f"DP-OUT-{k}"))
    bx = 288.29
    ys = []
    for k in range(1, 5):
        p = sdi.pin(f"SDI-OUT-{k}"); ys.append(p[1])
        s.wire([p, (bx, p[1])], "SDI"); s.label(f"SDI{k}", p[0] + 3.81, p[1]); s.entry(bx, p[1])
    ybus = 218.44
    s.bus([(bx + 2.54, ys[0] + 2.54), (bx + 2.54, ys[-1] + 2.54)], "SDI")
    s.bus([(bx + 2.54, ys[-1] + 2.54), (bx + 2.54, ybus), (330.2, ybus)], "SDI")
    if sdi_bus_end == "hlabel":
        s.hlabel("SDI[1..4]", 330.2, ybus, 0, "output")
    else:
        s.label("SDI[1..4]", 330.2, ybus)
    p = sdi.pin("REF-IN"); s.wire([p, (p[0] - 10.16, p[1])], "REF"); s.glabel("REF", p[0] - 10.16, p[1], 180, "input")
    return {"cpu": cpu, "gpu": gpu, "sdi": sdi, "sync": sync}


# =============================================================== PROCESSING_STACK_D8_4X_SX40
def processing_stack_d8_4x_sx40(s):
    """One RGBLink D8 Plus feeding four SX40 LED processors, one 4K60 HDMI 2.0 quadrant each.

    Interface: labels DP-IN and HDMI-IN (the D8 inputs), REF and NET-SHOW / NET-LED (global), LED1..4 (Tessera output 1 of each SX40).
    The D8 quadrants join the SX40 inputs by net label (Q1..Q4).
    """
    d8 = s.place("SWITCHER_RGBLINK_D8_PLUS", "SW1", (gr(90), gr(110)), show=("PreferredModel", "Status"))
    p = d8.pin("DP1.4-IN"); s.wire([(p[0] - 12.7, p[1]), p], "DP"); s.label("DP-IN", p[0] - 12.7, p[1])
    p = d8.pin("HDMI2.1-IN"); s.wire([(p[0] - 12.7, p[1]), p], "HDMI"); s.label("HDMI-IN", p[0] - 12.7, p[1])
    p = d8.pin("GENLOCK-IN"); s.wire([p, (p[0] - 6.35, p[1])], "REF"); s.glabel("REF", p[0] - 6.35, p[1], 180, "input")
    p = d8.pin("LAN"); s.wire([p, (p[0] - 6.35, p[1])], "NET"); s.glabel("NET-SHOW", p[0] - 6.35, p[1], 180, "bidirectional")
    s.nc(d8.pin("RS232")); s.nc(d8.pin("GENLOCK-LOOP"))
    sx = []
    for i in range(1, 5):
        p = d8.pin(f"HDMI2.0-OUT-{i}"); s.wire([p, (p[0] + 10.16, p[1])], "HDMI"); s.label(f"Q{i}", p[0] + 10.16, p[1])
    for i in range(1, 5):
        y = gr(45 + (i - 1) * 40.64)
        pr = s.place("LED_PROCESSOR_BROMPTON_SX40", f"PROC{i}", (gr(250), y), show=())
        sx.append(pr)
        p = pr.pin("HDMI2.0-IN"); s.wire([(p[0] - 15.24, p[1]), p], "HDMI"); s.label(f"Q{i}", p[0] - 15.24, p[1])
        s.nc(pr.pin("SDI-IN"))
        p = pr.pin("SYNC-IN"); s.wire([p, (p[0] - 3.81, p[1])], "REF"); s.glabel("REF", p[0] - 3.81, p[1], 180, "input")
        p = pr.pin("LAN"); s.wire([p, (p[0] - 3.81, p[1])], "NET"); s.glabel("NET-LED", p[0] - 3.81, p[1], 180, "bidirectional")
        for pn in ("HDMI2.0-THRU", "SDI-THRU", "SYNC-THRU", "TESSERA-OUT-2", "TESSERA-OUT-3", "TESSERA-OUT-4"):
            s.nc(pr.pin(pn))
        p = pr.pin("TESSERA-OUT-1"); s.wire([p, (p[0] + 10.16, p[1])], "LED"); s.label(f"LED{i}", p[0] + 10.16, p[1])
    return {"d8": d8, "sx": sx}


# =============================================================== SURVEYOR_NODE_A
def surveyor_node_a(s):
    """Protectli V1210 monitoring / remote-ops node: management port on the house LAN (NET-MGMT), second port spare."""
    sv = s.place("COMPUTER_PROTECTLI_V1210", "SURV1", (gr(90), gr(100)), show=("Model", "Role"))
    p = sv.pin("RJ45-1"); s.wire([p, (p[0] + 6.35, p[1])], "NET"); s.glabel("NET-MGMT", p[0] + 6.35, p[1], 0, "bidirectional")
    s.nc(sv.pin("RJ45-2")); s.nc(sv.pin("PWR-IN"))
    return {"surv": sv}


# =============================================================== AUDIO_SCARLETT_2I2_A
def audio_scarlett_2i2_a(s):
    """Focusrite Scarlett 2i2 USB audio interface: USB on net USB-AUDIO, line outputs AUDIOL / AUDIOR, headphones unused."""
    au = s.place("AUDIO_INTERFACE_FOCUSRITE_SCARLETT_2I2", "AUD1", (gr(120), gr(100)), show=("Model", "Outputs"))
    p = au.pin("USB-IN"); s.wire([p, (p[0] - 5.08, p[1])], "USB"); s.glabel("USB-AUDIO", p[0] - 5.08, p[1], 180, "bidirectional")
    for ch in ("L", "R"):
        p = au.pin(f"AUDIO-OUT-{ch}"); s.wire([p, (p[0] + 10.16, p[1])], "AUDIO"); s.label(f"AUDIO{ch}", p[0] + 10.16, p[1])
    s.nc(au.pin("AUDIO-HP"))
    return {"aud": au}


BLOCKS = [
    # (library, name, builder, description, keywords)
    ("sitara-render-nodes", "RENDER_NODE_A", render_node_a,
     "Render node A: Dell Precision 7875 Tower, RTX PRO 6000 Blackwell Max-Q (dual slot), 12G-SDI card and RTX PRO Sync card with the PCIe slots wired as claims, unused ports flagged. Excludes any external USB sound card.",
     "render node, Dell Precision 7875, RTX PRO 6000, SDI, genlock, AV"),
    ("sitara-av-blocks", "PROCESSING_STACK_D8_4X_SX40", processing_stack_d8_4x_sx40,
     "One RGBLink D8 Plus feeding four Brompton SX40 LED processors, one 4K60 HDMI 2.0 quadrant each, with reference and network labels.",
     "RGBLink D8, SX40, LED processor, Tessera, HDMI"),
    ("sitara-av-blocks", "SURVEYOR_NODE_A", surveyor_node_a,
     "Protectli V1210 surveyor (monitoring and remote-ops) node with its management port on the house LAN.",
     "surveyor, Protectli, StarWatch, MeshCentral, network"),
    ("sitara-av-blocks", "AUDIO_SCARLETT_2I2_A", audio_scarlett_2i2_a,
     "Focusrite Scarlett 2i2 USB audio interface with L/R line outputs; the USB end joins the render node by net label.",
     "audio, Focusrite, Scarlett, USB"),
]


def write_block(lib_dir, name, builder, description, keywords):
    """Write <lib_dir>/<name>.kicad_block/{<name>.kicad_sch,<name>.json}. Returns the schematic path."""
    bdir = os.path.join(lib_dir, name + ".kicad_block")
    ctx = Context(project="design_block", out_dir=bdir, rev="A", company="Sitara Systems", comment="", namespace=BLOCK_NAMESPACE)
    s = Sheet(ctx, name + ".kicad_sch", name.replace("_", " ").title() + " (design block)", "A3", ctx.uid("design-block-" + name))
    s.path = "/" + s.uuid
    builder(s)
    s.write(root=True)
    with open(os.path.join(bdir, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"description": description, "keywords": keywords, "fields": {}}, f, indent=2)
    return os.path.join(bdir, name + ".kicad_sch")
