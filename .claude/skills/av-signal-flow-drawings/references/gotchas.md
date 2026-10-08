# Gotchas (KiCad 10.0.x, found by testing with kicad-cli)

## Drawing and plotting
- **Net-class colors do not plot from the CLI.** Net classes defined in the project with name patterns render in the default wire color in PDF/SVG. An explicit per-wire stroke color does plot. Treat the explicit color as the real mechanism; net classes only help on screen.
- **No one-to-many fan-out.** A pin cannot be a bus. A "x19" group still needs 19 pins and 19 bus entries. A distribution amp is a symbol with N output pins.
- **Format mismatches are invisible to ERC.** A DisplayPort output wired to an HDMI input is just output-to-input. Encode the format in the pin name and check it with a script over the netlist (one format family per net unless a converter is on it).
- **Embedded symbol copies drift.** Each schematic caches its symbols; ERC warns `lib_symbol_mismatch` when the library has moved on. Run "Update Symbols from Library" before each release.
- **Exports:** `--draw-hop-over` draws wire crossings as hops. `--exclude-drawing-sheet` gives clean SVGs for embedding in documents.
- **Variants:** KiCad 10 has design variants (`--variant` on exports). Not tried here, but it is the native way to show "primary active / backup active" from one drawing.

## Scripting schematics and symbols
- All connection points sit on a **1.27 mm grid**. Off-grid endpoints are ERC warnings. Labels must sit exactly on a wire end. Wires are strict two-point segments.
- **Text with embedded newlines is unparseable** in text and text-box items. Use one box per paragraph.
- In generated symbol files, **unit sub-symbols are unprefixed** (`NAME_0_1`), and the `Value` property must equal the bare symbol name or ERC reports `lib_symbol_mismatch`.
- Write KiCad 8-era syntax and run `kicad-cli sch upgrade` / `sym upgrade --force` to normalize to the current format; hand-writing the newest format is fragile.
- Pin function names in a netlist carry the pin number suffix (`SDI-OUT-1_3`); strip `_<n>` before matching names.
- Global labels used on only one sheet raise an "only appears once" warning. Hierarchical labels and sheet pins must match exactly, including bus ranges.

## Libraries
- Symbol libraries upgrade cleanly with `kicad-cli sym upgrade`. Upgrades add `show_name`, `do_not_autoplace`, `in_pos_files` and `duplicate_pin_numbers_are_jumpers` defaults and re-sort pins; nothing else changes. The result will not open in KiCad 9.
- A **single bad footprint makes `kicad-cli fp` refuse the whole `.pretty` library** ("Unable to load library"). KiCad 10 rejects a pad with a zero size dimension, for example `(size 3.3 0)` on a non-plated hole. Use `(size 3.3 3.3)`. Test each footprint in its own folder to find the culprit.
- A file with a misspelled extension (`.kicad_symb`) is silently ignored by KiCad.
- Submodule checkouts may be a detached HEAD; check out `main` before committing.
- This repo is public. Do not put client names, quote numbers, prices or email references in symbol fields or descriptions.
