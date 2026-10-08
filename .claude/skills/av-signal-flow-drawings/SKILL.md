---
name: av-signal-flow-drawings
description: Build AV signal-flow drawings in KiCad 10 with the Sitara symbol libraries (render nodes, media servers, scalers, LED processors, sync, audio, network). Use when asked to draw how an AV system is wired, add or change AV symbols in av_components, use or create design blocks, or check these libraries against KiCad 10.
---

# AV signal-flow drawings in KiCad 10

KiCad is used here as a connectivity model, not a drafting tool: every port is a pin, every cable is a net, ERC checks signal direction, the netlist can be turned into a cable list when one is wanted, and `kicad-cli` exports the PDFs. It is good for port-level wiring drawings (what plugs into what). Do not use it for rack elevations, cable-pathway drawings, or anything needing auto-layout.

## Where things live

- `av_components/sitara-*.kicad_sym` - the AV libraries (computers, displays, cameras, networking, power, video, ...). Read `av_components/README.md` for the nested-component model (chassis symbols with PCIe slot pins, cards as separate symbols).
- `av_components/_generator/symbols_spec.py` - spec for generated symbols. Edit the spec, never the generated symbols. Symbols listed in its `RETIRED` list are deleted from the libraries on the next build (use it when a symbol is renamed or replaced).
- `av_components/_generator/build_symbols.py` - writes the spec into the libraries, upgrades to the current KiCad format, and splices symbols in. Existing symbols that are neither in the spec nor in `RETIRED` are left byte-for-byte untouched. Run `python build_symbols.py --check` first.
- `av_blocks/*.kicad_blocks/` - design block libraries (see Design blocks below).
- `worksheet_template/template.kicad_wks` - the Sitara drawing sheet (set per project via a `${KIPRJMOD}`-relative path).
- `themes/Sitara.json` - the Sitara KiCad color theme (black, brand-colored drawing-sheet frame). Select it in Preferences, and export with `kicad-cli ... --theme Sitara`; see `themes/README.md`.
- `tools/new_project.py` scaffolds a project (generator + lib tables); `tools/sitara_av/` is the sheet writer, palette, checks and build; `tools/check_repo.py` runs all repo checks; `templates/` holds the KiCad-native template. A print build (black and white, formats by line pattern) is produced next to the color PDF.
- Open items (TBC): `tools/sitara_av/tbc.py` and the `av-tbc-register` skill. Keep the list in the project generator, one list for the register sheet and the root-sheet count.
- `morphogencc_library/` is PCB electronics. Leave it out of AV drawings.

## Conventions

- **Pin names are `FORMAT-DIR-n`**, uppercase, hyphenated: `SDI-OUT-1`, `HDMI2.0-IN`, `DP1.4-IN`, `REF-IN`, `TESSERA-OUT-1`, `RJ45-1G`. The format prefix is what the format-check script reads, so keep it exact.
- **Electrical type is the role in the drawing.** Video, SDI, fiber, audio and reference sources are `output`, sinks are `input`; network and USB are `bidirectional`; power is `power_out`/`power_in`. ERC then catches output-to-output wiring and undriven inputs. Bidirectional SDI cards are drawn as outputs with a `PortMode` field.
- **PCIe slots are claims.** The chassis slot pin is an `input` named with slot number, generation and lanes (`PCIe-Slot-3-G4x8`); each card has an `output` pin named with its lanes (`PCIe-X8`). Two cards on one slot is an ERC error. A card wider than one slot gets a second output pin (`PCIe-ADJ`) wired to the neighbouring slot. The project build script also flags a card whose lanes exceed its slot. Use the vendor manual's slot numbering.
- **Layout**: inputs on the left, outputs on the right, control and power below. Signal flows left to right.
- **Text and pitch**: symbol text is 1.78 mm and pins sit 3.81 mm apart (`TEXT` and `PITCH` in `kicad_sym_writer.py`), so A3 sheets stay readable printed on A4. Symbol bodies widen automatically to fit the pin names. Keep notes and labels at the same size, and split a page rather than shrinking text.
- **Wire colors**: color means format and is the same in every project (legend order: video, audio and USB, then network, reference and PCIe). Sitara's hero hues go to the most common digital video formats: HDMI = Asia Violet, DisplayPort = Pumpkin. Rarer formats (12G-SDI magenta, Tessera teal, audio blue, USB brown) get secondary hues; network, reference and PCIe are muted neutrals, with dashes marking network and reference. Hues are deepened for at least 3:1 contrast and checked for color-vision confusion between wires that share a page.
- **Fields** carry facts (`Model`, `PartNumber`, `Status`, `Role`, ...). Show the identifying field (`Model` or `PreferredModel`) and `Role` on the drawing; hide the rest. They still export to the BOM.
- **Unconfirmed items**: a device not yet identified is a `PLACEHOLDER` symbol drawn with a dashed outline and excluded from the BOM; a known device with unconfirmed details carries `Status` = `TBC` and is drawn solid. Never invent a make or model. Say this in the title block and legend. Notes about what is TBC are welcome on the sheets, but do not cite sources for claims on the drawing; the drawing is confirmed through the project's review document.
- **Nets and buses**: group parallel cables of four or more on a vector bus (`SDI[1..4]`, `PROC[1..19]`) and name the members. Where a second path would have to cross a bus, join the nets with matching net labels instead. Use hierarchical sheets to keep pages readable, explicit wire colors per format, and a legend.
- **No-connect flags** on every deliberately unused port, so ERC reports only real gaps.
- **Project-specific notes are overlays**: notes, comments and slot assignments belong on the project sheets, not in library symbols or design blocks.
- Keep project-specific facts (client names, quote numbers, prices, email sources) out of this repo. It is public. Library symbols stay generic.

## Workflow

1. Gather the real system facts and mark every unconfirmed one TBC. State open questions rather than guessing.
2. Add any missing symbols to `symbols_spec.py`, run `build_symbols.py`, confirm all libraries still load.
3. Build the schematic (a generator script per project writes the `.kicad_sch` files; hand-drawing in the GUI is fine for small sheets). Add the project's `sym-lib-table` entries, and a `design-block-lib-table` entry if it uses design blocks, with `${KIPRJMOD}`-relative paths. Keep unrelated libraries (for example the PCB electronics library) out of AV projects.
4. Verify with `kicad-cli`, then **render the pages to PNG and look at them**:
   ```bash
   kicad-cli sch upgrade <sheet>
   kicad-cli sch erc --severity-all -o erc.txt <root.kicad_sch>
   kicad-cli sch export netlist --format kicadxml -o net.xml <root.kicad_sch>
   kicad-cli sch export pdf --draw-hop-over -o out.pdf <root.kicad_sch>
   pdftoppm -r 110 -png out.pdf page
   ```
   ERC clean is not enough: overlaps, clipped text and wires through symbols only show up in the render.
5. If a cable list is requested, derive it from the netlist (one cable per output-to-input connection, one per network port to the switch), not from the BOM. A BOM lists devices; connections only exist in the netlist. Skip internal PCIe links and record lengths as TBC until a site survey.

## Design blocks

A design block is a saved, reusable piece of schematic. A library is a folder `<name>.kicad_blocks/`; each block is a folder `<BLOCK>.kicad_block/` holding `<BLOCK>.kicad_sch` and `<BLOCK>.json` (description and keywords). In the schematic editor, open the Design Blocks panel to place one.

- Blocks hold only the generic assembly: the devices, their internal wiring and interface labels. No project notes, titles or per-project comments.
- Name variants explicitly (`RENDER_NODE_A`, later `RENDER_NODE_B`) in the same library.
- A block checked alone shows ERC errors for inputs its host sheet supplies (for example a `REF-IN` driven by a net on the project sheet) and for libraries that are not in scope; they clear once the block sits in a project.

## Gotchas

Read `references/gotchas.md` before scripting schematics or editing library files. The short list: net-class colors do not plot from the CLI (set explicit wire colors), text with newlines does not parse, a symbol's `Value` must equal its name, everything sits on a 1.27 mm grid, and ERC cannot see format mismatches (DP into HDMI) or PCIe lane mismatches.
