"""QA-проверка .blend: отчёт по объектам, габаритам, трансформам, материалам.

Использование:
  blender -b file.blend --python qa_check.py
Печатает по строке на объект и в конце строку QA-DONE (её удобно грепать).
"""
import bpy

print("=== QA:", bpy.data.filepath or "(без имени)", "===")
meshes = sorted((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: o.name)
total_tris = 0
issues = []
for obj in meshes:
    me = obj.data
    me.calc_loop_triangles()
    tris = len(me.loop_triangles)
    total_tris += tris
    rot = tuple(round(c, 3) for c in obj.rotation_euler)
    scl = tuple(round(c, 3) for c in obj.scale)
    clean = rot == (0.0, 0.0, 0.0) and scl == (1.0, 1.0, 1.0)
    mats = ",".join(m.name for m in me.materials) or "-"
    vs = [obj.matrix_world @ v.co for v in me.vertices]
    if vs:
        dims = "{:.3f}x{:.3f}x{:.3f}".format(
            max(v.x for v in vs) - min(v.x for v in vs),
            max(v.y for v in vs) - min(v.y for v in vs),
            max(v.z for v in vs) - min(v.z for v in vs),
        )
    else:
        dims = "-"
    print(f"  [{'OK' if clean else '!!'}] {obj.name:28s} tris={tris:6d} size={dims:22s} mats={mats}")
    if not clean:
        issues.append(obj.name)
print(f"mesh-объектов: {len(meshes)}, треугольников: {total_tris}")
print("issues:", ", ".join(issues) if issues else "нет")
print("QA-DONE")
