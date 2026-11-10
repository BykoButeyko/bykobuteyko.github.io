"""Renders the home page's link-preview card (og.png at the site root).

  pip install resvg-py
  python scripts/og_home.py
"""
from pathlib import Path

import resvg_py

ROOT = Path(__file__).parent.parent
W, H = 1200, 630
BG, SURFACE, LINE, INK, INK2, MUTED = "#0d0d0d", "#1a1a19", "#2c2c2a", "#f0efec", "#c3c2b7", "#898781"
OK, WIP, LINK = "#4fb286", "#d9a54a", "#7fb0ef"
FONT = "Segoe UI, Arial, sans-serif"

# (status color, status, title) for each research card, as on the home page
PROJECTS = [
    (OK, "Published", "How much of the whale short is a bet?"),
    (OK, "Published", "Do Hyperliquid longs still pay more than Binance longs?"),
    (WIP, "In progress", "When do Hyperliquid liquidations cascade?"),
]


def text(x, y, s, size, fill, weight=400, anchor="start", spacing=0):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" letter-spacing="{spacing}">{s}</text>')


def card():
    out = [f'<rect width="{W}" height="{H}" fill="{BG}"/>',
           f'<rect x="0" y="0" width="{W}" height="6" fill="{LINK}"/>',
           text(72, 132, "Byko Buteyko", 68, INK, 700, spacing=-1),
           text(72, 186, "Market research built from raw data:", 30, INK2),
           text(72, 226, "positioning, flows and forced selling.", 30, INK2)]
    y = 280
    for color, status, title in PROJECTS:
        out.append(f'<rect x="72" y="{y}" width="{W - 144}" height="76" rx="12" fill="{SURFACE}" stroke="{LINE}"/>')
        out.append(f'<circle cx="100" cy="{y + 38}" r="6" fill="{color}"/>')
        out.append(text(118, y + 46, status.upper(), 17, color, 600, spacing=1))
        out.append(text(278, y + 47, title, 25, INK, 600))
        out.append(text(W - 100, y + 47, "→", 25, MUTED, anchor="end"))
        y += 90
    out.append(text(W - 72, H - 34, "bykobuteyko.com", 22, MUTED, anchor="end"))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<style>text {{ font-family: {FONT}; }}</style>{"".join(out)}</svg>')


if __name__ == "__main__":
    dest = ROOT / "og.png"
    dest.write_bytes(bytes(resvg_py.svg_to_bytes(svg_string=card())))
    print(dest)
