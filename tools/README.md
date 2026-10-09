# tools

Python tooling for the AV signal-flow drawings. Needs Python 3.10+ and KiCad 10 (`kicad-cli` on PATH, or set `KICAD_CLI`).

| Script | What it does |
|---|---|
| `new_project.py <folder> --name N [--build] [--strict]` | Scaffold a new drawing project: lib tables, `_generator/` skeleton, optional first build. Starter drawing = render node + reference + network + server. Installs the Sitara color theme. |
| `build_template.py` | Regenerate `templates/sitara-av-project`, the KiCad "new project from template" version (needs path variable `SITARA_KICAD`; GUI behaviour not yet confirmed). |
| `build_blocks.py [--check]` | Regenerate the design blocks in `av_blocks/` from `sitara_av/blocks.py`. |
| `migrate_pins.py [--apply]` | One-off: renamed legacy hand-drawn pin names to `FORMAT-DIR-n`. Record in `av_components/_migration/pin_renames.json`. |
| `leak_scan.py` | Public-repo hygiene scan (emails, phones, prices, quote refs, local paths, tokens, plus a private name list). |
| `check_repo.py [--fast]` | Everything CI runs: symbols and blocks up to date, libraries load, pin naming, leak scan, scaffold smoke test. |

## `sitara_av` package

`Context` + `Sheet` write schematics; `palette` holds the wire colors and the line patterns used by the print variant; `checks` has
the format and PCIe-lane checks; `build` generates, upgrades, runs ERC, exports color PDF/SVG/PNG and a black-and-white
print PDF in which formats are told apart by line pattern and width, not by color; `blocks` holds the reusable assemblies; `overlap` estimates text collisions (the build fails in --strict mode on any); `reporting` draws the cloud / site-LAN data-flow page (also the REPORTING_ARCHITECTURE_A block); `power` sums PowerW fields into the power note on a sheet; `tbc` writes the open-items register sheet and the count on the root sheet (skill `av-tbc-register`).

## Public-repo leak scan

Generic patterns are in the script. Client, venue and people names are not stored in the repo: put one per line in a
gitignored `.leak-terms` file at the repo root, and in the GitHub repository secret `SITARA_LEAK_TERMS` for CI.
A line known to be safe can carry the marker `leak-ok`.

## CI

`.github/workflows/ci.yml` runs the leak scan and `check_repo.py` (KiCad 10 from the KiCad PPA). The workflow has not run yet; the first push will show whether the PPA install step needs adjusting.
