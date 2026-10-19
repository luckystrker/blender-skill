#!/usr/bin/env python3
"""check_glb.py — качественные проверки .glb для evals.
Запуск: blender -b --python check_glb.py -- /path/model.glb
Печатает одну строку JSON: GLB-CHECK: {...}
"""
import bpy
import bmesh
import json
import os
import struct
import sys

path = sys.argv[sys.argv.index("--") + 1]
out = {"path": path, "exists": os.path.exists(path), "size": os.path.getsize(path) if os.path.exists(path) else 0}

if not out["exists"]:
    print("GLB-CHECK:", json.dumps(out))
    raise SystemExit(0)

with open(path, "rb") as f:
    out["magic"] = f.read(4).decode("latin-1")

bpy.ops.wm.read_homefile(use_empty=True)
try:
    bpy.ops.import_scene.gltf(filepath=path)
except Exception as e:
    out["import_error"] = str(e)
    print("GLB-CHECK:", json.dumps(out))
    raise SystemExit(0)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
out["mesh_count"] = len(meshes)
out["names"] = sorted(o.name for o in meshes)[:15]

all_vs = []
non_manifold = 0
edges_total = 0
tris = 0
for o in meshes:
    for v in o.data.vertices:
        all_vs.append(o.matrix_world @ v.co)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for e in bm.edges:
        edges_total += 1
        if not e.is_manifold:
            non_manifold += 1
    bm.free()
    o.data.calc_loop_triangles()
    tris += len(o.data.loop_triangles)

if all_vs:
    xs = [v.x for v in all_vs]; ys = [v.y for v in all_vs]; zs = [v.z for v in all_vs]
    out["bbox"] = {
        "x": round(max(xs) - min(xs), 4),
        "y": round(max(ys) - min(ys), 4),
        "z": round(max(zs) - min(zs), 4),
    }
    out["max_dim"] = round(max(out["bbox"].values()), 4)
out["triangles"] = tris
out["edges"] = edges_total
out["non_manifold_edges"] = non_manifold
out["materials"] = sorted({m.name for o in meshes for m in o.data.materials if m})
out["has_floor"] = any(o.name.lower().startswith("floor") for o in meshes)
print("GLB-CHECK:", json.dumps(out))
