#!/usr/bin/env python3
"""Render animated SVG cards for the GitHub profile README.

Everything is drawn with plain SVG + CSS keyframes + SMIL, which keep working
when the SVG is shown through an <img> tag (GitHub's README renderer).
Fonts are embedded as base64 woff2 because <img> SVGs cannot load web fonts.

Outputs to cards/:
  hero.svg, build.svg, brand.svg, learn.svg, activity.svg, repo_<n>.svg
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


def svg(w, h, body, extra_css="", defs=""):
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
        f"<rect x='.5' y='.5' width='{w-1}' height='{h-1}' rx='16' fill='{PAPER}' stroke='{LINE}'/>"
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
    first, last = NAME.split(" ", 1)
    shine = ("" if STATIC else
             "<animateTransform attributeName='gradientTransform' type='translate' "
             "from='-700 0' to='700 0' dur='3.5s' begin='1.6s' repeatCount='indefinite'/>")
    defs = (f"<linearGradient id='shine' gradientUnits='userSpaceOnUse' x1='0' y1='0' x2='700' y2='0'>"
            f"<stop offset='0' stop-color='{INK}'/><stop offset='.42' stop-color='{INK}'/>"
            f"<stop offset='.5' stop-color='{BLUE}'/><stop offset='.58' stop-color='{INK}'/>"
            f"<stop offset='1' stop-color='{INK}'/>{shine}</linearGradient>")
    body = [
        f"<text x='40' y='52' font-size='13' class='sans rise' fill='{MUTED}' letter-spacing='3' {d(0.1)}>HELLO, I'M</text>",
        f"<text x='40' y='128' font-size='84' class='serif rise' fill='{INK}' {d(0.25)}>{escape(first)}</text>",
        f"<text x='40' y='208' font-size='84' class='serif rise' fill='{INK if STATIC else 'url(#shine)'}' {d(0.45)}>{escape(last)}</text>",
        f"<text x='42' y='248' font-size='17' class='sans fade' fill='{MUTED}' {d(0.9)}>{escape(TAGLINE)}</text>",
        f"<rect x='40' y='20' width='56' height='4' rx='2' fill='{BLUE}' class='fade' {d(0.2)}/>",
    ]
    # ASCII sketch portrait (generated by scripts/make_ascii_portrait.py), one row fades in after another
    art = BASE / "data" / "portrait_ascii.txt"
    if art.exists():
        rows = art.read_text().split("\n")
        rows = [r for r in rows]
        cols = max(len(r) for r in rows) or 1
        pw, ph, px, py = 250, 250, 520, 15
        lh = ph / max(len(rows), 1)
        body.append(f"<g font-family=\"Menlo,Consolas,'DejaVu Sans Mono','Courier New',monospace\" font-size='{lh * 1.0:.2f}' fill='{INK}' xml:space='preserve'>")
        for i, r in enumerate(rows):
            if not r.strip():
                continue
            r = r.ljust(cols)
            body.append(f"<text x='{px}' y='{py + (i + 1) * lh:.2f}' textLength='{pw}' lengthAdjust='spacingAndGlyphs' "
                        f"class='fade' {d(0.4 + i * 0.018)} xml:space='preserve'>{escape(r)}</text>")
        body.append("</g>")
    write("hero.svg", svg(w, h, "".join(body), defs=defs))


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


# --------------------------------------------------------------- activity
def render_activity(data):
    days = data.get("days", [])
    w, h = 800, 320
    monthly = OrderedDict()
    for dd in days:
        monthly[dd["date"][:7]] = monthly.get(dd["date"][:7], 0) + dd["count"]
    months = list(monthly)[-12:]
    vals = [monthly[m] for m in months]
    mx = max(vals + [1])
    best = vals.index(max(vals)) if vals else -1

    streak = cur = longest = 0
    for dd in days:
        cur = cur + 1 if dd["count"] > 0 else 0
        longest = max(longest, cur)
    for i, dd in enumerate(reversed(days)):  # current streak (today may still be empty)
        if dd["count"] > 0:
            streak += 1
        elif i > 0:
            break
    active = sum(1 for dd in days if dd["count"])
    busiest = max(days, key=lambda x: x["count"], default={"date": "", "count": 0})

    body = [f"<text x='40' y='46' font-size='13' class='sans' fill='{MUTED}' letter-spacing='3'>ACTIVITY · LAST 12 MONTHS</text>",
            f"<text x='40' y='90' font-size='38' class='serif' fill='{INK}'>{data.get('total_contributions', 0)} contributions</text>"]
    base_y, chart_h = 235, 95
    slot = (w - 80) / max(len(months), 1)
    bw = slot * 0.62
    for i, (m, v) in enumerate(zip(months, vals)):
        bh = max(3, v / mx * chart_h)
        x = 40 + i * slot + (slot - bw) / 2
        color = BLUE if i == best else INK
        op = 1 if i == best else .55
        body.append(f"<rect x='{x:.1f}' y='{base_y - bh:.1f}' width='{bw:.1f}' height='{bh:.1f}' rx='4' "
                    f"fill='{color}' opacity='{op}' class='grow' {d(0.3 + i * 0.06)}/>")
        label = date(int(m[:4]), int(m[5:]), 1).strftime("%b")
        body.append(f"<text x='{x + bw/2:.1f}' y='{base_y + 17}' font-size='11' class='sans' fill='{MUTED}' text-anchor='middle'>{label}</text>")
        if i == best:
            body.append(f"<text x='{x + bw/2:.1f}' y='{base_y - bh - 8:.1f}' font-size='16' class='serif pop' fill='{BLUE}' "
                        f"text-anchor='middle' {d(1.2)}>{v}</text>")
    stats = [("current streak", f"{streak} days"), ("active days", str(active)),
             ("longest streak", f"{longest} days"),
             ("busiest day", f"{busiest['count']} on {busiest['date'][5:]}" if busiest["date"] else "-")]
    sx = 40
    for k, v in stats:
        body.append(f"<g class='fade' {d(1.0)}><text x='{sx}' y='284' font-size='11' class='sans' fill='{MUTED}' letter-spacing='1'>{k.upper()}</text>"
                    f"<text x='{sx}' y='306' font-size='20' class='serif' fill='{INK}'>{escape(v)}</text></g>")
        sx += 190
    write("activity.svg", svg(w, h, "".join(body)))


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

<img src="./cards/activity.svg" width="100%" alt="Contribution activity"/>

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
    render_activity(data)
    render_repos(data)
    render_readme(data)
    print(f"✅ Rendered {len(list(CARDS.glob('*.svg')))} cards")


if __name__ == "__main__":
    main()
