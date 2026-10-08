# Sitara KiCad color theme

`Sitara.json` is a KiCad color theme for the schematic editor. It keeps KiCad's default schematic colors and changes one thing: the drawing sheet (frame, grid references and title block) is drawn in Sitara's brand black (Aster, `#1E1E1E`) instead of KiCad's default dark red. Pair it with `worksheet_template/template.kicad_wks`, whose title block carries the Sitara logo.

## Use it in KiCad
1. Copy `Sitara.json` to your KiCad colors folder and name it `sitara.json`:
   - Windows: `%APPDATA%\kicad\10.0\colors\`
   - Linux: `~/.config/kicad/10.0/colors/`
   - macOS: `~/Library/Preferences/kicad/10.0/colors/`
2. Restart KiCad, open the schematic editor, then Preferences → Schematic Editor → Colors, and choose **Sitara** in the theme list.

The theme is a per-user setting, so each person who opens a project needs to do this once.

## Use it from the command line
`kicad-cli sch export pdf --theme Sitara ...` (and `export svg`). The theme file must be in the colors folder above. The FirstSnow build script copies it there before exporting.

## Editing
The brand palette (Asia Violet `#967DFF`, Pumpkin `#FA941B`, Aster `#1E1E1E`, Bosco `#E6F0FF`) can be used for other colors; keep changes small so symbols stay legible.
