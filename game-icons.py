#!/usr/bin/env python3
import io
import math
import os
import string
import sys
import argparse
from pathlib import Path

from reportlab.lib.colors import Color, toColor
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF


def find_svgs(root: Path):
    if not root.exists():
        raise FileNotFoundError(f"Input directory does not exist: {root}")
    svgs = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(".svg"):
                svgs.append(Path(dirpath) / fn)
    svgs.sort(key=lambda p: (str(p.parent), p.name))
    return svgs


def compute_grid(page_w: float, page_h: float, cell: float):
    cols = max(1, int(page_w // cell))
    rows = max(1, int(page_h // cell))
    used_w = cols * cell
    used_h = rows * cell
    off_x = (page_w - used_w) / 2.0
    off_y = (page_h - used_h) / 2.0
    return cols, rows, off_x, off_y


def draw_svg_clipped(
    c: canvas.Canvas,
    svg_path: Path,
    cell_x: float,
    cell_y: float,
    *,
    cell_size: float,
    circle_diameter: float,
    grid_stroke_pt: float,
    grid_stroke_gray: float,
    circle_fill: Color,
    foreground_hex: str,
):
    """Draw a single cell:
       - white 1x1 in cell
       - black circle (default 0.9 in) centered
       - SVG scaled so its bounding square fits inside that circle
       - hairline cell outline on top
    """
    clip_radius = circle_diameter / 2.0
    icon_max_side_inside_circle = circle_diameter / math.sqrt(2.0)

    # 1) Outer cell: WHITE background
    c.saveState()
    c.setFillColorRGB(1, 1, 1)
    c.rect(cell_x, cell_y, cell_size, cell_size, stroke=0, fill=1)
    c.restoreState()

    # 2) Define circular clip centered in the cell
    cx = cell_x + cell_size / 2.0
    cy = cell_y + cell_size / 2.0
    c.saveState()
    clip_path = c.beginPath()
    clip_path.circle(cx, cy, clip_radius)
    c.clipPath(clip_path, stroke=0, fill=0)

    # 3) Inside the circle: fill with the requested background color
    c.setFillColor(circle_fill)
    c.circle(cx, cy, clip_radius, stroke=0, fill=1)

    # 4) Draw the SVG on top, scaled to fit the inscribed square
    try:
        drawing = load_svg_with_foreground(svg_path, foreground_hex)
    except Exception as e:
        c.restoreState()
        print(f"[WARN] Skipping {svg_path}: {e}")
        return

    dw = float(getattr(drawing, "width", 0) or 0)
    dh = float(getattr(drawing, "height", 0) or 0)
    if dw <= 0 or dh <= 0:
        c.restoreState()
        print(f"[WARN] Skipping {svg_path}: invalid SVG size ({dw}x{dh})")
        return

    target_side_pts = icon_max_side_inside_circle  # in points
    scale = min(target_side_pts / dw, target_side_pts / dh)

    draw_w = dw * scale
    draw_h = dh * scale
    draw_x = cell_x + (cell_size - draw_w) / 2.0
    draw_y = cell_y + (cell_size - draw_h) / 2.0

    c.saveState()
    c.translate(draw_x, draw_y)
    c.scale(scale, scale)
    renderPDF.draw(drawing, c, 0, 0)
    c.restoreState()

    # 5) End clipping
    c.restoreState()

    # 6) Hairline grid outline (on top so it's visible)
    c.saveState()
    c.setLineWidth(grid_stroke_pt)
    c.setStrokeGray(grid_stroke_gray)
    c.rect(cell_x, cell_y, cell_size, cell_size, stroke=1, fill=0)
    c.restoreState()


def load_svg_with_foreground(svg_path: Path, foreground_hex: str):
    svg_text = svg_path.read_text(encoding="utf-8")
    hex_lower = foreground_hex.lower()
    hex_upper = foreground_hex.upper()
    svg_text = svg_text.replace("#fff", hex_lower).replace("#FFF", hex_upper)
    return svg2rlg(io.BytesIO(svg_text.encode("utf-8")))


def parse_color(value: str, *, default: str) -> tuple[Color, str]:
    raw = (value or default).strip()
    if not raw:
        raw = default

    if raw.startswith("#"):
        color_spec = raw
    elif len(raw) in (3, 6) and all(ch in string.hexdigits for ch in raw):
        color_spec = f"#{raw}"
    else:
        color_spec = raw

    color = toColor(color_spec)

    # ReportLab's ``hexval`` includes a ``0x`` prefix (e.g., ``0x00ff00``).
    # Normalize the color to the standard ``#rrggbb`` format expected by web
    # colors so downstream code receives the canonical representation.
    r = max(0, min(255, int(round(color.red * 255))))
    g = max(0, min(255, int(round(color.green * 255))))
    b = max(0, min(255, int(round(color.blue * 255))))
    hex_value = f"#{r:02x}{g:02x}{b:02x}"
    return color, hex_value


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Lay out SVGs on an A4 grid of 1\" cells with 0.9\" black circles and clipped icons."
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory to recursively scan for .svg files.",
    )
    parser.add_argument(
        "output_pdf",
        type=Path,
        help="Path to the output PDF file (e.g., ~/Downloads/icons-grid.pdf).",
    )

    # A couple of sensible, future-friendly options:
    parser.add_argument(
        "--page",
        choices=["A4", "A4landscape"],
        default="A4",
        help="Page size/orientation (default: A4 portrait).",
    )
    parser.add_argument(
        "--cell-size-in",
        type=float,
        default=1.0,
        help="Cell side length in inches (default: 1.0).",
    )
    parser.add_argument(
        "--circle-diameter-in",
        type=float,
        default=0.9,
        help="Circle diameter in inches (default: 0.9).",
    )
    parser.add_argument(
        "--grid-hairline-pt",
        type=float,
        default=0.25,
        help="Grid stroke width in points (default: 0.25).",
    )
    parser.add_argument(
        "--grid-gray",
        type=float,
        default=0.2,
        help="Grid stroke gray level in [0,1], lower=darker (default: 0.2).",
    )
    parser.add_argument(
        "--foreground",
        default="fff",
        help="Foreground color for the SVG paths (default: fff).",
    )
    parser.add_argument(
        "--background",
        default="000",
        help="Background color for the circle clip (default: 000).",
    )

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    input_dir: Path = args.input_dir.expanduser()
    output_pdf: Path = args.output_pdf.expanduser()

    if not input_dir.exists():
        print(f"ERROR: Input directory does not exist: {input_dir}", file=sys.stderr)
        return 2

    # Ensure output directory exists
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    try:
        _foreground_color, foreground_hex = parse_color(args.foreground, default="fff")
        background_color, _background_hex = parse_color(args.background, default="000")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    # Page size
    pagesize = A4
    if args.page == "A4landscape":
        pagesize = landscape(A4)
    else:
        pagesize = portrait(A4)

    PAGE_WIDTH, PAGE_HEIGHT = pagesize
    CELL_SIZE = args.cell_size_in * inch
    CIRCLE_DIAMETER = args.circle_diameter_in * inch
    GRID_STROKE_PT = float(args.grid_hairline_pt)
    GRID_STROKE_GRAY = min(max(args.grid_gray, 0.0), 1.0)

    svgs = find_svgs(input_dir)
    if not svgs:
        print(f"ERROR: No SVGs found under: {input_dir}", file=sys.stderr)
        return 1

    c = canvas.Canvas(str(output_pdf), pagesize=pagesize)
    cols, rows, off_x, off_y = compute_grid(PAGE_WIDTH, PAGE_HEIGHT, CELL_SIZE)
    per_page = cols * rows

    for idx, svg in enumerate(svgs):
        cell_index = idx % per_page
        if cell_index == 0 and idx != 0:
            c.showPage()  # new page

        col = cell_index % cols
        row = cell_index // cols
        cell_x = off_x + col * CELL_SIZE
        cell_y = off_y + row * CELL_SIZE

        draw_svg_clipped(
            c,
            svg,
            cell_x,
            cell_y,
            cell_size=CELL_SIZE,
            circle_diameter=CIRCLE_DIAMETER,
            grid_stroke_pt=GRID_STROKE_PT,
            grid_stroke_gray=GRID_STROKE_GRAY,
            circle_fill=background_color,
            foreground_hex=foreground_hex,
        )

    c.save()
    print(
        f"✅ Wrote {len(svgs)} icons to {output_pdf} "
        f"({cols}×{rows} cells; {per_page} icons/page; page={args.page})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
