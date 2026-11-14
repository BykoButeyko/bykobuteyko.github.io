"""Builds the chart on the stablecoin issuance page from the stablecoin-flows repo (run its fetch.py first).

The SVG goes between <!-- chart:deciles --> and <!-- /chart:deciles --> in the page.

  python scripts/stablecoin_charts.py path/to/stablecoin-flows
"""
import re, sys
from pathlib import Path

PAGE = Path(__file__).parent.parent / "research" / "stablecoin-issuance" / "index.html"
W, H, LEFT, RIGHT, TOP, BOTTOM = 640, 330, 34, 8, 52, 280
LO, HI, GRID = -10, 8, (-10, -7.5, -5, -2.5, 2.5, 5, 7.5)
# colors also set as SVG attributes, so the chart renders even with a cached style.css
TRAIN, TEST, BAND = "#3987e5", "#e66767", "#3987e5"


def svg(m_tr, lo_tr, hi_tr, m_te, lo_te, hi_te):
    step = (W - LEFT - RIGHT) / 10
    x = lambda k: LEFT + (k - 0.5) * step  # k = 1..10
    y = lambda v: TOP + (HI - v) / (HI - LO) * (BOTTOM - TOP)
    out = [f'<text x="0" y="12" class="coin">Bitcoin return the week after, %</text>',
           f'<rect x="{x(10) - step / 2:.1f}" y="{TOP}" width="{step:.1f}" height="{BOTTOM - TOP}" fill="#f0efec" opacity=".05"/>']
    for v in GRID:
        out.append(f'<line x1="{LEFT}" x2="{W - RIGHT}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="grid" stroke="#2c2c2a"/>'
                   f'<text x="{LEFT - 6}" y="{y(v) + 4:.1f}" class="tick" text-anchor="end">{v:g}</text>')
    band = [f"{x(k):.1f},{y(v):.1f}" for k, v in zip(range(1, 11), hi_tr)] + \
           [f"{x(k):.1f},{y(v):.1f}" for k, v in reversed(list(zip(range(1, 11), lo_tr)))]
    out.append(f'<polygon points="{" ".join(band)}" fill="{BAND}" opacity=".16"/>')
    out.append(f'<line x1="{LEFT}" x2="{W - RIGHT}" y1="{y(0):.1f}" y2="{y(0):.1f}" class="mid" stroke="#898781" stroke-dasharray="3 3"/>'
               f'<text x="{LEFT - 6}" y="{y(0) + 4:.1f}" class="tick" text-anchor="end">0</text>')
    pts = " ".join(f"{x(k):.1f},{y(v):.1f}" for k, v in zip(range(1, 11), m_tr))
    out.append(f'<polyline points="{pts}" fill="none" stroke="{TRAIN}" stroke-width="2" stroke-linejoin="round"/>')
    for k, v in zip(range(1, 11), m_tr):
        out.append(f'<circle cx="{x(k):.1f}" cy="{y(v):.1f}" r="3.5" fill="{TRAIN}"/>')
    out.append(f'<line x1="{x(10):.1f}" x2="{x(10):.1f}" y1="{y(hi_te[-1]):.1f}" y2="{y(lo_te[-1]):.1f}" stroke="{TEST}" stroke-width="2"/>')
    for v in (hi_te[-1], lo_te[-1]):
        out.append(f'<line x1="{x(10) - 6:.1f}" x2="{x(10) + 6:.1f}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{TEST}" stroke-width="2"/>')
    for k, v in zip(range(1, 11), m_te):
        cx, cy = x(k), y(v)
        out.append(f'<rect x="{cx - 4.5:.1f}" y="{cy - 4.5:.1f}" width="9" height="9" fill="{TEST}" '
                   f'transform="rotate(45 {cx:.1f} {cy:.1f})"/>')
    out.append(f'<text x="{x(10) + step / 2 - 4:.1f}" y="{y(lo_te[-1]) + 20:.1f}" class="val" text-anchor="end" fill="#f0efec">'
               f'Test: {m_te[-1]:+.1f}%</text>'
               f'<text x="{x(10) + step / 2 - 4:.1f}" y="{y(m_tr[-1]) - 10:.1f}" class="val" text-anchor="end" fill="#f0efec">'
               f'Training: {m_tr[-1]:+.1f}%</text>')
    for k in range(1, 11):
        out.append(f'<text x="{x(k):.1f}" y="{BOTTOM + 18}" class="tick" text-anchor="middle">{k}</text>')
    out.append(f'<text x="{x(1):.1f}" y="{BOTTOM + 34}" class="tick" text-anchor="middle">least issued</text>'
               f'<text x="{x(10):.1f}" y="{BOTTOM + 34}" class="tick" text-anchor="middle">most issued</text>')
    # legend
    out.append(f'<g class="legend"><line x1="0" x2="18" y1="32" y2="32" stroke="{TRAIN}" stroke-width="2"/>'
               f'<circle cx="9" cy="32" r="3.5" fill="{TRAIN}"/><text x="24" y="36">2021-23, where I set the threshold, with 95% band</text>'
               f'<rect x="{392 - 4.5}" y="{32 - 4.5}" width="9" height="9" fill="{TEST}" transform="rotate(45 392 32)"/>'
               f'<text x="404" y="36">2024-26 test</text></g>')
    return (f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="Average bitcoin return the week after, '
            f'by decile of weekly stablecoin issuance: 2021-23 training and 2024-26 test">{"".join(out)}</svg>')


if __name__ == "__main__":
    repo = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(repo))
    import build
    from chart import by_decile
    train, test = build.split(build.frame())
    train, test = train.dropna(subset=["r_next"]), test.dropna(subset=["r_next"])
    chart = svg(*by_decile(train), *by_decile(test))
    html = PAGE.read_text(encoding="utf-8")
    html = re.sub(r"<!-- chart:deciles -->.*?<!-- /chart:deciles -->",
                  lambda m: f"<!-- chart:deciles -->{chart}<!-- /chart:deciles -->", html, flags=re.S)
    PAGE.write_text(html, encoding="utf-8")
    print(len(train), "training weeks,", len(test), "test weeks, last", test.index.max().date())
