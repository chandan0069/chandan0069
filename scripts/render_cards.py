#!/usr/bin/env python3
"""Render animated SVG cards for the GitHub profile README.

Everything is drawn with plain SVG + CSS keyframes + SMIL, which keep working
when the SVG is shown through an <img> tag (GitHub's README renderer).
Fonts are embedded as base64 woff2 because <img> SVGs cannot load web fonts.

Outputs to cards/:
  hero.svg, build.svg, brand.svg, learn.svg, city.svg, repo_<n>.svg
and regenerates README.md.

Set STATIC=1 to render every card in its final state (for screenshots).
"""
import base64
import json
import os
import subprocess
from collections import OrderedDict
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

BASE = Path(__file__).resolve().parent.parent
CARDS = BASE / "cards"
CARDS.mkdir(exist_ok=True)
STATIC = os.getenv("STATIC") == "1"

# Palette: paper, ink, three accents
PAPER, INK, MUTED = "#161b22", "#e6edf3", "#8b949e"
BLUE, RED, YELLOW = "#58a6ff", "#ff7b72", "#e3b341"
LINE = "#30363d"

NAME = "Chandan Chaudhary"
TAGLINE = "Python developer · AI & data engineering enthusiast"
LINKS = {
    "build": "https://github.com/chandan0069",
    "brand": "https://www.linkedin.com/in/chandanchaudhary1413",
    "learn": "https://chandanchaudhary.netlify.app",
}

FONTS = {
    "Instrument Serif": "https://fonts.gstatic.com/s/instrumentserif/v5/jizBRFtNs2ka5fXjeivQ4LroWlx-6zUTjnTLgNs.woff2",
    "Geist": "https://fonts.gstatic.com/s/geist/v5/gyBhhwUxId8gMGYQMKR3pzfaWI_RnOMImpna6VEdtaiL.woff2",
}
SERIF = "'Instrument Serif', Georgia, serif"
SANS = "'Geist', 'Helvetica Neue', Arial, sans-serif"


# ---------------------------------------------------------------- helpers
def font_css() -> str:
    cache = BASE / ".font_cache"
    cache.mkdir(exist_ok=True)
    out = []
    for name, url in FONTS.items():
        path = cache / f"{name}.woff2"
        if not path.exists():
            subprocess.run(["curl", "-fsSL", "-o", str(path), url], check=True)
        data = path.read_bytes()
        if data[:4] != b"wOF2":  # not a real font -> fall back to system fonts
            path.unlink()
            continue
        b64 = base64.b64encode(data).decode()
        out.append(f"@font-face{{font-family:'{name}';src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
    return "".join(out)


_FONT_CSS = None


def svg(w, h, body, extra_css="", defs="", bg=None, stroke=None):
    """Wrap a card: paper background, shared fonts + keyframes."""
    global _FONT_CSS
    if _FONT_CSS is None:
        _FONT_CSS = font_css()
    anim = "" if STATIC else """
      .rise{animation:rise .8s cubic-bezier(.2,.8,.2,1) backwards}
      .pop{animation:pop .7s cubic-bezier(.3,1.6,.5,1) backwards;transform-box:fill-box;transform-origin:center}
      .grow{animation:grow .9s cubic-bezier(.2,.8,.2,1) backwards;transform-box:fill-box;transform-origin:bottom}
      .fade{animation:fade .8s ease backwards}
      @keyframes rise{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
      @keyframes pop{from{opacity:0;transform:scale(.4) rotate(-6deg)}to{opacity:1;transform:none}}
      @keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
      @keyframes fade{from{opacity:0}to{opacity:1}}
      @media (prefers-reduced-motion:reduce){.rise,.pop,.grow,.fade{animation:none}}
    """
    return (
        f"<?xml version='1.0' encoding='UTF-8'?>\n"
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>"
        f"<defs>{defs}</defs>"
        f"<style>{_FONT_CSS}"
        f".serif{{font-family:{SERIF}}} .sans{{font-family:{SANS}}}"
        f"{anim}{extra_css}</style>"
        f"<rect x='.5' y='.5' width='{w-1}' height='{h-1}' rx='16' fill='{bg or PAPER}' stroke='{stroke or LINE}'/>"
        f"{body}</svg>"
    )


def d(t):  # animation-delay style
    return "" if STATIC else f"style='animation-delay:{t:.2f}s'"


def write(name, content):
    (CARDS / name).write_text(content)


def data_uri(path: Path) -> str:
    mime = "image/png" if path.suffix == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def load():
    p = BASE / "data" / "contributions.json"
    return json.loads(p.read_text()) if p.exists() else {}


def count_up(x, y, final, size, color, t0, steps=14, dt=0.05):
    """CSS can't change text, so stack SMIL-toggled copies (count-up effect)."""
    attrs = f"x='{x}' y='{y}' font-size='{size}' fill='{color}' class='serif'"
    if STATIC or final < 2:
        return f"<text {attrs}>{final}</text>"
    parts = []
    for i in range(steps):
        v = round(final * (i + 1) / steps) if i < steps - 1 else final
        begin = t0 + i * dt
        end = "" if i == steps - 1 else f"<set attributeName='opacity' to='0' begin='{begin + dt:.2f}s' fill='freeze'/>"
        parts.append(
            f"<text {attrs} opacity='0'>{v}"
            f"<set attributeName='opacity' to='1' begin='{begin:.2f}s' fill='freeze'/>{end}</text>")
    return "".join(parts)


# ------------------------------------------------------------------- hero
def render_hero():
    w, h = 800, 280
    H_BG, H_INK, H_MUTED, H_BLUE, H_LINE = "#f2f2ef", "#14141a", "#6b6b76", "#2f5bea", "#d9d9d4"
    first, last = NAME.split(" ", 1)
    shine = ("" if STATIC else
             "<animateTransform attributeName='gradientTransform' type='translate' "
             "from='-700 0' to='700 0' dur='3.5s' begin='1.6s' repeatCount='indefinite'/>")
    defs = (f"<linearGradient id='shine' gradientUnits='userSpaceOnUse' x1='0' y1='0' x2='700' y2='0'>"
            f"<stop offset='0' stop-color='{H_INK}'/><stop offset='.42' stop-color='{H_INK}'/>"
            f"<stop offset='.5' stop-color='{H_BLUE}'/><stop offset='.58' stop-color='{H_INK}'/>"
            f"<stop offset='1' stop-color='{H_INK}'/>{shine}</linearGradient>")
    body = [
        f"<text x='40' y='52' font-size='13' class='sans rise' fill='{H_MUTED}' letter-spacing='3' {d(0.1)}>HELLO, I'M</text>",
        f"<text x='40' y='128' font-size='84' class='serif rise' fill='{H_INK}' {d(0.25)}>{escape(first)}</text>",
        f"<text x='40' y='208' font-size='84' class='serif rise' fill='{H_INK if STATIC else 'url(#shine)'}' {d(0.45)}>{escape(last)}</text>",
        f"<text x='42' y='248' font-size='17' class='sans fade' fill='{H_MUTED}' {d(0.9)}>{escape(TAGLINE)}</text>",
        f"<rect x='40' y='20' width='56' height='4' rx='2' fill='{H_BLUE}' class='fade' {d(0.2)}/>",
    ]
    # Sketch portrait (data/portrait_sketch.png, light strokes on transparent), revealed top-to-bottom
    art = BASE / "data" / "portrait_sketch.png"
    if art.exists():
        px, py, pw, ph = 515, 15, 255, 255
        reveal = (f"<animate attributeName='height' from='0' to='{ph}' dur='2.2s' begin='0.4s' fill='freeze'/>"
                  if not STATIC else "")
        defs += (f"<clipPath id='reveal'><rect x='{px}' y='{py}' width='{pw}' "
                 f"height='{ph if STATIC else 0}'>{reveal}</rect></clipPath>")
        body.append(f"<image href='{data_uri(art)}' x='{px}' y='{py}' width='{pw}' height='{ph}' "
                    f"preserveAspectRatio='xMidYMid meet' clip-path='url(#reveal)'/>")
    write("hero.svg", svg(w, h, "".join(body), defs=defs, bg=H_BG, stroke=H_LINE))


# ------------------------------------------------------------------ tiles
def tile(name, label, color, big, caption, delay, counter=None):
    w, h = 260, 170
    ring = ("" if STATIC else
            f"<circle cx='0' cy='0' r='10' fill='none' stroke='{color}' stroke-width='2' opacity='0'>"
            f"<animate attributeName='r' from='10' to='120' dur='1.4s' begin='{delay + .5:.2f}s' fill='freeze'/>"
            f"<animate attributeName='opacity' from='.7' to='0' dur='1.4s' begin='{delay + .5:.2f}s' fill='freeze'/></circle>")
    value = (count_up(24, 106, counter, 64, INK, delay + 0.4) if counter is not None else
             f"<text x='24' y='104' font-size='46' class='serif' fill='{INK}'>{escape(big)}</text>")
    body = (
        f"<g class='pop' {d(delay)}>"
        f"<rect x='0' y='0' width='{w}' height='8' fill='{color}' clip-path='url(#top)'/>"
        f"{ring}"
        f"<text x='24' y='42' font-size='12' class='sans' fill='{color}' letter-spacing='3'>{label}</text>"
        f"{value}"
        f"<text x='24' y='138' font-size='14' class='sans' fill='{MUTED}'>{escape(caption)}</text>"
        f"<text x='{w-24}' y='146' font-size='24' class='sans' fill='{INK}' text-anchor='end'>↗</text>"
        f"</g>")
    defs = f"<clipPath id='top'><rect x='0' y='0' width='{w}' height='{h}' rx='16'/></clipPath>"
    write(f"{name}.svg", svg(w, h, body, defs=defs))


def render_tiles(data):
    repos = data.get("public_repos", 0)
    tile("build", "BUILD", BLUE, "", "public repositories on GitHub", 0.9, counter=repos or None)
    tile("brand", "BRAND", RED, "LinkedIn", "let's connect", 1.1)
    tile("learn", "LEARN", YELLOW, "Portfolio", "projects & writing", 1.3)


# ------------------------------------------------------------------- city
GREENS = ["#0f5a2a", "#13a247", "#27e05a", "#7dff94"]  # low -> high contribution count
CITY_BG, TRAY, EMPTY_TILE = "#080c0a", "#1b2a22", "#17201b"


def shade(hex_, f):
    r, g, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)))


def pts(*p):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in p)


def render_city(data):
    """GitHub-style contribution grid whose flat heatmap tiles rise into glowing 3D bars."""
    days = data.get("days", [])
    w, h = 800, 380
    peak = max([dd["count"] for dd in days] + [1])
    start = (date.fromisoformat(days[0]["date"]).weekday() + 1) % 7 if days else 0  # weeks start on Sunday
    ncols = (len(days) + start + 6) // 7
    cw, rh, maxh = 12.6, 22.0, 78.0
    gx0, gy0 = w / 2, 160.0

    cells, month_cols = [], {}
    for i, dd in enumerate(days):
        col, row = divmod(i + start, 7)
        cells.append((row, col, dd))
        month_cols.setdefault(dd["date"][:7], col)
    cells.sort(key=lambda c: (c[0], c[1]))  # far row -> near row (painter's order)

    body = [f"<rect x='16' y='84' width='{w-32}' height='{h-100}' rx='18' fill='none' stroke='{TRAY}' stroke-width='1.5'/>"]
    for lbl, r in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        sc = 0.94 + 0.06 * r / 6
        body.append(f"<text x='{gx0 - (ncols/2) * cw * sc - 12:.1f}' y='{gy0 + r * rh + 6:.1f}' font-size='11' class='sans' "
                    f"fill='{MUTED}' text-anchor='end'>{lbl}</text>")
    for m, col in month_cols.items():
        if col > ncols - 3 or col == 0 and m != list(month_cols)[0]:
            continue
        body.append(f"<text x='{gx0 + (col - ncols/2 + .5) * cw * .94:.1f}' y='{gy0 - 52:.1f}' font-size='12' class='sans' "
                    f"fill='{MUTED}' text-anchor='middle'>{date(int(m[:4]), int(m[5:]), 1).strftime('%b')}</text>")

    for row, col, dd in cells:
        cnt = dd["count"]
        sc = 0.94 + 0.06 * row / 6
        cx = gx0 + (col - ncols / 2 + .5) * cw * sc
        yb = gy0 + row * rh + rh / 2           # front-bottom edge of the tile
        bw = cw * sc * 0.76
        xl, xr = cx - bw / 2, cx + bw / 2
        ox, dd_ = bw * 0.28, rh * 0.36          # oblique depth offset
        if cnt == 0:
            body.append(f"<polygon points='{pts((xl, yb), (xr, yb), (xr + ox, yb - dd_), (xl + ox, yb - dd_))}' fill='{EMPTY_TILE}'/>")
            continue
        lvl = min(3, int(cnt / peak * 4 - 1e-9))
        c = GREENS[lvl]
        bh = max(6.0, cnt / peak * maxh)
        top = lambda e: pts((xl, yb - e), (xr, yb - e), (xr + ox, yb - e - dd_), (xl + ox, yb - e - dd_))
        front = lambda e: pts((xl, yb - e), (xr, yb - e), (xr, yb), (xl, yb))
        side = lambda e: pts((xr, yb - e), (xr + ox, yb - e - dd_), (xr + ox, yb - dd_), (xr, yb))
        if STATIC:
            faces = (top(bh), front(bh), side(bh))
            anim = lambda to, frm: ""
        else:
            faces = (top(0), front(0), side(0))
            begin = 2.0 + col * 0.04 + row * 0.015
            anim = lambda to, frm: (f"<animate attributeName='points' from='{frm}' to='{to}' dur='1s' begin='{begin:.2f}s' "
                                    f"fill='freeze' calcMode='spline' keyTimes='0;1' keySplines='.2 .9 .3 1.15'/>")
        body.append(f"<polygon points='{faces[2]}' fill='{shade(c, .55)}'>{anim(side(bh), side(0))}</polygon>")
        body.append(f"<polygon points='{faces[1]}' fill='{shade(c, .85)}'>{anim(front(bh), front(0))}</polygon>")
        body.append(f"<polygon points='{faces[0]}' fill='{shade(c, 1.12)}'>{anim(top(bh), top(0))}</polygon>")

    # streak stats
    streak = cur = 0
    for dd in days:
        cur = cur + 1 if dd["count"] > 0 else 0
    for i, dd in enumerate(reversed(days)):
        if dd["count"] > 0:
            streak += 1
        elif i > 0:
            break
    active = sum(1 for dd in days if dd["count"])

    total = data.get("total_contributions", 0)
    head = (f"<text x='32' y='52' font-size='30' class='sans fade' fill='{INK}'><tspan fill='{GREENS[2]}'>{total}</tspan> contributions in the last year</text>")
    foot_y = h - 30
    foot = (f"<text x='36' y='{foot_y}' font-size='12' class='sans' fill='{MUTED}'>Refreshed daily · {streak}-day streak · {active} active days</text>"
            f"<text x='{w-200}' y='{foot_y}' font-size='12' class='sans' fill='{MUTED}' text-anchor='end'>Less</text>")
    for i, col in enumerate([EMPTY_TILE] + GREENS):
        foot += f"<rect x='{w-190 + i * 20}' y='{foot_y - 11}' width='14' height='14' rx='3' fill='{col}'/>"
    foot += f"<text x='{w-84}' y='{foot_y}' font-size='12' class='sans' fill='{MUTED}'>More</text>"
    write("city.svg", svg(w, h, head + "".join(body) + foot, bg=CITY_BG))


# ------------------------------------------------------------- repo cards
def render_repos(data):
    for old in CARDS.glob("repo_*.svg"):
        old.unlink()
    accents = [BLUE, RED, YELLOW, INK]
    for i, r in enumerate(data.get("repos", [])[:4]):
        w, h = 396, 150
        name = r["name"]
        if len(name) <= 24:
            lines = [name]
        else:
            cut = name.rfind("-", 0, 24)
            cut = cut + 1 if cut > 8 else 24
            lines = [name[:cut], name[cut:]]
        c = accents[i % 4]
        t = 1.5 + i * 0.15
        body = [f"<rect x='0' y='0' width='8' height='{h}' fill='{c}' clip-path='url(#l)' class='fade' {d(t)}/>"]
        for j, ln in enumerate(lines[:2]):
            body.append(f"<text x='28' y='{52 + j*30}' font-size='26' class='serif rise' fill='{INK}' {d(t)}>{escape(ln)}</text>")
        desc = r.get("description") or ""
        if desc:
            body.append(f"<text x='28' y='108' font-size='13' class='sans fade' fill='{MUTED}' {d(t + .2)}>{escape(desc[:46] + ('…' if len(desc) > 46 else ''))}</text>")
        meta = " · ".join(x for x in [r.get("language"), f"★ {r.get('stars', 0)}"] if x)
        body.append(f"<text x='28' y='{h-22}' font-size='13' class='sans fade' fill='{MUTED}' {d(t + .2)}>{escape(meta)}</text>")
        body.append(f"<text x='{w-26}' y='{h-20}' font-size='22' class='sans' fill='{INK}' text-anchor='end'>↗</text>")
        defs = f"<clipPath id='l'><rect x='0' y='0' width='{w}' height='{h}' rx='16'/></clipPath>"
        write(f"repo_{i+1}.svg", svg(w, h, "".join(body), defs=defs))


def render_readme(data):
    """README.md is generated so repo links stay in sync with pinned repos."""
    repo_imgs = [
        f'<a href="{r["url"]}"><img src="./cards/repo_{i+1}.svg" width="49%" alt="{escape(r["name"])}"/></a>'
        for i, r in enumerate(data.get("repos", [])[:4])]
    readme = f"""<div align="center">

<img src="./cards/hero.svg" width="100%" alt="{NAME}"/>

<a href="{LINKS['build']}"><img src="./cards/build.svg" width="32.5%" alt="Build"/></a>
<a href="{LINKS['brand']}"><img src="./cards/brand.svg" width="32.5%" alt="Brand"/></a>
<a href="{LINKS['learn']}"><img src="./cards/learn.svg" width="32.5%" alt="Learn"/></a>

<img src="./cards/city.svg" width="100%" alt="Contribution city"/>

{chr(10).join(repo_imgs)}

</div>
"""
    (BASE / "README.md").write_text(readme)


def main():
    data = load()
    for old in CARDS.glob("*.svg"):
        old.unlink()
    render_hero()
    render_tiles(data)
    render_city(data)
    render_repos(data)
    render_readme(data)
    print(f"✅ Rendered {len(list(CARDS.glob('*.svg')))} cards")


if __name__ == "__main__":
    main()
