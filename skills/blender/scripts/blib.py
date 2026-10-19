"""blib.py — общая библиотека 3D-паттернов для Blender-задач (загружается через exec).

Загрузка в execute_blender_code:
    exec(open("/home/piagent/pi-agent/blender/tools/blib.py").read())

Правила библиотеки:
  - кубы создаются size=2 (scale = полуразмер);
  - направленная геометрия — make_beam (без Euler-поворотов цилиндров);
  - после scale/rotation — transform_apply сразу;
  - размеры от соседей — только из verify_bounds;
  - ничего не вызывается как «ops» бездумно: функции сами готовят контекст.
"""
import bpy
import bmesh
import math
from mathutils import Vector


# ------------------------------------------------------------------ материалы
def mat(name, base, metallic=0.0, rough=0.5, alpha=None, emission=None, strength=0.0):
    """Простой PBR-материал. alpha < 1 включает прозрачность (BLEND)."""
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = base
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if alpha is not None:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = 'BLEND'
    if emission is not None:
        b.inputs["Emission Color"].default_value = emission
        b.inputs["Emission Strength"].default_value = strength
    return m


# ------------------------------------------------------------------ операции
def solo(obj):
    """Сделать obj единственным выделенным и активным (для ops)."""
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def apply_transforms(obj, location=False):
    solo(obj)
    bpy.ops.object.transform_apply(location=location, rotation=True, scale=True)
    bpy.ops.object.select_all(action='DESELECT')
    return obj


def bevel(obj, width, segments=3, angle=30):
    """Фаска-скругление и немедленное применение."""
    b = obj.modifiers.new("Bev", 'BEVEL')
    b.width = width
    b.segments = segments
    b.limit_method = 'ANGLE'
    b.angle_limit = math.radians(angle)
    solo(obj)
    bpy.ops.object.modifier_apply(modifier="Bev")
    bpy.ops.object.select_all(action='DESELECT')
    return obj


def boolean_difference(target, cutter, delete_cutter=True):
    mod = target.modifiers.new("Bool", 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cutter
    solo(target)
    bpy.ops.object.modifier_apply(modifier="Bool")
    bpy.ops.object.select_all(action='DESELECT')
    if delete_cutter:
        bpy.data.objects.remove(cutter, do_unlink=True)
    return target


# ------------------------------------------------------------------ примитивы
def cube(name, loc, half, material=None, roty=0.0, rotx=0.0, bev=0.0):
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = half
    if roty or rotx:
        obj.rotation_euler = (rotx, roty, 0)
    apply_transforms(obj)
    if material:
        obj.data.materials.append(material)
    if bev > 0:
        bevel(obj, bev, 2, 40)
    return obj


def cyl(name, r, depth, loc, material=None, verts=32, bev=0.0, rotx=0.0, roty=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=(rotx, roty, 0))
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.transform_apply(rotation=True)
    if material:
        obj.data.materials.append(material)
    if bev > 0:
        bevel(obj, bev, 2, 40)
    return obj


def cone(name, r1, r2, depth, loc, material=None, verts=32, rotx=0.0, roty=0.0):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=(rotx, roty, 0))
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.transform_apply(rotation=True)
    if material:
        obj.data.materials.append(material)
    return obj


def sphere(name, r, loc, material=None, squash_z=1.0, segments=28):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=segments // 2, radius=r, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (1, 1, squash_z)
    apply_transforms(obj)
    if material:
        obj.data.materials.append(material)
    return obj


def make_beam(name, start, end, hw=0.008, hh=0.008, material=None):
    """Брусок из start в end без Euler-поворотов. hw — по одной оси, hh — по другой."""
    dx, dy, dz = end[0]-start[0], end[1]-start[1], end[2]-start[2]
    L = math.sqrt(dx*dx + dy*dy + dz*dz)
    if L < 1e-6:
        return None
    fx, fy, fz = dx/L, dy/L, dz/L
    ux, uy, uz = (0, 0, 1) if abs(fz) < 0.99 else (1, 0, 0)
    rx, ry, rz = fy*uz-fz*uy, fz*ux-fx*uz, fx*uy-fy*ux
    rL = math.sqrt(rx*rx+ry*ry+rz*rz)
    rx, ry, rz = rx/rL, ry/rL, rz/rL
    upx, upy, upz = ry*fz-rz*fy, rz*fx-rx*fz, rx*fy-ry*fx
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    verts = []
    for base in (start, end):
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            verts.append(bm.verts.new((
                base[0]+rx*hw*sx+upx*hh*sy,
                base[1]+ry*hw*sx+upy*hh*sy,
                base[2]+rz*hw*sx+upz*hh*sy)))
    v = verts
    for f in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (0, 3, 2, 1), (4, 5, 6, 7)):
        bm.faces.new([v[i] for i in f])
    bm.to_mesh(mesh)
    bm.free()
    if material:
        obj.data.materials.append(material)
    return obj


# ------------------------------------------------------------------ проверки
def verify_bounds(name):
    obj = bpy.data.objects[name]
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    b = {k: (min(getattr(v, k) for v in vs), max(getattr(v, k) for v in vs)) for k in 'xyz'}
    print(f"{name}: X[{b['x'][0]:.3f},{b['x'][1]:.3f}] Y[{b['y'][0]:.3f},{b['y'][1]:.3f}] Z[{b['z'][0]:.3f},{b['z'][1]:.3f}]")
    return b


def verify_overlap(name_a, name_b, axis='z', min_overlap=0.005):
    a, b = verify_bounds(name_a), verify_bounds(name_b)
    overlap = min(a[axis][1], b[axis][1]) - max(a[axis][0], b[axis][0])
    ok = overlap >= min_overlap
    print(f"  {name_a} <-> {name_b} [{axis.upper()}]: {'OK' if ok else 'GAP!'} ({overlap:.4f})")
    return ok


def audit_all():
    issues = []
    for obj in sorted((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: o.name):
        rot = tuple(round(c, 3) for c in obj.rotation_euler)
        scl = tuple(round(c, 3) for c in obj.scale)
        if rot != (0.0, 0.0, 0.0) or scl != (1.0, 1.0, 1.0):
            issues.append((obj.name, rot, scl))
    print("AUDIT:", "чисто" if not issues else issues)
    return not issues


# ------------------------------------------------------------------ сцена
def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return obj


def add_area(name, loc, energy, size, target=(0, 0, 0.8)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.size = size
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    bpy.context.collection.objects.link(lo)
    aim(lo, target)
    return lo


def studio(target=(0, 0, 0.8), scale=1.0, cam_pos=None, lens=50, floor=True):
    """Студийный свет под масштаб объекта: scale ≈ характерный размер (м)."""
    s = bpy.context.scene
    add_area("Key", (4.5*scale, -5.5*scale, 5.5*scale), 1500*scale*scale, 7*scale, target)
    add_area("Fill", (-5.0*scale, -4.0*scale, 3.5*scale), 500*scale*scale, 6*scale, target)
    add_area("Rim", (-4.0*scale, 5.5*scale, 3.5*scale), 900*scale*scale, 5*scale, (target[0], target[1], target[2]+0.1))
    sd = bpy.data.lights.new("Sun", "SUN")
    sd.energy = 2.0
    sd.angle = math.radians(10)
    so = bpy.data.objects.new("Sun", sd)
    bpy.context.collection.objects.link(so)
    so.rotation_euler = (math.radians(55), 0, math.radians(35))
    if floor and bpy.data.objects.get("Floor") is None:
        bpy.ops.mesh.primitive_plane_add(size=40*scale, location=(0, 0, 0))
        floor_obj = bpy.context.active_object
        floor_obj.name = "Floor"
        fm = mat("Floor", (0.04, 0.043, 0.05, 1), 0.1, 0.55)
        floor_obj.data.materials.append(fm)
    cam = bpy.data.objects.get("Camera")
    if cam is None:
        cam_data = bpy.data.cameras.new("Camera")
        cam = bpy.data.objects.new("Camera", cam_data)
        bpy.context.collection.objects.link(cam)
    cam.data.lens = lens
    if cam_pos is not None:
        cam.location = cam_pos
    aim(cam, target)
    s.camera = cam
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.render.resolution_x = 900
    s.render.resolution_y = 620
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    s.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg is not None:
        bg.inputs[0].default_value = (0.045, 0.05, 0.06, 1.0)
        bg.inputs[1].default_value = 0.6
    return cam


# ------------------------------------------------------------------ выдача
def save_scene(path):
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("saved:", path)


def save_milestone(path):
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("milestone:", path)


def export_glb(out, exclude=("Floor",)):
    bpy.ops.object.select_all(action='DESELECT')
    count = 0
    for obj in bpy.data.objects:
        keep = obj.type == 'MESH' and obj.name.split(".")[0] not in set(exclude)
        obj.select_set(keep)
        count += keep
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_apply=True)
    print("exported:", out, "meshes:", count)
    return out


def render_preview(path, res=(360, 240), samples=24):
    import os
    s = bpy.context.scene
    old = (s.render.resolution_x, s.render.resolution_y, s.cycles.samples, s.render.filepath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    s.render.resolution_x, s.render.resolution_y = res
    s.cycles.samples = samples
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)
    s.render.resolution_x, s.render.resolution_y, s.cycles.samples, s.render.filepath = old
    print("preview:", path)
    return path


print("blib: загружено —", ", ".join(sorted(n for n in dir() if not n.startswith("_") and callable(globals()[n]))))


# ------------------------------------------------------------------ продвинутые приёмы
def lathe(name, profile, steps=96, material=None, thickness=None, offset=-1.0, merge=0.0008):
    """Тело вращения (lathe/screw): profile = [(r, z), ...] вдоль поверхности (дно -> кромка).
    thickness + offset дают толщину стенки (Solidify). Вращение вокруг оси Z."""
    mesh = bpy.data.meshes.new(name)
    verts = [(r, 0.0, z) for r, z in profile]
    edges = [(i, i + 1) for i in range(len(verts) - 1)]
    mesh.from_pydata(verts, edges, [])
    mesh.validate()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    sc = obj.modifiers.new("Lathe", 'SCREW')
    sc.axis = 'Z'
    sc.angle = math.radians(360)
    sc.steps = steps
    sc.use_merge_vertices = True
    sc.merge_threshold = merge
    solo(obj)
    bpy.ops.object.modifier_apply(modifier="Lathe")
    if thickness:
        so = obj.modifiers.new("Wall", 'SOLIDIFY')
        so.thickness = thickness
        so.offset = offset
        so.use_even_offset = True
        bpy.ops.object.modifier_apply(modifier="Wall")
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=merge)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth()
    return obj


def curve_tube(name, points, section=None, radius=None, material=None, resolution=16):
    """Плавная труба/лента по Безье через точки. section=(half_width, half_thickness) — плоская лента;
    иначе radius — круглое сечение."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.resolution_u = resolution
    cu.use_fill_caps = True
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(points) - 1)
    for bp, co in zip(sp.bezier_points, points):
        bp.co = co
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    prof_obj = None
    if section is not None:
        w, t = section
        pts2 = [(w, t * 0.45), (w * 0.55, t), (-w * 0.55, t), (-w, t * 0.45),
                (-w, -t * 0.45), (-w * 0.55, -t), (w * 0.55, -t), (w, -t * 0.45)]
        pc = bpy.data.curves.new(name + "Prof", 'CURVE')
        pc.dimensions = '2D'
        sk = pc.splines.new('POLY')
        sk.points.add(len(pts2) - 1)
        for i, (x, y) in enumerate(pts2):
            sk.points[i].co = (x, y, 0, 1)
        sk.use_cyclic_u = True
        prof_obj = bpy.data.objects.new(name + "Prof", pc)
        bpy.context.collection.objects.link(prof_obj)
        cu.bevel_mode = 'OBJECT'
        cu.bevel_object = prof_obj
    else:
        cu.bevel_depth = radius or 0.01
    obj = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(obj)
    solo(obj)
    bpy.ops.object.convert(target='MESH')
    obj = bpy.context.active_object
    if prof_obj is not None:
        bpy.data.objects.remove(prof_obj, do_unlink=True)
    if material:
        obj.data.materials.append(material)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth()
    return obj


def shrinkwrap_to(obj, target, offset=0.0012, method='NEAREST_SURFACEPOINT'):
    """Прижать объект к поверхности target (декали/надписи): модификатор Shrinkwrap."""
    sw = obj.modifiers.new("Wrap", 'SHRINKWRAP')
    sw.target = target
    sw.wrap_method = method
    sw.wrap_mode = 'ABOVE_SURFACE'
    sw.offset = offset
    solo(obj)
    bpy.ops.object.modifier_apply(modifier="Wrap")
    return obj
