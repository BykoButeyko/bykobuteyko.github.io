"""Builds the charts on the Hyperliquid whales page from a copy of hl_whales.db.

The SVG goes straight into the HTML between <!-- chart:NAME --> and <!-- /chart:NAME -->,
so the page stays one file and the charts pick up the page's colors.

  python scripts/charts.py path/to/hl_whales.db
"""
import re, sqlite3, sys
from datetime import datetime, timezone
from pathlib import Path

PAGE = Path(__file__).parent.parent / "research" / "hyperliquid-whales" / "index.html"
COINS = ["BTC", "ETH", "SOL", "HYPE"]
LO, HI = 20, 70          # shared y range in %, so the coins compare directly


def load(db_path):
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    rows = db.execute("SELECT ts, coin, long_ntl, short_ntl, dir_long_ntl, dir_short_ntl FROM series_a ORDER BY ts").fetchall()
    series = {c: [] for c in COINS}
    for ts, coin, l, s, dl, ds in rows:
        if coin in series and l + s > 0 and dl + ds > 0:
            series[coin].append((ts, 100 * s / (l + s), 100 * ds / (dl + ds)))
    return db, series


def dumbbell(series):
    w, row, top, left, right = 640, 44, 46, 56, 24
    h = top + row * len(COINS) + 30
    x = lambda v: left + (v - LO) / (HI - LO) * (w - left - right)
    out = [f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="Raw and unhedged short share of $1M+ accounts per coin">']
    out.append(f'<g class="legend"><circle cx="{left}" cy="14" r="5" class="raw"/><text x="{left + 12}" y="18">Raw short share</text>'
               f'<circle cx="{left + 150}" cy="14" r="5" class="unh"/><text x="{left + 162}" y="18">Unhedged directional</text></g>')
    for v in range(LO, HI + 1, 10):
        out.append(f'<line x1="{x(v)}" x2="{x(v)}" y1="{top - 10}" y2="{h - 26}" class="{"mid" if v == 50 else "grid"}"/>'
                   f'<text x="{x(v)}" y="{h - 8}" class="tick" text-anchor="middle">{v}%</text>')
    for i, c in enumerate(COINS):
        _, raw, unh = series[c][-1]
        y = top + i * row + row / 2 - 10
        a, b = sorted((raw, unh))
        out.append(f'<text x="{left - 14}" y="{y + 5}" class="coin" text-anchor="end">{c}</text>'
                   f'<line x1="{x(a)}" x2="{x(b)}" y1="{y}" y2="{y}" class="link"/>')
        # put each value label on the outer side of its dot
        for v, cls, side in ((raw, "raw", 1 if raw > unh else -1), (unh, "unh", 1 if unh >= raw else -1)):
            anchor = "start" if side > 0 else "end"
            out.append(f'<circle cx="{x(v):.1f}" cy="{y}" r="6" class="{cls}"><title>{c} {"raw" if cls == "raw" else "unhedged"}: {v:.1f}% short</title></circle>'
                       f'<text x="{x(v) + side * 12:.1f}" y="{y + 4}" class="val {cls}" text-anchor="{anchor}">{v:.0f}%</text>')
    out.append("</svg>")
    return "".join(out)


def multiples(series):
    pw, ph, gap, block = 300, 150, 40, 206     # block = panel title + plot + date labels
    w, h = pw * 2 + gap, 30 + block * 2
    out = [f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="Short share over time per coin, raw and unhedged">']
    t0 = min(s[0][0] for s in series.values())
    t1 = max(s[-1][0] for s in series.values())
    for i, c in enumerate(COINS):
        ox, oy = (i % 2) * (pw + gap), 30 + (i // 2) * block + 30
        x = lambda t: ox + 30 + (t - t0) / (t1 - t0) * (pw - 34)
        y = lambda v: oy + (HI - v) / (HI - LO) * ph
        _, raw, unh = series[c][-1]
        out.append(f'<text x="{ox}" y="{oy - 14}" class="coin">{c}</text>'
                   f'<text x="{ox + pw}" y="{oy - 14}" class="tick" text-anchor="end">raw {raw:.0f}% · unhedged {unh:.0f}%</text>')
        for v in (30, 50, 70):
            out.append(f'<line x1="{ox + 30}" x2="{ox + pw}" y1="{y(v)}" y2="{y(v)}" class="{"mid" if v == 50 else "grid"}"/>'
                       f'<text x="{ox + 24}" y="{y(v) + 4}" class="tick" text-anchor="end">{v}%</text>')
        for k, cls in ((1, "raw"), (2, "unh")):
            pts = " ".join(f"{x(p[0]):.1f},{y(p[k]):.1f}" for p in series[c])
            out.append(f'<polyline points="{pts}" class="line {cls}"/>')
        if i >= 2:
            for t, anchor in ((t0, "start"), (t1, "end")):
                d = datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%b %d %H:%M")
                out.append(f'<text x="{x(t)}" y="{oy + ph + 18}" class="tick" text-anchor="{anchor}">{d}</text>')
    out.append('<g class="legend"><line x1="0" x2="20" y1="10" y2="10" class="line raw"/><text x="26" y="14">Raw short share</text>'
               '<line x1="150" x2="170" y1="10" y2="10" class="line unh"/><text x="176" y="14">Unhedged directional</text></g>')
    out.append("</svg>")
    return "".join(out)


def facts(db, series):
    print(f"{len(series['BTC'])} snapshots, last {datetime.fromtimestamp(series['BTC'][-1][0] / 1000, timezone.utc):%Y-%m-%d %H:%M} UTC")
    for c in COINS:
        raws = [p[1] for p in series[c]]
        print(f"{c}: raw {raws[-1]:.1f}% unhedged {series[c][-1][2]:.1f}% | raw range {min(raws):.1f}-{max(raws):.1f}")
    for c in COINS:
        side = dict(db.execute("SELECT side, SUM(ntl) FROM breakdown WHERE coin = ? GROUP BY side", (c,)).fetchall())
        hedged = db.execute("SELECT SUM(ntl) FROM breakdown WHERE coin = ? AND label = 'hedged_on_hl'", (c,)).fetchone()[0] or 0
        print(f"{c} all tracked: short {100 * side['short'] / (side['long'] + side['short']):.1f}% | "
              f"shorts ${side['short'] / 1e6:.0f}M, hedged on HL ${hedged / 1e6:.0f}M")


def inject(html, name, svg):
    pat = re.compile(rf"(<!-- chart:{name} -->).*?(<!-- /chart:{name} -->)", re.S)
    return pat.sub(lambda m: m.group(1) + svg + m.group(2), html)


if __name__ == "__main__":
    db, series = load(sys.argv[1])
    html = PAGE.read_text(encoding="utf-8")
    html = inject(html, "shift", dumbbell(series))
    html = inject(html, "time", multiples(series))
    PAGE.write_text(html, encoding="utf-8")
    facts(db, series)
