#!/usr/bin/env python3
"""check_render.py — проверка рендера на наличие цветного декора.
Запуск: blender -b --python check_render.py -- /path/render.png
Печатает: RENDER-CHECK: {"red_pct": ..., "orange_pct": ..., ...}

Идея: у чашки INSTANT NOODLES на белой керамике красные надписи и оранжевый орнамент.
Считаем долю пикселей красного/оранжевого оттенка (сэмплирование, каждый ~97-й пиксель).
"""
import bpy
import json
import os
import sys

path = sys.argv[sys.argv.index("--") + 1]
out = {"path": path, "exists": os.path.exists(path)}
if not out["exists"]:
    print("RENDER-CHECK:", json.dumps(out))
    raise SystemExit(0)

img = bpy.data.images.load(path)
w, h = img.size
px = list(img.pixels)
step = 4 * 97
red = orange = samples = 0
for i in range(0, len(px) - 3, step):
    r, g, b = px[i], px[i + 1], px[i + 2]
    samples += 1
    if r > 0.42 and g < 0.33 and b < 0.33:
        red += 1
    elif r > 0.55 and 0.28 < g < 0.62 and b < 0.30:
        orange += 1

out.update({
    "size": [w, h],
    "samples": samples,
    "red_pct": round(100.0 * red / max(samples, 1), 3),
    "orange_pct": round(100.0 * orange / max(samples, 1), 3),
})
print("RENDER-CHECK:", json.dumps(out))
