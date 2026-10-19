"""Minimal lathe example: a smooth hollow vase in ~30 lines.

Run inside Blender MCP `execute_blender_code` with this repo as the working directory:

    exec(open("tools/blib.py").read())
    exec(open("examples/vase.py").read())

The trick: describe the OUTER surface as a list of (radius, height) points,
spin it 360° (Screw modifier) and let Solidify add the wall thickness.
No booleans, watertight from the lathe.
"""
import math

# (radius, height) from the bottom centre up to the rim
PROFILE = [
    (0.0003, 0.000), (0.030, 0.000), (0.038, 0.003), (0.044, 0.010),
    (0.050, 0.030), (0.056, 0.070), (0.058, 0.100), (0.054, 0.140),
    (0.045, 0.170), (0.040, 0.182), (0.0405, 0.186),
]

clay = mat("VaseClay", (0.85, 0.87, 0.90, 1), 0.0, 0.22)
vase = lathe("Vase", PROFILE, steps=128, material=clay, thickness=0.004)
verify_bounds("Vase")

studio(target=(0, 0, 0.09), scale=0.35, cam_pos=(0.30, -0.28, 0.22), lens=50)
s = bpy.context.scene
s.cycles.samples = 64
s.render.filepath = "/tmp/vase.png"
bpy.ops.render.render(write_still=True)
audit_all()
print("VASE-DONE")
