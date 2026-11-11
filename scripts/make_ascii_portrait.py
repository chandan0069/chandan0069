#!/usr/bin/env python3
"""One-off helper: turn source-photo.jpg into an ASCII sketch (data/portrait_ascii.txt).

Needs Pillow + numpy (not required in CI - the output file is committed).
    pip install pillow numpy && python scripts/make_ascii_portrait.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

BASE = Path(__file__).resolve().parent.parent
COLS, ROWS = 70, 50          # characters are ~2x taller than wide
RAMP = " .:-=+*#%@"           # light on dark: denser = stronger feature

img = Image.open(BASE / "source-photo.jpg").convert("L")
w, h = img.size
img = img.crop((int(w * .08), 0, int(w * .92), int(h * .84)))     # head + shoulders (square crop)
img = img.resize((COLS * 6, ROWS * 6), Image.LANCZOS)               # cell aspect ~0.72 -> square on screen

a = np.asarray(img, dtype=float) / 255
# remove the photo's vignette by dividing out a heavy blur (local normalisation)
wall = np.asarray(img.filter(ImageFilter.GaussianBlur(70)), dtype=float) / 255 + 1e-3
n = np.clip(a / wall, 0, 2) / 2                                      # 0.5 == same as surroundings
fine = np.asarray(img.filter(ImageFilter.GaussianBlur(1.5)), dtype=float) / 255
soft = np.asarray(img.filter(ImageFilter.GaussianBlur(6)), dtype=float) / 255
edges = np.abs(fine - soft) / wall                                   # outlines
dark = np.clip((0.5 - n) * 2.0, 0, 1)                                # hair, beard, shirt
strength = np.clip(edges * 9 + dark * 0.7, 0, 1)
strength = np.asarray(Image.fromarray((strength * 255).astype("uint8")).resize((COLS, ROWS), Image.BOX), dtype=float) / 255
strength = np.clip((strength - 0.05) * 1.5, 0, 1)

lines = ["".join(RAMP[int(v * (len(RAMP) - 1))] for v in row).rstrip() for row in strength]
(BASE / "data" / "portrait_ascii.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
