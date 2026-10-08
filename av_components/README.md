## Modular Computer Design (Nested Components)

### The Three-Tier System

Computers are designed using a **nested component approach** to avoid combinatorial explosion of variants:

**Tier 1: Generic Computer Chassis**
Base computer types by form factor:
- `COMPUTER_TOWER_WORKSTATION`
- `COMPUTER_SFF_STANDARD`
- `COMPUTER_TINY_COMPACT`
- `COMPUTER_RACKMOUNT_1U`
- `COMPUTER_RACKMOUNT_2U`

**Tier 2: Specific Product Lines**
More specific variants when I/O differs significantly:
- `COMPUTER_LENOVO_THINKSTATION_P3`
- `COMPUTER_LENOVO_THINKSTATION_P7`
- `COMPUTER_DELL_PRECISION_3660`

**Tier 3: Internal Expansion Modules**
Separate symbols that nest inside computers:
- `GPU_NVIDIA_RTX_PRO_6000_BLACKWELL_MAXQ` (double-width GPU)
- `CAPTURE_CARD_SDI_12G_4CH` (4-channel 12G-SDI card)
- `CARD_NVIDIA_RTX_PRO_SYNC` (frame lock / genlock card)

### Why Nested Components?

**Problem:** A computer line with 5 models × 10 GPU options × 3 capture card options = 150 symbol variants

**Solution:** 5 computer symbols + 10 GPU symbols + 3 capture card symbols = 18 symbols total

**Benefits:**
- Reflects physical modularity (GPUs are separate, replaceable)
- Matches procurement process (spec computer, then spec GPU)
- Easy to show multi-GPU configurations
- Components are reusable across computer models
- Clear signal paths (displays connect to specific GPU)

### Explicit PCIe Connections (Option B)

**Decision:** Use explicit pin connections for internal expansion slots.

**Implementation (slots are claims):**
- Computer symbols have one slot pin per physical slot, an **input** named by slot number, generation and lanes, e.g. `PCIe-Slot-2-G5x16`
- Expansion card symbols have an **output** pin named by lanes, e.g. `PCIe-X16`, `PCIe-X8`
- A card wider than one slot has a second output pin, `PCIe-ADJ`, wired to the neighbouring slot
- Draw wires between them on the schematic
- Two cards on one slot join two outputs on a net, which ERC reports as an error, so over-commitment is caught automatically
- ERC cannot compare lane counts; the project build script checks that a card's lanes do not exceed its slot's lanes

**Why not just visual nesting?**
- Explicit connections support multi-GPU systems cleanly
- Can document which slot each card occupies
- Enables power budget tracking (sum all connected card TDPs)
- Signal path is traceable (Display 1 → GPU 2 → Slot 3)
- KiCad ERC can validate configurations (two cards on same slot, power over budget)

### Computer Symbol Pin Layout

**External I/O Pins (1-16+):**
```
pin 1:  "Power-Input"
pin 2:  "USB-C-Front"
pin 3:  "USB-A-Front-1"
...
pin 16: "RJ45-2"
```

**Internal PCIe Slot Pins:**
```
"PCIe-Slot-1-G5x8"
"PCIe-Slot-2-G5x16"
"PCIe-Slot-3-G4x4"     # x8 physical, x4 electrical
...
```

**Note:** Slot pin names carry the slot number, PCIe generation and electrical lanes, so a card can be checked against the slot it claims. Use the vendor manual's slot numbering and note the source of the numbering in the symbol's `PCIeConfig` field.

**Power Distribution Pins:**
```
pin 21: "PCIe-Power-Bus"    # Supplies aux power to cards
pin 22: "PSU-Capacity"       # Informational capacity value
```

**Pin Types:**
- External I/O: `input`, `output`, or `bidirectional` as appropriate
- PCIe slots: `input` (claimed by a card's `output` pin)
- Power bus: `power_out`
- PSU capacity: `passive`

### GPU/Expansion Card Pin Layout

**Connection Pins:**
```
pin 1:  "PCIe-X16"           # Output: claims the computer's slot pin
pin 2:  "PCIe-ADJ"           # Second output on a double-width card; wire to the neighbouring slot
```

**Function Pins (GPU example):**
```
pin 2:  "DisplayPort-1"
pin 3:  "DisplayPort-2"
pin 4:  "DisplayPort-3"
pin 5:  "DisplayPort-4"
```

**Power Pins:**
```
pin 6:  "Power-PCIe"         # Auxiliary power from PSU
```

**Pin Types:**
- PCIe claim: `output`
- Display outputs: `output`
- Power input: `power_in`

### Multi-GPU Example

```
COMPUTER_LENOVO_THINKSTATION_P7
├── PCIe-Slot-1(x16) → GPU_NVIDIA_RTX6000
│   ├── DisplayPort-1 → Display 1
│   ├── DisplayPort-2 → Display 2
│   ├── DisplayPort-3 → Display 3
│   └── DisplayPort-4 → Display 4
├── PCIe-Slot-2(x16) → GPU_NVIDIA_RTX4000
│   ├── DisplayPort-1 → Display 5
│   ├── DisplayPort-2 → Display 6
│   ├── DisplayPort-3 → Display 7
│   └── DisplayPort-4 → Display 8
└── PCIe-Slot-3(x8) → CAPTURE_CARD_DECKLINK
    ├── SDI-In-1 → Camera 1
    └── SDI-In-2 → Camera 2
```

Signal paths are explicit. Power budget can be calculated. Installation is documented.

### Computer Symbol Properties

```
property "PreferredModel" "Lenovo ThinkStation P7"
property "FormFactor" "Tower Workstation"
property "PCIeConfig" "4x PCIe Gen4: 2x x16, 1x x8, 1x x4"
property "PSU" "1000W (1350W optional)"
property "MaxGPUs" "4 (with proper cooling)"
property "Notes" "Slots 1-2 share bandwidth if both x16 populated"
```

### GPU Symbol Properties

```
property "PreferredModel" "NVIDIA RTX 6000 Ada Generation"
property "VRAM" "48GB GDDR6"
property "DisplayOutputs" "4x DisplayPort 1.4a"
property "PCIeInterface" "x16 Gen4"
property "PowerDraw" "300W TDP"
property "PowerConnectors" "1x 16-pin (12VHPWR)"
property "CoolingSlots" "Triple-slot width"
```

### When to Create Separate Computer Symbols

**Do create separate if:**
- Different form factors (Tower vs SFF vs Tiny)
- Significantly different I/O layouts
- Different PCIe slot configurations
- Different generation with incompatible slots (DDR4 vs DDR5 platform)

**Don't create separate for:**
- Different CPU models (i5 vs i7 vs i9) - note in properties
- Different RAM amounts - note in properties
- Different storage configs - note in properties
- Minor model year updates with same I/O

Use properties to document CPU/RAM/storage options that vary within same chassis.

## Pin names and generic symbols

All AV symbols use `FORMAT-DIR-n` pin names (`HDMI-OUT-1`, `DP-IN-1`, `RJ45-1`, `PWR-IN`, `USB-A-REAR-1`). The older hand-drawn
symbols were migrated by `tools/migrate_pins.py` (rename table: `_migration/pin_renames.json`); pin numbers did not change, so
existing schematics keep their wiring but show the new labels. Pins the script could not classify (PCIe slots, RS232, GPIO,
power rails) were left alone.

Generic placeholders in `sitara-video`, `sitara-displays` and the new `sitara-audio` (matrix switcher, SDI/HDMI converters,
SDI/HDMI distribution amplifiers, projector, Dante endpoint, stereo amplifier) are dashed and excluded from the BOM until a
real model replaces them. Add or change generated symbols in `_generator/symbols_spec.py`, then run `build_symbols.py`.
