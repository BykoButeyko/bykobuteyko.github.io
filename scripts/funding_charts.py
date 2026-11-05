"""Builds the chart on the Hyperliquid funding page from a copy of funding.db (hyperliquid-funding-gap repo).

Same idea as charts.py: the SVG goes between <!-- chart:gap --> and <!-- /chart:gap --> in the page.

  python scripts/funding_charts.py path/to/funding.db
"""
import re, sqlite3, sys
from datetime import datetime, timezone
from pathlib import Path

PAGE = Path(__file__).parent.parent / "research" / "hyperliquid-funding" / "index.html"
COINS = ["BTC", "ETH", "SOL", "HYPE"]
HOUR = 3_600_000
LO, HI = -30, 60         # shared y range, % a year
W, H, GAP_X, TOP = 270, 150, 70, 30


def hourly(db, venue, coin):
    """Per-hour rate keyed by the hour it ends at; each settlement spread over the hours since the last one."""
    rows = db.execute("SELECT time, rate FROM funding WHERE venue=? AND coin=? ORDER BY time", (venue, coin)).fetchall()
    out, prev = {}, None
    for t, r in rows:
        h = round(t / HOUR)
        if prev is None:
            n = 1 if venue == "hl" else 8
        else:
            n = min(max(h - prev, 1), 8)
        for k in range(h - n + 1, h + 1):
            out[k] = r / n
        prev = h
    return out


def series(db, coin):
    """30-day trailing mean of HL minus Binance, % a year, one point per week."""
    hl, bn = hourly(db, "hl", coin), hourly(db, "bn", coin)
    hours = sorted(set(hl) & set(bn))
    gap = [(h, (hl[h] - bn[h]) * 8760 * 100) for h in hours]
    pts, win, total, j = [], 30 * 24, 0.0, 0
    for i, (h, g) in enumerate(gap):
        total += g
        while gap[j][0] <= h - win:
            total -= gap[j][1]
            j += 1
        if i - j + 1 >= 20 * 24 and h % 168 == 0:
            pts.append((h, total / (i - j + 1)))
    return pts


def svg(data):
    t0 = min(p[0][0] for p in data.values() if p)
    t1 = max(p[-1][0] for p in data.values() if p)
    x = lambda h, ox: ox + (h - t0) / (t1 - t0) * W
    y = lambda v, oy: oy + (HI - min(max(v, LO), HI)) / (HI - LO) * H
    out = [f'<svg class="chart" viewBox="0 0 640 {2 * (H + TOP + 40)}" role="img" '
           f'aria-label="30-day mean funding gap, Hyperliquid minus Binance, per coin">']
    for i, coin in enumerate(COINS):
        ox, oy = 30 + (i % 2) * (W + GAP_X), TOP + (i // 2) * (H + TOP + 40)
        pts = data[coin]
        out.append(f'<text x="{ox - 30}" y="{oy - 12}" class="coin">{coin}</text>')
        if pts:
            out.append(f'<text x="{ox + W}" y="{oy - 12}" class="tick" text-anchor="end">last 30 days {pts[-1][1]:.1f}%</text>')
        for v in (0, 20, 40, 60, -20):
            cls = "mid" if v == 0 else "grid"
            out.append(f'<line x1="{ox}" x2="{ox + W}" y1="{y(v, oy):.1f}" y2="{y(v, oy):.1f}" class="{cls}"/>'
                       f'<text x="{ox - 6}" y="{y(v, oy) + 4:.1f}" class="tick" text-anchor="end">{v}</text>')
        for yr in (2024, 2025, 2026):
            h = datetime(yr, 1, 1, tzinfo=timezone.utc).timestamp() * 1000 / HOUR
            out.append(f'<text x="{x(h, ox):.1f}" y="{oy + H + 18}" class="tick" text-anchor="middle">{yr}</text>')
        line = " ".join(f"{x(h, ox):.1f},{y(v, oy):.1f}" for h, v in pts)
        out.append(f'<polyline points="{line}" class="line gap"/>')
    out.append("</svg>")
    return "".join(out)


if __name__ == "__main__":
    db = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
    data = {c: series(db, c) for c in COINS}
    chart = svg(data)
    html = PAGE.read_text(encoding="utf-8")
    html = re.sub(r"<!-- chart:gap -->.*?<!-- /chart:gap -->", lambda m: f"<!-- chart:gap -->{chart}<!-- /chart:gap -->",
                  html, flags=re.S)
    PAGE.write_text(html, encoding="utf-8")
    print({c: round(p[-1][1], 1) for c, p in data.items() if p})
