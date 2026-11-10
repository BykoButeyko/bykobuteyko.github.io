"""Builds the chart on the bitcoin ETF basis page from the etf-flows repo (run its fetch.py first).

The SVG goes between <!-- chart:weekly --> and <!-- /chart:weekly --> in the page.

  python scripts/etf_charts.py path/to/etf-flows
"""
import re, sys
from pathlib import Path

import pandas as pd

PAGE = Path(__file__).parent.parent / "research" / "bitcoin-etf-basis" / "index.html"
W, LEFT, RIGHT = 640, 34, 8
PANELS = [  # column, class, title, y range (thousand BTC), gridlines, height
    ("flow_btc", "flow", "ETF net flow, thousand BTC per week", (-40, 55), (-40, -20, 20, 40), 170),
    ("d_short", "short", "Change in leveraged funds' CME net short, thousand BTC per week", (-17, 17), (-15, -10, -5, 5, 10, 15), 120),
]


def svg(w, test_start):
    t0, t1 = w.index.min(), w.index.max()
    span = (t1 - t0).days + 7
    x = lambda t: LEFT + (t - t0).days / span * (W - LEFT - RIGHT)
    bw = 7 / span * (W - LEFT - RIGHT) * 0.72
    out, top = [], 0
    for col, cls, title, (lo, hi), grid, h in PANELS:
        oy = top + 22
        y = lambda v: oy + (hi - v) / (hi - lo) * h
        out.append(f'<text x="0" y="{top + 12}" class="coin">{title}</text>')
        xs = x(test_start)
        out.append(f'<rect x="{xs:.1f}" y="{oy}" width="{W - RIGHT - xs:.1f}" height="{h}" class="shade"/>')
        for v in grid:
            out.append(f'<line x1="{LEFT}" x2="{W - RIGHT}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="grid"/>'
                       f'<text x="{LEFT - 6}" y="{y(v) + 4:.1f}" class="tick" text-anchor="end">{v}</text>')
        for t, v in w[col].items():
            v /= 1000
            y0, y1 = sorted((y(0), y(v)))
            out.append(f'<rect x="{x(t) - bw / 2:.1f}" y="{y0:.1f}" width="{bw:.1f}" height="{max(y1 - y0, 0.5):.1f}" class="bar {cls}"/>')
        out.append(f'<line x1="{LEFT}" x2="{W - RIGHT}" y1="{y(0):.1f}" y2="{y(0):.1f}" class="mid"/>'
                   f'<text x="{LEFT - 6}" y="{y(0) + 4:.1f}" class="tick" text-anchor="end">0</text>')
        top = oy + h + 26
    out.append(f'<text x="{x(test_start) + 6:.1f}" y="36" class="tick">test period</text>')
    for yr in ("2024", "2025", "2026"):
        out.append(f'<text x="{x(pd.Timestamp(yr + "-01-01")):.1f}" y="{top - 8}" class="tick" text-anchor="middle">{yr}</text>')
    hgt = top
    return (f'<svg class="chart" viewBox="0 0 {W} {hgt}" role="img" aria-label="Weekly bitcoin ETF net flow above, '
            f'weekly change in leveraged-fund CME net short below, January 2024 to November 2026">{"".join(out)}</svg>')


if __name__ == "__main__":
    repo = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(repo))
    import build
    w = build.weekly()
    chart = svg(w, build.TEST_START)
    html = PAGE.read_text(encoding="utf-8")
    html = re.sub(r"<!-- chart:weekly -->.*?<!-- /chart:weekly -->",
                  lambda m: f"<!-- chart:weekly -->{chart}<!-- /chart:weekly -->", html, flags=re.S)
    PAGE.write_text(html, encoding="utf-8")
    print(len(w), "weeks, last", w.index.max().date())
