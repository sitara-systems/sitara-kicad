---
name: av-signal-flow-drawings
description: Build AV signal-flow drawings in KiCad 10 with the Sitara symbol libraries (render nodes, media servers, scalers, LED processors, sync, network). Use when asked to draw how an AV system is wired, add or change AV symbols in av_components, generate a cable list from a drawing, or check these libraries against KiCad 10.
---

# AV signal-flow drawings in KiCad 10

KiCad is used here as a connectivity model, not a drafting tool: every port is a pin, every cable is a net, ERC checks signal direction, the netlist is the cable schedule, and `kicad-cli` exports the PDFs. It is good for port-level wiring drawings (what plugs into what). Do not use it for rack elevations, cable-pathway drawings, or anything needing auto-layout.

## Where things live

- `av_components/sitara-*.kicad_sym` - the AV libraries (computers, displays, cameras, networking, power, video, ...). Read `av_components/README.md` for the nested-component model (chassis symbols with PCIe slot pins, cards as separate symbols).
- `av_components/_generator/symbols_spec.py` - spec for generated symbols. Edit the spec, never the generated symbols.
- `av_components/_generator/build_symbols.py` - writes the spec into the libraries, upgrades to the current KiCad format, and splices symbols in. Existing symbols not in the spec are left byte-for-byte untouched. Run `python build_symbols.py --check` first.
- `worksheet_template/template.kicad_wks` - the Sitara drawing sheet (set per project via `${KIPRJMOD}`-relative path).
- `morphogencc_library/` is PCB electronics. Leave it out of AV drawings.

## Conventions

- **Pin names are `FORMAT-DIR-n`**, uppercase, hyphenated: `SDI-OUT-1`, `HDMI2.0-IN`, `DP-OUT-3`, `REF-IN`, `LED-OUT-1`, `RJ45-1G`. The format prefix is what the format-check script reads, so keep it exact.
- **Electrical type is the role in the drawing**: video, SDI, fiber and reference sources are `output`, sinks are `input`; network, USB and PCIe are `bidirectional`; power is `power_out`/`power_in`. ERC then catches output-to-output wiring and undriven inputs. Bidirectional SDI cards are drawn as outputs with a `PortMode` field.
- **Layout**: inputs on the left, outputs on the right, control/power below. Signal flows left to right.
- **Fields** carry facts (`Model`, `Role`, `Status`, `Resolution`, ...). Show `Model` and `Role` on the drawing, hide the rest; they still export to the BOM.
- **Unconfirmed devices** are marked `Status` = `TBC` or `PLACEHOLDER`, drawn with a dashed outline, and placeholders are excluded from the BOM. Do not invent a make or model; build a placeholder symbol instead. Notes about what is TBC are welcome on the sheets, but do not cite sources for claims on the drawing; the drawing is confirmed through the project's review document.
- **Cable IDs are net names**: label every wire; group parallel cables of four or more on a vector bus (`SDI[1..4]`, `PROC[1..19]`). Use hierarchical sheets to keep pages readable and a legend for wire colors.
- **No-connect flags** on every deliberately unused port, so ERC reports only real gaps.
- Keep project-specific facts (client names, quote numbers, prices, email sources) out of this repo. It is public. Library symbols stay generic.

## Workflow

1. Gather the real system facts and mark every unconfirmed one TBC. State open questions rather than guessing.
2. Add any missing symbols to `symbols_spec.py`, run `build_symbols.py`, confirm all libraries still load.
3. Build the schematic (a generator script per project writes the `.kicad_sch` files; hand-drawing in the GUI is fine for small sheets). Add the project's `sym-lib-table` entries with `${KIPRJMOD}`-relative paths.
4. Verify with `kicad-cli`, then **render the pages to PNG and look at them**:
   ```bash
   kicad-cli sch upgrade <sheet>
   kicad-cli sch erc --severity-all -o erc.txt <root.kicad_sch>
   kicad-cli sch export netlist --format kicadxml -o net.xml <root.kicad_sch>
   kicad-cli sch export pdf --draw-hop-over -o out.pdf <root.kicad_sch>
   pdftoppm -r 110 -png out.pdf page
   ```
   ERC clean is not enough: overlaps, clipped text and wires through symbols only show up in the render.
5. Derive the cable list from the netlist (one cable per output-to-input connection, one per network port to the switch), not from the BOM. A BOM lists devices; connections only exist in the netlist. Skip internal PCIe links. Record lengths as TBC until a site survey.

## Gotchas

Read `references/gotchas.md` before scripting schematics or editing library files. The short list: net-class colors do not plot from the CLI (set explicit wire colors), text with newlines does not parse, a symbol's `Value` must equal its name, everything sits on a 1.27 mm grid, and ERC cannot see format mismatches (DP into HDMI).
