"""Full example: a decorated ceramic mug — the "instant noodles cup".

Run inside Blender MCP `execute_blender_code` with this repo as the working directory:

    exec(open("skills/blender/scripts/blib.py").read())
    exec(open("examples/cup.py").read())

What it demonstrates:
  * lathe()            — the conical mug body from a 2D profile (watertight, no booleans)
  * curve_tube()       — the flat D-shaped handle as a Bezier curve with a ribbon profile
  * shrinkwrap_to()    — printed artwork (words) laid onto the tapered wall automatically
  * cone_rib()         — stripes that follow the cone's generatrix
  * the critic checklist: render every side, compare with the reference, fix differences
"""
import math
import bmesh as _bmesh
from mathutils import Vector

# ---------------------------------------------------------------- materials
ceramic = mat("Ceramic", (0.93, 0.92, 0.90, 1), 0.0, 0.08)
orange = mat("OrangePrint", (0.97, 0.32, 0.03, 1), 0.0, 0.55)
red = mat("RedPrint", (0.58, 0.025, 0.03, 1), 0.0, 0.62)
white = mat("WhitePrint", (0.95, 0.95, 0.95, 1), 0.0, 0.5)

# any bold grotesque installed on your system; Liberation Sans ships with most distros
font = bpy.data.fonts.load("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf")

# ---------------------------------------------------------------- body (lathe)
PROFILE = [
    (0.0003, 0.0095), (0.020, 0.0095), (0.030, 0.0105), (0.0365, 0.0135),
    (0.0405, 0.018), (0.0435, 0.024), (0.050, 0.055), (0.0545, 0.078),
    (0.0570, 0.088), (0.0585, 0.0945), (0.0605, 0.0995), (0.0635, 0.1015), (0.0665, 0.1010),
]
cup = lathe("Cup", PROFILE, steps=128, material=ceramic, thickness=0.0028, offset=1.0)
verify_bounds("Cup")

# IMPORTANT: check the wall direction with ray probes before decorating —
# SOLIDIFY offset is easy to get backwards (see SKILL.md).
deps = bpy.context.evaluated_depsgraph_get()
hit, loc, *_ = bpy.context.scene.ray_cast(deps, (-0.2, 0, 0.06), (1, 0, 0))
print("outer surface at x =", round(loc.x, 4), "| R_prof(0.06) should be ~0.0510")


def R_prof(z):
    if z <= PROFILE[0][1]:
        return PROFILE[0][0]
    for (r0, z0), (r1, z1) in zip(PROFILE, PROFILE[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0) if z1 > z0 else 0
            return r0 + (r1 - r0) * t
    return PROFILE[-1][0]


# ---------------------------------------------------------------- handle (curve)
hp = [
    (0.052, 0, 0.083), (0.070, 0, 0.090), (0.086, 0, 0.081), (0.0925, 0, 0.0615),
    (0.0925, 0, 0.0455), (0.086, 0, 0.028), (0.070, 0, 0.0205), (0.042, 0, 0.0245),
]
curve_tube("Handle", hp, section=(0.0045, 0.0090), material=ceramic, resolution=28)


# ---------------------------------------------------------------- printed stripes
def cone_rib(name, a0, a1, z0, z1, t_out=0.0011, in_off=-0.0005, material=None, steps=3):
    """A stripe that follows the cone: its edges run along the generatrix."""
    bm = _bmesh.new()
    cols = []
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * i / steps
        ca, sa = math.cos(a), math.sin(a)
        ilo, ihi = R_prof(z0) + in_off, R_prof(z1) + in_off
        olo, ohi = ilo + t_out, ihi + t_out
        cols.append((bm.verts.new((olo*ca, olo*sa, z0)), bm.verts.new((ohi*ca, ohi*sa, z1)),
                     bm.verts.new((ilo*ca, ilo*sa, z0)), bm.verts.new((ihi*ca, ihi*sa, z1))))
    for i in range(steps):
        o0a, o1a, i0a, i1a = cols[i]
        o0b, o1b, i0b, i1b = cols[i + 1]
        bm.faces.new([o0a, o0b, o1b, o1a]); bm.faces.new([i1a, i1b, i0b, i0a])
        bm.faces.new([o1a, o1b, i1b, i1a]); bm.faces.new([i0a, i0b, o0b, o0a])
    o0a, o1a, i0a, i1a = cols[0]; bm.faces.new([i0a, i1a, o1a, o0a])
    o0a, o1a, i0a, i1a = cols[-1]; bm.faces.new([o0a, o1a, i1a, i0a])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(obj)
    solo(obj)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    if material:
        obj.data.materials.append(material)
    return obj


for band, (z0, z1) in enumerate(((0.0885, 0.0995), (0.0185, 0.0305))):
    stripes = []
    for i in range(64):
        a0 = math.radians(i * 5.625)
        stripes.append(cone_rib(f"Rib.{band}.{i}", a0, a0 + math.radians(3.2), z0, z1, material=orange, steps=2))
    solo(stripes[0])
    for o in stripes[1:]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = stripes[0]
    bpy.ops.object.join()
    bpy.context.active_object.name = f"Stripes{band}"

# thin red rings
for name, zc in (("RingTop", 0.0860), ("RingLow", 0.0330)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=R_prof(zc) + 0.0006,
                                        depth=0.0020, location=(0, 0, zc), end_fill_type='NOTHING')
    ring = bpy.context.active_object
    ring.name = name
    ring.data.materials.append(red)


# ---------------------------------------------------------------- printed words
def arc_word(word, z, size, material, center_deg=-90, gap=0.002, out=0.0005, thick=0.0007):
    """Lay a word onto the cone: distribute flat letters in a wide arc, then Shrinkwrap
    pulls every glyph onto the surface (and tilts it with the wall)."""
    R = R_prof(z) + 0.012
    objs, widths = [], []
    for ch in word:
        bpy.ops.object.text_add()
        t = bpy.context.active_object
        t.data.body = ch
        t.data.size = size
        t.data.extrude = 0.0
        t.data.font = font
        t.data.align_x = 'CENTER'
        t.data.align_y = 'CENTER'
        solo(t)
        bpy.ops.object.convert(target='MESH')
        o = bpy.context.active_object
        objs.append(o)
        widths.append(o.dimensions.x)
    total = sum(widths) + gap * (len(word) - 1)
    a = math.radians(center_deg) - (total / R) / 2
    made = []
    for i in range(len(word)):
        w = widths[i]
        a += (w / 2) / R
        o = objs[i]
        o.location = (R * math.cos(a), R * math.sin(a), z)
        o.rotation_euler = (math.pi / 2, 0, a + math.pi / 2)
        solo(o)
        bpy.ops.object.transform_apply(rotation=True, location=True)
        made.append(o)
        a += (w / 2) / R + gap / R
    solo(made[0])
    for o in made[1:]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = made[0]
    bpy.ops.object.join()
    word_obj = bpy.context.active_object
    word_obj.name = f"Word.{word}"
    shrinkwrap_to(word_obj, cup, offset=out, method='NEAREST_SURFACEPOINT')
    ink = word_obj.modifiers.new("Ink", 'SOLIDIFY')
    ink.thickness = thick
    ink.offset = 1.0
    solo(word_obj)
    bpy.ops.object.modifier_apply(modifier="Ink")
    word_obj.data.materials.append(material)
    return word_obj


arc_word("INSTANT", 0.0700, 0.0180, red, gap=0.0022)
arc_word("NOODLES", 0.0490, 0.0190, red, gap=0.0020)

# the red "CUP" tab
cone_rib("CupPanel", math.radians(-115), math.radians(-65), 0.0195, 0.0340,
         t_out=0.0015, in_off=-0.0005, material=red, steps=24)
arc_word("CUP", 0.0268, 0.0110, white, gap=0.0024, out=0.0018, thick=0.0008)

# ---------------------------------------------------------------- present & export
studio(target=(0, 0, 0.055), scale=0.25, cam_pos=(-0.10, -0.27, 0.155), lens=50)
s = bpy.context.scene
s.cycles.samples = 64
s.render.filepath = "/tmp/cup.png"
bpy.ops.render.render(write_still=True)

export_glb("cup.glb")
audit_all()
print("CUP-DONE")
