#!/usr/bin/env python3
"""Render animated SVG cards for the GitHub profile README.

Generates a stack of SVG files in the ``cards/`` directory:

1. ``hero.svg`` – name, tagline, optional portrait.
2. ``tiles.svg`` – three linked icons (GitHub, LinkedIn, website).
3. ``contributions.svg`` – monthly bar‑chart + streak/active‑days/busiest‑day.
4. ``repo_<name>.svg`` – one card per featured repo (``featured_repos.json``).
5. ``heatmap.svg`` – recoloured contribution heat‑map.

All SVGs embed the required fonts (Patrick Hand & Montserrat Alternates) as
base64‑encoded WOFF files generated with ``pyftsubset``.
Animations are CSS keyframe fades staggered by ``delay`` seconds.  They are
disabled when the user prefers reduced motion and can be frozen for screenshots
by setting the environment variable ``STATIC=1``.
"""

import os
import json
import base64
import subprocess
from pathlib import Path
from textwrap import dedent
from collections import defaultdict
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Configuration – colours and fonts (mirroring the website)
# ---------------------------------------------------------------------------
PRIMARY_COLOR = "#000B49"
BG_COLOR = "#fcfcfc"
FONT_FAMILIES = {
    "Patrick Hand": "https://fonts.gstatic.com/s/patrickhand/v22/LDI1apSCOBkofAIDsoO3H8ySgA.ttf",
    "Montserrat Alternates": "https://fonts.gstatic.com/s/montalternates/v12/7Au5p_0qiz-wgOZ6Qm4fJvZcLxVn2eU.ttf",
}

BASE_DIR = Path(__file__).resolve().parent.parent
CARDS_DIR = BASE_DIR / "cards"
CARDS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Helper: download a font, subset it and return a data‑URI string
# ---------------------------------------------------------------------------
def embed_font(name: str, url: str) -> str:
    cache_dir = BASE_DIR / ".font_cache"
    cache_dir.mkdir(exist_ok=True)
    ttf_path = cache_dir / f"{name}.ttf"
    woff_path = cache_dir / f"{name}.woff"
    if not ttf_path.exists():
        subprocess.run(["curl", "-sSL", url, "-o", str(ttf_path)], check=True)
    subset_chars = "".join(chr(c) for c in range(32, 127))
    subprocess.run([
        "pyftsubset",
        str(ttf_path),
        f"--output-file={woff_path}",
        f"--text={subset_chars}",
        "--flavor=woff",
        "--quiet",
    ], check=True)
    b64 = base64.b64encode(woff_path.read_bytes()).decode()
    return f"data:font/woff;charset=utf-8;base64,{b64}"

# ---------------------------------------------------------------------------
# CSS builder – includes staggered animation and reduced‑motion handling
# ---------------------------------------------------------------------------
def build_style(card_index: int) -> str:
    delay = card_index * 0.6
    static = os.getenv("STATIC") == "1"
    animation = "none" if static else "fadeIn 0.7s ease forwards"
    delay_css = "0s" if static else f"{delay}s"
    return dedent(f"""
        <style>
        @font-face {{
            font-family: 'Patrick Hand';
            src: url('{embed_font('Patrick Hand', FONT_FAMILIES['Patrick Hand'])}');
        }}
        @font-face {{
            font-family: 'Montserrat Alternates';
            src: url('{embed_font('Montserrat Alternates', FONT_FAMILIES['Montserrat Alternates'])}');
        }}
        .card {{
            font-family: 'Patrick Hand', cursive;
            fill: {PRIMARY_COLOR};
            opacity: 0;
            animation: {animation};
            animation-delay: {delay_css};
        }}
        @keyframes fadeIn {{
            to {{ opacity: 1; }}
        }}
        @media (prefers-reduced-motion: reduce) {{
            .card {{ animation: none; opacity: 1; }}
        }}
        </style>
    """)

# ---------------------------------------------------------------------------
# 1. Hero card
# ---------------------------------------------------------------------------
def render_hero():
    name = "Chandan Chaudhary"
    tagline = "Python Developer | AI & Data Engineering Enthusiast"
    portrait = BASE_DIR / "source-photo.jpg"
    portrait_href = portrait.name if portrait.exists() else ""
    svg = f"""<?xml version='1.0' encoding='UTF-8'?>
    <svg xmlns='http://www.w3.org/2000/svg' width='800' height='250'>
    {build_style(0)}
    <g class='card'>
        <text x='20' y='60' font-size='48'>{name}</text>
        <text x='20' y='110' font-size='24'>{tagline}</text>
    </g>
    """
    if portrait_href:
        svg += f"<image href='{portrait_href}' x='560' y='20' width='200' height='200'/>"
    svg += "</svg>"
    (CARDS_DIR / "hero.svg").write_text(svg)

# ---------------------------------------------------------------------------
# 2. Tiles card – three linked icons (placeholders if missing)
# ---------------------------------------------------------------------------
def render_tiles():
    links = [
        ("https://github.com/chandan0069", "github.svg"),
        ("https://www.linkedin.com/in/chandanchaudhary1413", "linkedin.svg"),
        ("https://chandanchaudhary.netlify.app", "website.svg"),
    ]
    width = 800
    tile_width = int(width * 0.325)
    spacing = (width - 3 * tile_width) // 4
    x = spacing
    parts = ["<?xml version='1.0' encoding='UTF-8'?>",
             f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='200'>",
             build_style(1),
             "<g class='card'>"]
    for url, img in links:
        img_path = BASE_DIR / img
        img_href = img_path.name if img_path.exists() else ""
        parts.append(
            f"<a href='{url}' target='_blank'>"
            f"<image href='{img_href}' x='{x}' y='20' width='{tile_width}' height='160'/>"
            "</a>")
        x += tile_width + spacing
    parts.append("</g></svg>")
    (CARDS_DIR / "tiles.svg").write_text("\n".join(parts))

# ---------------------------------------------------------------------------
# 3. Contributions chart (monthly bar chart + stats)
# ---------------------------------------------------------------------------
def render_contributions():
    data_path = BASE_DIR / "data" / "contributions.json"
    if not data_path.exists():
        return
    with data_path.open() as f:
        payload = json.load(f)
    days = {d["date"]: d["count"] for d in payload.get("days", [])}
    # Aggregate monthly totals
    monthly = defaultdict(int)
    for date, cnt in days.items():
        month = date[:7]
        monthly[month] += cnt
    months = sorted(monthly.keys())
    max_val = max(monthly.values()) if monthly else 1
    # Streak & stats
    streak = 0
    today = datetime.utcnow().date()
    day = today
    while days.get(day.isoformat(), 0) > 0:
        streak += 1
        day -= timedelta(days=1)
    active_days = sum(1 for c in days.values() if c > 0)
    busiest_day = max(days.items(), key=lambda kv: kv[1], default=(None, 0))
    # SVG
    w, h = 800, 300
    bar_width = (w - 80) // (len(months) or 1)
    svg = ["<?xml version='1.0' encoding='UTF-8'?>",
           f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}'>",
           build_style(2),
           "<g class='card'>"]
    for i, month in enumerate(months):
        val = monthly[month]
        bar_h = int((val / max_val) * 180)
        x = 40 + i * bar_width
        y = h - 60 - bar_h
        svg.append(f"<rect x='{x}' y='{y}' width='{bar_width-4}' height='{bar_h}' fill='{PRIMARY_COLOR}'/>")
        svg.append(f"<text x='{x+bar_width/2}' y='{h-40}' font-size='12' text-anchor='middle'>{month[5:]}</text>")
    stats = f"Streak: {streak} days | Active days: {active_days} | Busiest: {busiest_day[0] or ''} ({busiest_day[1]})"
    svg.append(f"<text x='40' y='20' font-size='14'>{stats}</text>")
    svg.append("</g></svg>")
    (CARDS_DIR / "contributions.svg").write_text("\n".join(svg))

# ---------------------------------------------------------------------------
# 4. Featured repo cards (optional)
# ---------------------------------------------------------------------------
def render_featured_repos():
    repos_path = BASE_DIR / "featured_repos.json"
    if not repos_path.exists():
        return
    with repos_path.open() as f:
        repos = json.load(f)
    for i, repo in enumerate(repos):
        w, h = 400, 200
        svg = ["<?xml version='1.0' encoding='UTF-8'?>",
               f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}'>",
               build_style(3 + i),
               "<g class='card'>",
               f"<a href='{repo['url']}' target='_blank'>",
               f"<text x='20' y='40' font-size='20' font-weight='bold'>{repo['name']}</text>",
               f"<text x='20' y='70' font-size='14'>{repo['description']}</text>",
               f"<text x='20' y='100' font-size='12'>⭐ {repo['stars']} • {repo['language']}</text>",
               "</a>",
               "</g></svg>"]
        filename = f"repo_{repo['name'].replace('/', '_')}.svg"
        (CARDS_DIR / filename).write_text("\n".join(svg))

# ---------------------------------------------------------------------------
# 5. Re‑colour the existing heat‑map SVG
# ---------------------------------------------------------------------------
def render_heatmap():
    src = BASE_DIR / "contrib-heatmap.svg"
    if not src.exists():
        return
    data = src.read_text()
    import re
    recoloured = re.sub(r"fill='[^']+'", f"fill='{PRIMARY_COLOR}'", data)
    (CARDS_DIR / "heatmap.svg").write_text(recoloured)

# ---------------------------------------------------------------------------
def main():
    render_hero()
    render_tiles()
    render_contributions()
    render_featured_repos()
    render_heatmap()
    print(f"✅ Rendered {len(list(CARDS_DIR.iterdir()))} SVG cards into {CARDS_DIR}")

if __name__ == "__main__":
    main()
