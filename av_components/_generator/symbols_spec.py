"""Symbol specifications for reusable AV video gear (render nodes, media servers, scalers, LED processors, sync, network).

Each entry: lib (target .kicad_sym basename), ref (designator prefix), desc, w (body width mm),
pins [(name, side L|R, electrical type)] in top-to-bottom order per side, fields {name: value},
visible (fields drawn on the schematic besides Reference/Value), dashed (TBC placeholder),
exclude_bom (placeholder never counted).

Status is CONFIRMED / TBC / PLACEHOLDER. Edit here, re-run
build_symbols.py; never hand-edit the generated symbols.
"""

def _n(fmt, n, side, etype):
    return [(f"{fmt}-{i}", side, etype) for i in range(1, n + 1)]


SYMBOLS = {
    # ------------------------------------------------------------------ sitara-computers
    "DELL_PRECISION_7875_TOWER": dict(
        lib="sitara-computers", ref="CPU", w=48.26,
        desc="Dell Precision 7875 Tower workstation (Threadripper PRO)",
        pins=[("PWR-IN", "L", "power_in"),
              ("USB-C-FRONT-1", "L", "bidirectional"), ("USB-C-FRONT-2", "L", "bidirectional"),
              ("USB-A-FRONT-1", "L", "bidirectional"), ("USB-A-FRONT-2", "L", "bidirectional"), ("HEADSET-FRONT", "L", "bidirectional"),
              ("USB-A-REAR-1", "L", "bidirectional"), ("USB-A-REAR-2", "L", "bidirectional"), ("USB-A-REAR-3", "L", "bidirectional"),
              ("USB-C-REAR-1", "L", "bidirectional"), ("USB-C-REAR-2", "L", "bidirectional"), ("USB-C-REAR-3", "L", "bidirectional"),
              ("AUDIO-OUT", "L", "output"),
              ("RJ45-1G", "R", "bidirectional"), ("RJ45-10G", "R", "bidirectional")] + [("PCIe-Slot-1-G5x8", "R", "input"), ("PCIe-Slot-2-G5x16", "R", "input"), ("PCIe-Slot-3-G4x4", "R", "input"),
                                                            ("PCIe-Slot-4-G4x8", "R", "input"), ("PCIe-Slot-5-G4x16", "R", "input"), ("PCIe-Slot-6-G4x8", "R", "input")],
        fields={"Model": "Dell Precision 7875 Tower", "PreferredModel": "Dell Precision 7875 Tower",
 "Processor": "AMD Ryzen Threadripper PRO 9945WX, 12C/24T, 4.7-5.4 GHz, 350 W",
 "RAM": "64 GB (2x 32 GB) DDR5-5200 RDIMM ECC", "Storage": "2x 2 TB NVMe Performance SSD (SED ready)",
 "PSU": "1350 W Platinum, C20 inlet (owner's manual); 90-264 VAC, 16 A max",
 "PowerW": "1350", "PowerBasis": "Dell PSU rating: maximum for the whole node, installed cards included",
 "PowerTypicalW": "800", "PowerTypicalBasis": "estimate: CPU 350 W + GPU 300 W + about 150 W other", "OS": "Windows 11 Pro", "Network": "Integrated: RJ45 1 GbE (Realtek RTL8111-EPP) + RJ45 10 GbE (Marvell AQC113)", "Management": "AMD DASH; suspected on the 1 GbE jack, to be confirmed when the unit arrives (Oct 28)",
 "PCIeConfig": "6 full-height slots, numbered as in the Dell owner's manual rear view: 1 Gen5 x8 (open-ended), 2 Gen5 x16, 3 Gen4 x8 running x4 (open-ended), 4 Gen4 x8 (open-ended), 5 Gen4 x16, 6 Gen4 x8 (open-ended). Slot pins are inputs: a card claims a slot with an output pin, so two cards on one slot is an ERC error. Slot pin names carry electrical lanes", "FormFactor": "Tower Workstation", "Mounting": "Dell rail kit 3WF88 / 03W88, 4U",
 "Status": "CONFIRMED",
 "Usage": "Real-time render node"},
        visible=("Model",)),
    "GPU_NVIDIA_RTX_PRO_6000_BLACKWELL_MAXQ": dict(
        lib="sitara-computers", ref="GPU", w=30.48,
        desc="NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition, 96 GB, 4x DisplayPort",
        pins=[("PCIe-X16", "L", "output"), ("PCIe-ADJ", "L", "output")] + _n("DP-OUT", 4, "R", "output"),
        fields={"Model": "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition", "PreferredModel": "NVIDIA RTX PRO 6000 Blackwell Max-Q",
 "Architecture": "Blackwell", "VRAM": "96 GB GDDR7 ECC", "DisplayOutputs": "4x DisplayPort 2.1",
 "PCIeInterface": "x16 Gen5", "PowerW": "300", "PowerBasis": "NVIDIA spec (Max-Q)", "PowerIncludedIn": "host", "CoolingSlots": "Dual-slot", "SlotWidth": "2 (PCIe-X16 + PCIe-ADJ: also blocks the adjacent slot)",
 "Status": "CONFIRMED",
 "Usage": "Render node GPU; DP outputs unused when video leaves over SDI"},
        visible=("Model",)),
    "CAPTURE_CARD_SDI_12G_4CH": dict(
        lib="sitara-computers", ref="SDI", w=30.48,
        desc="Generic 4-channel 12G-SDI PCIe I/O card with reference input, drawn configured as 4x OUT",
        pins=[("PCIe-X8", "L", "output"), ("REF-IN", "L", "input")] + _n("SDI-OUT", 4, "R", "output"),
        fields={"PowerIncludedIn": "host", "Model": "DeckLink 8K Pro G2 | AJA Corvid 44 12G BNC (TBC)", "PreferredModel": "TBC",
 "SlotWidth": "1 (TBC for DeckLink; AJA Corvid 44 is single width)", "PortMode": "4x OUT in this drawing (hardware ports are bidirectional 12G-SDI)",
 "Connector": "BNC", "RefInput": "Tri-level / black burst, 59.94 or 60 - format TBC",
 "Output": "4x 2160p60 10-bit 4:2:2 single-link 12G, locked to house reference",
 "Status": "TBC",
},
        visible=("Model", "Status")),

    # ------------------------------------------------------------------ sitara-video (new)
    "MEDIASERVER_RESOLUME_HOUSE": dict(
        lib="sitara-video", ref="SRV", w=38.1,
        desc="Resolume media server (venue-owned); 4x 12G-SDI in, 5x 8K out (DP 1.4 and HDMI 2.1)",
        pins=_n("SDI-IN", 4, "L", "input") + [("REF-IN", "L", "input"), ("LAN", "L", "bidirectional")]
             + _n("DP-OUT", 5, "R", "output") + _n("HDMI-OUT", 5, "R", "output"),
        fields={"Model": "TBC (house Resolume server; make, model, GPU unknown)", "PreferredModel": "TBC",
 "Role": "Primary | Backup (set per instance)",
 "Ingest": "4x 12G-SDI live inputs",
 "Outputs": "5x 8K per server: DP 1.4 (primary path) or HDMI 2.1 (backup path) into the D8 units",
 "Fallback": "Backup server plays an ambient ProRes loop",
 "Status": "TBC",},
        visible=("Model", "Role", "Status")),
    "SWITCHER_RGBLINK_D8_PLUS": dict(
        lib="sitara-video", ref="SW", w=38.1,
        desc="RGBLink D8 (Plus) 8K presentation switcher/scaler: DP 1.4 + HDMI 2.1 in, 4x HDMI 2.0 4K quadrants out",
        pins=[("DP1.4-IN", "L", "input"), ("HDMI2.1-IN", "L", "input"), ("GENLOCK-IN", "L", "input"),
              ("LAN", "L", "bidirectional"), ("RS232", "L", "bidirectional")]
             + _n("HDMI2.0-OUT", 4, "R", "output") + [("GENLOCK-LOOP", "R", "output")],
        fields={"Model": "RGBLink D8 Plus (sometimes called 'D8 Pro'; verify)", "PartNumber": "130-0008-03-0", "PreferredModel": "RGBLink D8 Plus",
 "Inputs": "1x HDMI 2.1 + 1x DP 1.4, 8K60, auto-switch between the two",
 "Outputs": "4x HDMI 2.0 4K60 (8K input split into four quadrants)",
 "Mode": "Primary server on DP 1.4, backup server on HDMI 2.1",
 "Control": "1x RJ45 LAN, 1x RS-232; genlock 1 IN + 1 LOOP (BNC)", "Status": "TBC",},
        visible=("Model", "Status")),
    "LED_PROCESSOR_BROMPTON_SX40": dict(
        lib="sitara-video", ref="PROC", w=38.1,
        desc="Brompton Tessera SX40 4K LED processor: 12G-SDI + HDMI 2.0 in (loop-through), 4x 10G Tessera out",
        pins=[("HDMI2.0-IN", "L", "input"), ("SDI-IN", "L", "input"), ("SYNC-IN", "L", "input"), ("LAN", "L", "bidirectional")]
             + [("HDMI2.0-THRU", "R", "output"), ("SDI-THRU", "R", "output"), ("SYNC-THRU", "R", "output")]
             + _n("TESSERA-OUT", 4, "R", "output"),
        fields={"Model": "Brompton Tessera SX40", "PartNumber": "TBC (no public order code)",
 "PreferredModel": "Brompton Tessera SX40",
 "Inputs": "1x 12G-SDI + 1x HDMI 2.0, each with loop-through; bi/tri-level sync in/thru",
 "Outputs": "4x 10G Tessera to the panels (not detailed in this drawing)",
 "Capacity": "~9 Mpx @ 60 Hz, up to 4096x2160 60 Hz", "Status": "TBC",},
        visible=("Model",)),
    "SYNC_GENERATOR_TBC": dict(
        lib="sitara-video", ref="REF", w=30.48, dashed=True,
        desc="House reference / genlock source - placeholder until source, format and distribution are confirmed",
        pins=_n("REF-OUT", 4, "R", "output"),
        fields={"Model": "TBC (house sync source)", "PreferredModel": "TBC",
 "Format": "Tri-level or black burst, 59.94 or 60 Hz - open",
 "Distribution": "To the reference inputs of downstream devices - TBC", "Status": "TBC",},
        visible=("Model", "Status")),
    "SCALER_TBC": dict(
        lib="sitara-video", ref="SW", w=30.48, dashed=True, exclude_bom=True,
        desc="Placeholder scaler - built for the library, not placed in the drawings",
        pins=[("VID-IN-1", "L", "input"), ("VID-OUT-1", "R", "output")],
        fields={"Model": "TBC", "Status": "PLACEHOLDER",},
        visible=("Status",)),
    "DA_HDMI_1X2_TBC": dict(
        lib="sitara-video", ref="DA", w=30.48, dashed=True, exclude_bom=True,
        desc="Placeholder HDMI distribution amplifier 1x2 - built, NOT placed (placeholder)",
        pins=[("HDMI-IN", "L", "input")] + _n("HDMI-OUT", 2, "R", "output"),
        fields={"Model": "TBC", "Status": "PLACEHOLDER",},
        visible=("Status",)),
    "DA_HDMI_1X4_TBC": dict(
        lib="sitara-video", ref="DA", w=30.48, dashed=True, exclude_bom=True,
        desc="Placeholder HDMI distribution amplifier 1x4 - built, NOT placed (placeholder)",
        pins=[("HDMI-IN", "L", "input")] + _n("HDMI-OUT", 4, "R", "output"),
        fields={"Model": "TBC", "Status": "PLACEHOLDER",},
        visible=("Status",)),
    "EXTENDER_FIBER_HDMI21_TX": dict(
        lib="sitara-video", ref="EXT", w=30.48,
        desc="HDMI 2.1 / DP 1.4 over fiber extender, transmitter",
        pins=[("HDMI-IN", "L", "input"), ("FIBER-OUT", "R", "output")],
        fields={"Model": "TBC", "Status": "TBC",},
        visible=("Model",)),
    "EXTENDER_FIBER_HDMI21_RX": dict(
        lib="sitara-video", ref="EXT", w=30.48,
        desc="HDMI 2.1 / DP 1.4 over fiber extender, receiver",
        pins=[("FIBER-IN", "L", "input"), ("HDMI-OUT", "R", "output")],
        fields={"Model": "TBC", "Status": "TBC",},
        visible=("Model",)),

    # ------------------------------------------------------------------ sitara-displays
    "LED_WALL_AOTO_3SURFACE": dict(
        lib="sitara-displays", ref="LED", w=35.56,
        desc="LED wall (ceiling + wall + floor, AOTO AE/RM) as one 19-feed load; no detail past the processors",
        pins=_n("FEED", 19, "L", "input"),
        fields={"Model": "AOTO AE (floor) / AOTO RM (ceiling, wall) - split inferred from spec sheets, TBC", "PreferredModel": "AOTO AE / RM",
 "Surfaces": "Ceiling 8320x6400 | Wall 8320x1920 | Floor 8320x6400", "Canvas": "8320x14720 (122.5 MP)",
 "Pitch": "TBC (AE 1.56/2.31 mm; RM 1.56/1.95/2.31 mm - '2 mm' is not an AOTO SKU)",
 "Feeds": "19 (one per SX40; feed-to-surface mapping TBC)", "Status": "TBC",},
        visible=("Model",)),
    "CARD_NVIDIA_RTX_PRO_SYNC": dict(
        lib="sitara-computers", ref="SYNC", w=30.48,
        desc="NVIDIA RTX PRO Sync card (frame lock / genlock). Shown for PCIe slot accounting",
        pins=[("PCIe-X4", "L", "output"), ("GENLOCK-IN", "L", "input"), ("GENLOCK-LOOP", "R", "output")],
        fields={"PowerIncludedIn": "host", "Model": "NVIDIA RTX PRO Sync", "PreferredModel": "NVIDIA RTX PRO Sync",
 "Usage": "Added separately (not sold by Dell)", "SlotWidth": "1 (retailer listing; vendor datasheet not found)", "Lanes": "Drawn as x4 for slot accounting. Reportedly uses no PCIe data lines (sync runs over ribbon cables to each GPU), electrical lanes not published", "Status": "TBC"},
        visible=("Model", "Usage")),
    "AUDIO_INTERFACE_FOCUSRITE_SCARLETT_2I2": dict(
        lib="sitara-computers", ref="AUD", w=35.56,
        desc="Focusrite Scarlett 2i2 USB audio interface used as the render node sound card (line outputs L/R + headphones)",
        pins=[("USB-IN", "L", "bidirectional"), ("AUDIO-OUT-L", "R", "output"), ("AUDIO-OUT-R", "R", "output"), ("AUDIO-HP", "R", "output")],
        fields={"PowerIncludedIn": "host", "Model": "Focusrite Scarlett 2i2", "PreferredModel": "Focusrite Scarlett 2i2", "Generation": "Older unit (1st or 2nd gen), TBC",
 "Outputs": "2x 1/4 in balanced line out (one stereo pair); 1x 1/4 in TRS headphone out",
 "Connection": "USB 2.0 to the render node (interface-end connector TBC, likely Type-B)", "Status": "CONFIRMED"},
        visible=("Model", "Outputs")),
    "AUDIO_DESTINATION_TBC": dict(
        lib="sitara-computers", ref="AUDX", w=30.48, dashed=True, exclude_bom=True,
        desc="Placeholder for the audio system that receives the render node's stereo pair",
        pins=[("AUDIO-IN-L", "L", "input"), ("AUDIO-IN-R", "L", "input")],
        fields={"Model": "TBC (house audio system)", "PreferredModel": "TBC", "InputConnector": "TBC", "Status": "PLACEHOLDER"},
        visible=("Model", "Status")),
    "COMPUTER_PROTECTLI_V1210": dict(
        lib="sitara-computers", ref="SURV", w=35.56,
        desc="Protectli Vault V1210 (2-port, Intel N5105) - surveyor node: headless StarWatch monitoring and remote-ops node",
        pins=[("PWR-IN", "L", "power_in"), ("RJ45-1", "R", "bidirectional"), ("RJ45-2", "R", "bidirectional")],
        fields={"Model": "Protectli V1210 (2-port)", "PreferredModel": "Protectli V1210",
 "Processor": "Intel N5105 quad-core, 2.0 GHz base / 2.9 GHz turbo", "RAM": "4 GB LPDDR4 on-board (soldered)",
 "Storage": "500 GB NVMe SSD (Kingston NV3), M.2", "Network": "2x Intel I226-V 2.5 GbE RJ45",
 "OS": "Ubuntu Server 26.04", "Role": "Surveyor node (StarWatch + MeshCentral)",
 "Software": "Sitara surveyor app (headless StarWatch, survey drivers: remote control and health of the render-node application) + MeshCentral (remote / out-of-band management)",
 "Power": "12 V DC adapter (draw not listed)", "Mounting": "TBC (VESA or shelf)",
 "Status": "CONFIRMED",
 "Usage": "Monitoring / remote-ops node on the same LAN as the render node."},
        visible=("Model", "Role")),
    "NETWORK_HOUSE_LAN_TBC": dict(
        lib="sitara-networking", ref="NET", w=35.56, dashed=True, exclude_bom=True,
        desc="House network - placeholder until the switches are confirmed. Everything connects to the house LAN.",
        pins=[("NET-MGMT", "L", "bidirectional"), ("NET-SHOW", "L", "bidirectional"), ("NET-LED", "L", "bidirectional"),
              ("NET-UPLINK", "R", "bidirectional")],
        fields={"Model": "TBC (house switches)", "PreferredModel": "TBC",
 "Topology": "Switches, VLANs, IP plan, uplink - all TBC", "Status": "PLACEHOLDER",},
        visible=("Model", "Status")),

    # ------------------------------------------------------------------ generic AV building blocks (placeholders until a model is chosen)
    "SWITCHER_HDMI_MATRIX_4X4": dict(
        lib="sitara-video", ref="SW", w=30.48, dashed=True, exclude_bom=True,
        desc="Generic 4x4 HDMI matrix switcher - placeholder until a model is chosen",
        pins=_n("HDMI-IN", 4, "L", "input") + [("LAN", "L", "bidirectional")] + _n("HDMI-OUT", 4, "R", "output"),
        fields={"Model": "TBC", "Status": "PLACEHOLDER"}, visible=("Status",)),
    "DA_SDI_1X4": dict(
        lib="sitara-video", ref="DA", w=30.48, dashed=True, exclude_bom=True,
        desc="Generic SDI distribution amplifier 1x4 - placeholder until a model is chosen",
        pins=[("SDI-IN", "L", "input")] + _n("SDI-OUT", 4, "R", "output"),
        fields={"Model": "TBC", "Status": "PLACEHOLDER"}, visible=("Status",)),
    "CONVERTER_SDI_TO_HDMI": dict(
        lib="sitara-video", ref="CONV", w=30.48, dashed=True, exclude_bom=True,
        desc="Generic SDI to HDMI converter - placeholder until a model is chosen",
        pins=[("SDI-IN", "L", "input"), ("HDMI-OUT", "R", "output")],
        fields={"Model": "TBC", "Status": "PLACEHOLDER"}, visible=("Status",)),
    "CONVERTER_HDMI_TO_SDI": dict(
        lib="sitara-video", ref="CONV", w=30.48, dashed=True, exclude_bom=True,
        desc="Generic HDMI to SDI converter - placeholder until a model is chosen",
        pins=[("HDMI-IN", "L", "input"), ("SDI-OUT", "R", "output")],
        fields={"Model": "TBC", "Status": "PLACEHOLDER"}, visible=("Status",)),
    "PROJECTOR_GENERIC": dict(
        lib="sitara-displays", ref="PRJ", w=30.48, dashed=True, exclude_bom=True,
        desc="Generic projector with HDMI and SDI inputs - placeholder until a model is chosen",
        pins=[("HDMI-IN-1", "L", "input"), ("SDI-IN-1", "L", "input"), ("LAN", "L", "bidirectional")],
        fields={"Model": "TBC", "Status": "PLACEHOLDER"}, visible=("Status",)),
    "AUDIO_DANTE_ENDPOINT_2X2": dict(
        lib="sitara-audio", ref="AUD", w=30.48, dashed=True, exclude_bom=True,
        desc="Generic Dante endpoint, 2 analog in and 2 analog out - placeholder until a model is chosen",
        pins=[("AUDIO-IN-L", "L", "input"), ("AUDIO-IN-R", "L", "input"), ("RJ45-1", "R", "bidirectional"),
              ("AUDIO-OUT-L", "R", "output"), ("AUDIO-OUT-R", "R", "output")],
        fields={"Model": "TBC", "Status": "PLACEHOLDER"}, visible=("Status",)),
    "AMPLIFIER_STEREO_GENERIC": dict(
        lib="sitara-audio", ref="AMP", w=30.48, dashed=True, exclude_bom=True,
        desc="Generic stereo amplifier - placeholder until a model is chosen",
        pins=[("AUDIO-IN-L", "L", "input"), ("AUDIO-IN-R", "L", "input"), ("PWR-IN", "L", "power_in"),
              ("SPEAKER-L", "R", "output"), ("SPEAKER-R", "R", "output")],
        fields={"Model": "TBC", "Status": "PLACEHOLDER"}, visible=("Status",)),
}

LIBS = sorted({s["lib"] for s in SYMBOLS.values()})

# Body width grows to fit the longest pin names on each side at the symbol text size (multiples of 2.54 mm)
import math as _math
from kicad_sym_writer import TEXT as _TEXT
_CHAR = _TEXT * 0.96
for _name, _spec in SYMBOLS.items():
    _l = max([len(p[0]) for p in _spec["pins"] if p[1] == "L"] or [0])
    _r = max([len(p[0]) for p in _spec["pins"] if p[1] == "R"] or [0])
    _need = (_l + _r) * _CHAR + 5.08
    _spec["w"] = max(_spec["w"], _math.ceil(_need / 2.54) * 2.54)

# Symbols removed from the libraries on the next build (renamed or replaced)
RETIRED = ["AUDIO_INTERFACE_USB_2STEREO", "AUDIO_INTERFACE_TBC"]
