# sitara-kicad

KiCad 10 libraries and tooling from Sitara Systems.

- `av_components/` - symbol libraries for AV signal-flow drawings (computers, video, displays, audio, network, ...) and their generator
- `av_blocks/` - reusable design blocks (render node, D8 + SX40 processing stack, surveyor node, audio)
- `tools/` - the `sitara_av` drawing generator, project scaffolder, checks (see `tools/README.md`)
- `templates/` - KiCad project template
- `themes/` - the Sitara KiCad color theme; `worksheet_template/` - the drawing sheet
- `morphogencc_library/` - PCB parts

New drawing project: `python tools/new_project.py ../MyShow --name MyShow --build`
