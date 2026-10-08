---
name: av-tbc-register
description: Keep the open-items ("to be confirmed", TBC) register of a Sitara AV drawing - one list with owner, expected date and note, shown as a register sheet plus a count on the root sheet. Use when asked to add, change, close or assign open items on a drawing, to show what is still unconfirmed, or to add a TBC page to a new project.
---

# TBC register for AV drawings

Every Sitara AV drawing keeps its unconfirmed facts in **one list** that produces two things:

- a **register sheet** (A3, last page): `#`, item, detail line, owner, expected date, note, one row per item
- a **summary box** on the root sheet: how many are open, how many per owner, which items have a date, and which sheet holds the register

Code: `tools/sitara_av/tbc.py` (`Item`, `register_sheet`, `summary`). New projects from `tools/new_project.py` already include the register with two example items. FirstSnow keeps its list in `_generator/gen_schematic.py` (`TBC_ROWS`).

## Editing the list

Edit the list in the project's `gen_schematic.py`, then run `python _generator/build_all.py --strict`. Never edit the `.kicad_sch` files.

```python
from sitara_av import tbc
TBC = [
    tbc.Item("SDI card model and slot", "DeckLink or AJA", "Sitara", "Oct 28", "decides slot use"),
    tbc.Item("House switches, VLANs, uplink", "", "Client", "", ""),
]
```

Fields: `item` (one line), `detail` (optional second line, smaller), `owner` (who must confirm it: a person or company), `expected` (date, only when known), `note`.

## Rules

- **Owner means who has to answer.** Use "Sitara" when we confirm it ourselves (arrival of a unit, a document we can read) and the other party's name when we are waiting on them. Leave it empty rather than guessing; it shows as "-" and counts as "unassigned".
- **Dates only when known.** Do not put an estimate in `expected`; put it in `note`. A dated item is listed on the root-sheet summary.
- **Close an item by deleting it.** Do not mark done in place; the count is the length of the list. Write the confirmed fact into the symbol field or the drawing instead (symbols: `av_components/_generator/symbols_spec.py`, never hand-edit the library).
- **Facts on the drawing are not cited to sources**, and the register holds questions, not answers. In a public repo (`sitara-kicad`) keep client, person and price details out; the project folder (private) may name owners.
- **Capacity:** up to 14 rows fit one sheet; `register_sheet` raises beyond that. Split the list or add a second register sheet.
- Keep the root summary box and the root `subsheet` box in place when copying the pattern to a new project (see `tools/new_project.py`, `system()` for the positions). Root sheet text stays at the note size (2.29 mm); use `T` for anything else.

## Check

After a change: `build_all.py --strict` (ERC 0, format/PCIe checks OK), then open the last PNG in `exports/RevA/png` and check rows are not cut off and the root sheet count matches the register.
