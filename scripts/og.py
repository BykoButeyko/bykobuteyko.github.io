"""Renders the link-preview cards (1200x630) for the home page and the funding and cascade notes.
The whale note's card comes from render.py.

  pip install resvg-py
  python scripts/og.py
"""
import re
from pathlib import Path

import resvg_py

ROOT = Path(__file__).parent.parent
W, H = 1200, 630
BG, SURFACE, LINE, INK, INK2, MUTED = "#0d0d0d", "#1a1a19", "#2c2c2a", "#f0efec", "#c3c2b7", "#898781"
OK, WIP, LINK, LONG = "#4fb286", "#d9a54a", "#7fb0ef", "#3987e5"
FONT = "Segoe UI, Arial, sans-serif"

# The pages style their charts with CSS variables; resvg needs plain colors.
STYLE = f"""
text {{ font-family: {FONT}; }}
.chart text {{ font-size: 12px; fill: {MUTED}; }}
.chart .coin {{ fill: {INK}; font-weight: 600; font-size: 13px; }}
.chart .grid {{ stroke: {LINE}; stroke-width: 1; }}
.chart .mid {{ stroke: {MUTED}; stroke-width: 1; stroke-dasharray: 3 3; }}
.chart .line {{ fill: none; stroke-width: 2; stroke-linejoin: round; }}
.chart .line.gap {{ stroke: {LONG}; }}
"""

# (status color, status, title) for each research card, as on the home page
PROJECTS = [
    (OK, "Published", "How much of the whale short is a bet?"),
    (OK, "Published", "Do Hyperliquid longs still pay more than Binance longs?"),
    (WIP, "In progress", "When do Hyperliquid liquidations cascade?"),
]


def text(x, y, s, size, fill, weight=400, anchor="start", spacing=0):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" letter-spacing="{spacing}">{s}</text>')


def lines(x, y, rows, size, fill, weight=400, gap=1.3):
    return [text(x, y + i * size * gap, r, size, fill, weight) for i, r in enumerate(rows)]


def status(x, y, color, label):
    return [f'<circle cx="{x + 6}" cy="{y - 6}" r="6" fill="{color}"/>',
            text(x + 22, y, label.upper(), 17, color, 600, spacing=1)]


def frame(body):
    out = [f'<rect width="{W}" height="{H}" fill="{BG}"/>', f'<rect width="{W}" height="6" fill="{LINK}"/>',
           *body, text(72, H - 34, "Byko Buteyko", 22, MUTED), text(W - 72, H - 34, "bykobuteyko.com", 22, MUTED, anchor="end")]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<style>{STYLE}</style>{"".join(out)}</svg>')


def chart(page, name):
    html = page.read_text(encoding="utf-8")
    svg = re.search(rf"<!-- chart:{name} -->(.*?)<!-- /chart:{name} -->", html, re.S).group(1)
    return re.search(r'viewBox="([^"]+)"', svg).group(1), svg[svg.index(">") + 1: svg.rindex("</svg>")]


def home():
    body = [text(72, 132, "Byko Buteyko", 68, INK, 700, spacing=-1),
            *lines(72, 186, ["Market research built from raw data:", "positioning, flows and forced selling."], 30, INK2, gap=1.33)]
    y = 280
    for color, label, title in PROJECTS:
        body += [f'<rect x="72" y="{y}" width="{W - 144}" height="76" rx="12" fill="{SURFACE}" stroke="{LINE}"/>',
                 *status(94, y + 45, color, label), text(278, y + 47, title, 25, INK, 600),
                 text(W - 100, y + 47, "→", 25, MUTED, anchor="end")]
        y += 90
    # the home card carries its own name at the top, so it skips the footer name
    return frame(body).replace(text(72, H - 34, "Byko Buteyko", 22, MUTED), "")


def funding():
    vb, inner = chart(ROOT / "research" / "hyperliquid-funding" / "index.html", "gap")
    body = [*status(72, 96, OK, "Published"),
            *lines(72, 160, ["Do Hyperliquid longs", "still pay more than", "Binance longs?"], 46, INK, 700, gap=1.2),
            *lines(72, 350, ["The gap averaged about 6.5% a year", "from 2023 to 2026. In 2026 it sits", "at 1 to 5%, about what T-bills pay."], 23, INK2, gap=1.45),
            f'<rect x="620" y="60" width="508" height="480" rx="14" fill="{SURFACE}" stroke="{LINE}"/>',
            f'<svg class="chart" x="644" y="80" width="460" height="400" viewBox="{vb}">{inner}</svg>',
            text(644, 516, "Hyperliquid minus Binance funding, 30-day mean, % a year", 15, MUTED)]
    return frame(body)


def cascades():
    body = [*status(72, 96, WIP, "In progress"),
            *lines(72, 168, ["When do Hyperliquid", "liquidations cascade?"], 58, INK, 700, gap=1.18),
            *lines(72, 318, ["Liquidations, trade flow, funding, open interest and book depth",
                             "on BTC, ETH, SOL and HYPE, recorded since 5 November 2026."], 24, INK2, gap=1.45)]
    y = 410
    for i, s in enumerate(["Method fixed before the data", "No results before 30 cascades", "First results around Feb 2027"]):
        x = 72 + i * 356
        body += [f'<rect x="{x}" y="{y}" width="340" height="64" rx="12" fill="{SURFACE}" stroke="{LINE}"/>',
                 text(x + 20, y + 40, s, 19, INK, 600)]
    return frame(body)


CARDS = {"og.png": home, "research/hyperliquid-funding/og.png": funding,
         "research/hyperliquid-liquidations/og.png": cascades}

if __name__ == "__main__":
    for path, make in CARDS.items():
        (ROOT / path).write_bytes(bytes(resvg_py.svg_to_bytes(svg_string=make())))
        print(ROOT / path)
