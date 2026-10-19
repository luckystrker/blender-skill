# Blender: кодовые паттерны (шпаргалка)

Проверенные сниппеты для `execute_blender_code` (Blender 4.5, bpy). Копируй целиком — все они рабочие.

## Карта соединений (комментарий в начале кода)

```python
# Connection Map (пример):
#   body_bottom (Z=0.30)  <-> wheels (Z=0..0.84)   overlap: оси колёс врезаны в арки
#   mirror_stem входит в борт (y=±1.015) на 4 см     overlap: 0.04m по Y
#   light_bar врезана в нос (x=2.95) на 1.5 см       overlap: 0.015m по X
```

## make_beam — направленная геометрия без Euler-поворотов

```python
import bpy, bmesh, math

def make_beam(name, start, end, hw=0.012, hh=0.010, material=None):
    """Брусок из точки start в точку end (ноги, стойки, спицы, дуги). Без поворотов."""
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
                base[2]+rz*hw*sx+upz*hh*sy,
            )))
    v = verts
    for f in ((0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(0,3,2,1),(4,5,6,7)):
        bm.faces.new([v[i] for i in f])
    bm.to_mesh(mesh); bm.free()
    if material:
        obj.data.materials.append(material)
    return obj
```

## verify_bounds / verify_overlap — проверка после каждой части

```python
def verify_bounds(name):
    obj = bpy.data.objects[name]
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    b = {
        'x': (min(v.x for v in vs), max(v.x for v in vs)),
        'y': (min(v.y for v in vs), max(v.y for v in vs)),
        'z': (min(v.z for v in vs), max(v.z for v in vs)),
    }
    print(f"{name}: X[{b['x'][0]:.3f},{b['x'][1]:.3f}] Y[{b['y'][0]:.3f},{b['y'][1]:.3f}] Z[{b['z'][0]:.3f},{b['z'][1]:.3f}]")
    return b

def verify_overlap(name_a, name_b, axis='z', min_overlap=0.005):
    a, b = verify_bounds(name_a), verify_bounds(name_b)
    overlap = min(a[axis][1], b[axis][1]) - max(a[axis][0], b[axis][0])
    ok = overlap >= min_overlap
    print(f"  {name_a} <-> {name_b} [{axis.upper()}]: {'OK' if ok else 'GAP!'} ({overlap:.4f})")
    return ok
```

## finalize / audit_all — чистота сцены в конце

```python
def finalize(name):
    obj = bpy.data.objects[name]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    bpy.ops.object.select_all(action='DESELECT')

def audit_all():
    all_ok = True
    for obj in sorted((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: o.name):
        rot = tuple(round(c, 3) for c in obj.rotation_euler)
        scl = tuple(round(c, 3) for c in obj.scale)
        ok = rot == (0.0, 0.0, 0.0) and scl == (1.0, 1.0, 1.0)
        all_ok = all_ok and ok
        print(f"  [{'OK' if ok else '!!'}] {obj.name:26s} rot={rot} scl={scl}")
    print("clean =", all_ok)
    return all_ok
```

## Корпус из 2D-профиля (экструзия контура) — как у Cybertruck

```python
import bpy
from mathutils import Vector

def profile_body(name, profile_xz, width, material):
    """Замкнутый корпус: контур в XZ, extrusion по ±Y. profile_xz — [(x, z), ...] по часовой."""
    W = width / 2
    verts = [(x, -W, z) for x, z in profile_xz] + [(x, W, z) for x, z in profile_xz]
    n = len(profile_xz)
    faces = [tuple(range(n)), tuple(range(2*n-1, n-1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, n + i, n + j, j))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj
```

## Арки колёс — булев вырез цилиндрами

```python
def cut_arch(body, x, radius=0.55, depth=2.2, z=0.42):
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=radius, depth=depth,
                                        location=(x, 0, z), rotation=(math.pi/2, 0, 0))
    cutter = bpy.context.active_object
    mod = body.modifiers.new("Arch", 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cutter
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier="Arch")
    bpy.data.objects.remove(cutter, do_unlink=True)
```

## Студийный свет + камера + пол (стандартный сетап)

```python
import bpy, math
from mathutils import Vector

def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def add_area(name, loc, energy, size, target=(0, 0, 0.8)):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size
    lo = bpy.data.objects.new(name, ld); lo.location = loc
    bpy.context.collection.objects.link(lo); aim(lo, target)
    return lo

def studio(target=(0, 0, 0.8)):
    add_area("Key", (4.5, -5.5, 5.5), 1500, 7, target)
    add_area("Fill", (-5.0, -4.0, 3.5), 500, 6, target)
    add_area("Rim", (-4.0, 5.5, 3.5), 900, 5, target)
    sd = bpy.data.lights.new("Sun", "SUN"); sd.energy = 2.0; sd.angle = math.radians(10)
    so = bpy.data.objects.new("Sun", sd); bpy.context.collection.objects.link(so)
    so.rotation_euler = (math.radians(55), 0, math.radians(35))
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    floor = bpy.context.active_object; floor.name = "Floor"
    fm = bpy.data.materials.new("Floor"); fm.use_nodes = True
    b = fm.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.035, 0.04, 0.05, 1)
    b.inputs["Roughness"].default_value = 0.55
    floor.data.materials.append(fm)
    cam_data = bpy.data.cameras.new("Camera"); cam_data.lens = 50
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = (5.4, -5.2, 2.35); aim(cam, (0.1, 0, 0.75))
    bpy.context.scene.camera = cam
    s = bpy.context.scene
    s.render.engine = "CYCLES"; s.cycles.samples = 64; s.cycles.device = "CPU"
    s.render.resolution_x = 900; s.render.resolution_y = 600
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    s.world = world; world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.04, 0.05, 0.07, 1.0); bg.inputs[1].default_value = 0.5
    return cam
```

## Milestone: сохранить / вернуть состояние

```python
bpy.ops.wm.save_as_mainfile(filepath="/path/milestones/<имя>.blend")
bpy.ops.wm.open_mainfile(filepath="/path/milestones/<имя>.blend")
```

## Экспорт .glb + превью-миниатюра

```python
import os
# экспорт: только меши модели, без Floor/света/камеры
bpy.ops.object.select_all(action='DESELECT')
exclude = {"Floor"}
count = 0
for obj in bpy.data.objects:
    keep = obj.type == 'MESH' and obj.name.split(".")[0] not in exclude
    obj.select_set(keep)
    count += keep
bpy.ops.export_scene.gltf(filepath="/path/models/<id>.glb", export_format='GLB', use_selection=True, export_apply=True)

# превью
s = bpy.context.scene
old = (s.render.resolution_x, s.render.resolution_y, s.cycles.samples, s.render.filepath)
s.render.resolution_x, s.render.resolution_y, s.cycles.samples = 360, 240, 24
os.makedirs("/path/previews", exist_ok=True)
s.render.filepath = "/path/previews/<id>.png"
bpy.ops.render.render(write_still=True)
s.render.resolution_x, s.render.resolution_y, s.cycles.samples, s.render.filepath = old
```

## Процедурный материал (без UV, Object-координаты)

```python
def noise_material(name, dark, light, scale=8, roughness=0.4):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    n, l = mat.node_tree.nodes, mat.node_tree.links
    n.clear()
    out = n.new('ShaderNodeOutputMaterial'); bsdf = n.new('ShaderNodeBsdfPrincipled'); bsdf.location = (100, 0)
    ramp = n.new('ShaderNodeValToRGB'); ramp.location = (-200, 0)
    ramp.color_ramp.elements[0].color = dark; ramp.color_ramp.elements[1].color = light
    noise = n.new('ShaderNodeTexNoise'); noise.location = (-400, 0); noise.inputs['Scale'].default_value = scale
    tex = n.new('ShaderNodeTexCoord'); tex.location = (-800, 0)
    l.new(tex.outputs['Object'], noise.inputs['Vector'])
    l.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    l.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = roughness
    l.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat
```

## Грабли Blender 4.x (короткий список)
- Нет входа `Subsurface Color` (удалён) — не трогай.
- `bpy.ops.view3d.*` вне 3D-контекста падает — работай с `area.spaces[0].region_3d` напрямую.
- Не вызывай `bpy.ops.outliner.orphans_purge()` — теряются материалы.
- Не предполагай, что Camera существует — сперва `[o.name for o in bpy.data.objects]`.
- Депрессии формы делай мультипликативно (`z = z_bot + (z_top-z_bot)*k`), не вычитанием — иначе дырки.
