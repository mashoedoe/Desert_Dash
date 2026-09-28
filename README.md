# Desert Dash

**Stage explorer: https://mashoedoe.github.io/Desert_Dash/stages.html**

Interactive maps and elevation profiles for the five Desert Dash stages, with GPX downloads and the official stage maps.

All source material comes from the Desert Dash website: https://desertdashnamibia.com/the-route/

## Contents

- `stages.html` — the stage explorer, served by GitHub Pages
- `Resources/Stages/` — per-stage GPX tracks, map and profile images, official stage map PDFs, and build scripts (see its [README](Resources/Stages/README.md))
- `Resources/` — original route GPX, 2025 booklet and maps

## Rebuilding

Requires Python with `numpy` and `pymupdf`.

```powershell
python Resources\Stages\build_explorer.py   # regenerates stages.html
python Resources\Stages\serve_explorer.py   # local preview
```
