# lazy-game-icons
A simple script to create a printable sheet for Lazy Monster Tokens

First, you're going to want to read the article [Crafting Your Lazy Monster Tokens](https://slyflourish.com/crafting_lazy_monster_tokens.html) by Mike Shea over on Sly Flourish. The article explains what Lazy Monster Tokens are and why you'd want to use them. Hint: For playing in-person Role Playing Games (RPGs). That article already includes a printable PDF that has a bunch of great monster tokens to print out and use. Mike Shea used a selection of icons from https://game-icons.net/.

The script in this repository allows you to create such a printable PDF sheet for many more token designs.
Basically, just point the script to a folder structure filled with the icons, as downloadable from Game-icons.

When downloading the icons, be sure to set the background color to transparent and the forground color to white.
That will let you change these from the command-line.

## Prerequisites

macOS / Linux / Windows

Python 3.9+
Check: python3 --version

(macOS) Homebrew recommended: https://brew.sh

## Quick start (macOS)

````
# 1) Create a project folder and enter it
mkdir -p ~/Projects/icon-pdf && cd ~/Projects/icon-pdf

# 2) Save the script
#    (place game-icons.py here)

# 3) Create & activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 4) Install dependencies
pip install --upgrade pip
pip install reportlab svglib

# 5) Run it
python game-icons.py "/Users/daren/projects/game-icons/black-background" \
  "~/Downloads/icons-grid.pdf"
```

## Usage
python game-icons.py INPUT_DIR OUTPUT_PDF [options]


## Positional arguments

- `INPUT_DIR` — directory to recursively scan for .svg files
- `OUTPUT_PDF` — output file path (e.g., `~/Downloads/icons-grid.pdf`)

## Options

- `--page {A4,A4landscape}`
  Page size/orientation. Default: A4 (portrait).

- `--cell-size-in FLOAT`
  Cell side length in inches. Default: 1.0.

- `--circle-diameter-in FLOAT`
  Circle diameter in inches. Default: 0.9.

- `--grid-hairline-pt FLOAT`
  Grid line stroke width in points. Default: 0.25.

- `--grid-gray FLOAT`
  Grid gray level in [0,1] (lower = darker). Default: 0.2.

- `--foreground COLOR`
  Foreground color to apply to white `#fff` fills/strokes inside the SVGs. Accepts CSS color names or hex (with/without `#`). Default: `fff`.

- `--background COLOR`
  Fill color for the circular token background. Accepts CSS color names or hex (with/without `#`). Default: `000`.

- `--annotate`
  Include a non-clickable tooltip per icon that displays the SVG path relative to the input directory (disabled by default).

## Examples

```
# Default layout (A4 portrait, 1.0" cells, 0.9" circle)
python game-icons.py "./icons" "./icons-grid.pdf"

# Landscape A4 with darker hairline and smaller (0.8") circle
python game-icons.py "./icons" "./icons-grid.pdf" \
  --page A4landscape --circle-diameter-in 0.8 --grid-gray 0.1

# Bigger cells (1.25") while keeping a 0.9" circle
python game-icons.py "./icons" "./icons-grid.pdf" \
  --cell-size-in 1.25 --circle-diameter-in 0.9

# Light blue icons on a black background with tooltips enabled
python game-icons.py "./icons" "./icons-grid.pdf" \
  --foreground lightblue --background 000 --annotate
```

## How it works

- **Grid**: packs as many cell_size_in squares as fit on the A4 page, centered.
- **Circle**: drawn and clipped per cell, exact diameter = --circle-diameter-in.
- **Scaling**: each SVG is scaled so its max side ≤ circle_diameter / √2, preserving aspect ratio.
- **Hairline grid**: a thin rectangle stroke is drawn on top of each cell for cutting guidance.

## Project layout

```
your-project/
├─ game-icons.py
├─ README.md
└─ (optional) requirements.txt
```

## Troubleshooting

No SVGs found: confirm your INPUT_DIR path and that files end with .svg.

Fonts look different: ReportLab renders vector paths; embedded fonts in SVGs may be converted. If you need exact text rendering, convert text to outlines in the source SVGs.

Margins too tight: use --cell-size-in to change packing density or switch to --page A4landscape.

Tips for printing & cutting

The 0.9″ circle inside a 1.0″ cell leaves a small tolerance for cutting/punching.

You can faintly preview the circle edge by adding an optional stroke in the script (commented in code).

For US Letter, adapt the page size in code or add a --page option variant.

## License

This project is dedicated to the public domain under CC0 1.0 Universal.
To the extent possible under law, I waive all copyright and related or neighboring rights to this work.

See the included LICENCE file for the full text of the CC0 1.0 Universal Public Domain Dedication.
SPDX-License-Identifier: CC0-1.0

## Contributing

PRs welcome! Ideas: --margins, crop marks at N/E/S/W, page headers/footers, per-folder sections, or exporting multiple sizes in one run.


