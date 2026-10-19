"""Студийный сетап сцены: свет, пол, камера, настройки Cycles.

Использование (в CLI-сборке):
  blender -b file.blend --python studio.py
или внутри execute_blender_code:  exec(compile(open("<путь>/studio.py").read(), "studio.py", "exec"))

После вызова: scene.camera = cam-объект, рендер настроен на Cycles CPU 900x600.
"""
import bpy
import math
from mathutils import Vector


def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def add_area(name, loc, energy, size, target=(0, 0, 0.8)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.size = size
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    bpy.context.collection.objects.link(lo)
    aim(lo, target)
    return lo


def studio(target=(0, 0, 0.8), camera_loc=(5.4, -5.2, 2.35)):
    if bpy.data.objects.get("Key") is None:
        add_area("Key", (4.5, -5.5, 5.5), 1500, 7, target)
        add_area("Fill", (-5.0, -4.0, 3.5), 500, 6, target)
        add_area("Rim", (-4.0, 5.5, 3.5), 900, 5, target)
    if bpy.data.objects.get("Sun") is None:
        sd = bpy.data.lights.new("Sun", "SUN")
        sd.energy = 2.0
        sd.angle = math.radians(10)
        so = bpy.data.objects.new("Sun", sd)
        bpy.context.collection.objects.link(so)
        so.rotation_euler = (math.radians(55), 0, math.radians(35))
    if bpy.data.objects.get("Floor") is None:
        bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
        floor = bpy.context.active_object
        floor.name = "Floor"
        fm = bpy.data.materials.new("Floor")
        fm.use_nodes = True
        b = fm.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.035, 0.04, 0.05, 1)
        b.inputs["Roughness"].default_value = 0.55
        floor.data.materials.append(fm)
    cam = bpy.data.objects.get("Camera")
    if cam is None:
        cam_data = bpy.data.cameras.new("Camera")
        cam_data.lens = 50
        cam = bpy.data.objects.new("Camera", cam_data)
        bpy.context.collection.objects.link(cam)
    cam.location = camera_loc
    aim(cam, target)
    s = bpy.context.scene
    s.camera = cam
    s.render.engine = "CYCLES"
    s.cycles.samples = 64
    s.cycles.device = "CPU"
    s.render.resolution_x = 900
    s.render.resolution_y = 600
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    s.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg is not None:
        bg.inputs[0].default_value = (0.04, 0.05, 0.07, 1.0)
        bg.inputs[1].default_value = 0.5
    return cam


if __name__ == "__main__":
    studio()
    print("STUDIO-READY")
