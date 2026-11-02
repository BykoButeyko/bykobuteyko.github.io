"""Renders PNGs from the charts on the whales page: the link-preview card (og.png) and
1200x675 images for posts. Builds one SVG per image and rasterises it with resvg.

  pip install resvg-py
  python scripts/render.py [post_dir]
"""
import re, sys
from pathlib import Path

import resvg_py

ROOT = Path(__file__).parent.parent
PAGE = ROOT / "research" / "hyperliquid-whales" / "index.html"
BG, LINE, INK, INK2, MUTED, SHORT = "#0d0d0d", "#2c2c2a", "#f0efec", "#c3c2b7", "#898781", "#e66767"
FONT = "Segoe UI, Arial, sans-serif"

# The page styles its charts with CSS variables; resvg needs plain colors.
STYLE = f"""
text {{ font-family: {FONT}; }}
.chart text {{ font-size: 13px; fill: {MUTED}; }}
.chart .coin {{ fill: {INK}; font-weight: 600; }}
.chart .legend text {{ fill: {INK2}; }}
.chart .val.unh {{ fill: {INK}; font-weight: 600; }}
.chart .val.raw {{ fill: {INK2}; }}
.chart .grid {{ stroke: {LINE}; stroke-width: 1; }}
.chart .mid {{ stroke: {MUTED}; stroke-width: 1; stroke-dasharray: 3 3; }}
.chart .link {{ stroke: {MUTED}; stroke-width: 2; }}
.chart circle.raw {{ fill: {BG}; stroke: {INK2}; stroke-width: 2; }}
.chart circle.unh {{ fill: {SHORT}; stroke: {BG}; stroke-width: 2; }}
.chart .line {{ fill: none; stroke-width: 2; stroke-linejoin: round; }}
.chart .line.raw {{ stroke: {INK2}; stroke-dasharray: 4 3; stroke-width: 1.5; }}
.chart .line.unh {{ stroke: {SHORT}; }}
"""


def chart(name):
    html = PAGE.read_text(encoding="utf-8")
    svg = re.search(rf"<!-- chart:{name} -->(.*?)<!-- /chart:{name} -->", html, re.S).group(1)
    vb = re.search(r'viewBox="([^"]+)"', svg).group(1)
    inner = svg[svg.index(">") + 1: svg.rindex("</svg>")]
    return vb, inner


def text(x, y, s, size, fill, weight=400, anchor="start"):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{s}</text>'


def card(w, h, lines, name, top, bottom=40):
    """lines: (text, size, color, weight) stacked from the top; chart fills the space below."""
    out, y = [], 0
    for s, size, fill, weight in lines:
        y += size * 1.35 if y else top
        out.append(text(64, y, s, size, fill, weight))
    vb, inner = chart(name)
    cy, ch = y + 30, h - (y + 30) - bottom - 40
    out.append(f'<svg class="chart" x="64" y="{cy}" width="{w - 128}" height="{ch}" viewBox="{vb}">{inner}</svg>')
    out.append(text(64, h - bottom, "Byko Buteyko", 20, MUTED))
    out.append(text(w - 64, h - bottom, "bykobuteyko.com", 20, MUTED, anchor="end"))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<style>{STYLE}</style><rect width="{w}" height="{h}" fill="{BG}"/>{"".join(out)}</svg>')


IMAGES = {
    "og.png": (1200, 630, 1, [("Hyperliquid · accounts above $1M", 22, MUTED, 400),
                               ("How much of the whale short is a bet?", 46, INK, 650)], "shift", 70),
    "post-shift.png": (1200, 675, 2, [("Short share of $1M+ accounts: raw vs unhedged", 38, INK, 650),
                                      ("Unhedged = without market makers, vaults, relative-value books", 22, INK2, 400),
                                      ("and shorts hedged with spot or staked coins on Hyperliquid", 22, INK2, 400)], "shift", 70),
    "post-time.png": (1200, 675, 2, [("Short share of $1M+ accounts, every 15 minutes", 38, INK, 650)], "time", 70),
}


def render(out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, (w, h, zoom, lines, ch, top) in IMAGES.items():
        png = resvg_py.svg_to_bytes(svg_string=card(w, h, lines, ch, top), zoom=zoom)
        dest = (PAGE.parent if name == "og.png" else out_dir) / name
        dest.write_bytes(bytes(png))
        print(dest)


if __name__ == "__main__":
    render(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "posts")
