"""Convert MASSX-RZ's downloaded cabin into a separate real-time asset copy.

Run with Blender --background --disable-autoexec Original/EndlessJourney.blend.
The original scene is never saved over. Procedural materials are baked into
tileable PBR maps before the evaluated room is exported for Unreal.
"""
import bpy
import json
import re
import math
from collections import Counter
from pathlib import Path
from mathutils import Vector, Matrix

root = Path(__file__).resolve().parents[1]
asset = root / "Assets/ThirdParty/EndlessJourney"
out = asset / "GameCopy"
out.mkdir(exist_ok=True)
texdir = out / "Textures"
texdir.mkdir(exist_ok=True)
scene = bpy.context.scene

for image in bpy.data.images:
    if image.filepath:
        path = asset / image.filepath.replace("//", "")
        if path.exists():
            image.filepath = str(path)
            image.reload()

# Limit costly render subdivision/bevels in this game copy.
for obj in scene.objects:
    for mod in obj.modifiers:
        if mod.type == "SUBSURF":
            mod.levels = min(mod.levels, 1)
            mod.render_levels = min(mod.render_levels, 1)
        elif mod.type == "BEVEL":
            mod.segments = min(mod.segments, 3)
deps = bpy.context.evaluated_depsgraph_get()
instances = []
base_meshes = {}
for i in deps.object_instances:
    obj = i.object
    key = (obj.name, obj.data.as_pointer()) if obj.type in {"MESH", "CURVE", "SURFACE", "FONT"} else None
    if i.show_self and not obj.original.hide_render and key is not None and key not in base_meshes:
        base_meshes[key] = bpy.data.meshes.new_from_object(obj, preserve_all_data_layers=True, depsgraph=deps)
    instances.append((obj.original, i.matrix_world.copy(), i.show_self, i.is_instance, key))
collection = bpy.data.collections.new("GameCopy")
scene.collection.children.link(collection)
# Simplify repeated geometry once before expanding its instances.
repeats = Counter(i[4] for i in instances if i[2] and i[4] is not None)
for key, mesh in list(base_meshes.items()):
    count = repeats[key]
    limit = 384 if key[0].startswith("HexFloor") else 160
    if count <= 32:
        limit = 8000 if key[0].startswith(("Leaves", "Moss", "Branches", "Mattress")) else 20000
    if len(mesh.polygons) > limit:
        proxy = bpy.data.objects.new("LOD_Conversion", mesh)
        collection.objects.link(proxy)
        bpy.ops.object.select_all(action="DESELECT")
        proxy.select_set(True)
        bpy.context.view_layer.objects.active = proxy
        mod = proxy.modifiers.new("Real-time geometry budget", "DECIMATE")
        mod.ratio = limit / len(mesh.polygons)
        bpy.ops.object.modifier_apply(modifier=mod.name)
        base_meshes[key] = proxy.data
        bpy.data.objects.remove(proxy, do_unlink=True)
print("SHARED_GEOMETRY_OPTIMIZED", len(base_meshes), flush=True)
meshes = []
lights = []
offset = Vector((12.5, -1.6, 0.1))
for obj, matrix, show, instanced, key in instances:
    if not show or obj.hide_render:
        continue
    if not instanced and not obj.visible_get():
        continue
    if obj.type == "LIGHT":
        pos = matrix.translation - offset
        lights.append({"name": obj.name, "type": obj.data.type,
                       "position": list(pos), "rotation": list(matrix.to_euler()),
                       "color": list(obj.data.color), "energy": obj.data.energy,
                       "size": getattr(obj.data, "size", 0.1),
                       "size_y": getattr(obj.data, "size_y", 0.1)})
    if obj.type not in {"MESH", "CURVE", "SURFACE", "FONT"}:
        continue
    if any(s.material and s.material.name == "Volume" for s in obj.material_slots):
        continue
    mesh = base_meshes[key].copy()
    if not mesh.polygons:
        bpy.data.meshes.remove(mesh)
        continue
    # World positions preserve collection instances and geometry-node output.
    mesh.transform(matrix)
    item = bpy.data.objects.new("Part_" + obj.name, mesh)
    collection.objects.link(item)
    if obj.name.startswith(("Moss", "Leaves", "Branches", "Thermoball")) and len(mesh.polygons) > 20000:
        bpy.ops.object.select_all(action="DESELECT")
        item.select_set(True)
        bpy.context.view_layer.objects.active = item
        dec = item.modifiers.new("Game decorative LOD", "DECIMATE")
        dec.ratio = max(0.04, min(1.0, 18000 / len(mesh.polygons)))
        bpy.ops.object.modifier_apply(modifier=dec.name)
    if not item.data.uv_layers:
        uv = item.data.uv_layers.new(name="UVMap")
        for face in item.data.polygons:
            normal = face.normal
            axis = max(range(3), key=lambda i: abs(normal[i]))
            axes = [i for i in range(3) if i != axis]
            for index in face.loop_indices:
                v = item.data.vertices[item.data.loops[index].vertex_index].co
                uv.data[index].uv = (v[axes[0]], v[axes[1]])
    meshes.append(item)

(out / "geometry-cost.json").write_text(json.dumps(sorted([(o.name, len(o.data.polygons)) for o in meshes], key=lambda x:x[1], reverse=True), indent=2))
print("EVALUATED_ROOM", len(meshes), "parts", sum(len(o.data.polygons) for o in meshes), "polygons", flush=True)
materials = {m for o in meshes for m in o.data.materials if m}
manifest = {"source": "MASSX-RZ / Endless Journey", "offset": list(offset),
            "lights": lights, "materials": {}, "meshes": len(meshes)}

# The author's procedural metal/plastic shaders are shared tiling materials.
# Bake each shader on a meter-sized plane with object coordinates intact.
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -20))
plane = bpy.context.object
plane.name = "MaterialBakePlane"
plane.location = (0, 0, 0)
for original in list(scene.objects):
    if original != plane:
        original.hide_render = True
scene.render.engine = "CYCLES"
scene.cycles.samples = 1
scene.cycles.device = "CPU"
scene.render.bake.margin = 8
scene.render.bake.use_selected_to_active = False

def input_value(node, key, default):
    if node and key in node.inputs:
        v = node.inputs[key].default_value
        return list(v) if hasattr(v, "__len__") else float(v)
    return default

def bake(mat, shader, channel, original_output, original_surface):
    tree = mat.node_tree
    filename = re.sub(r"[^A-Za-z0-9_]", "_", mat.name) + "_" + channel + ".png"
    if (texdir / filename).exists():
        return bpy.data.images.load(str(texdir / filename), check_existing=True)
    image = bpy.data.images.new(filename, width=1024, height=1024, alpha=False)
    image.colorspace_settings.name = "sRGB" if channel in {"BaseColor", "Emission"} else "Non-Color"
    target = tree.nodes.new("ShaderNodeTexImage")
    target.image = image
    tree.nodes.active = target
    emit = None
    if channel != "Normal":
        emit = tree.nodes.new("ShaderNodeEmission")
        socket_name = {"BaseColor": "Base Color", "Metallic": "Metallic", "Roughness": "Roughness", "Emission": "Emission Color"}[channel]
        socket = shader.inputs[socket_name]
        if socket.is_linked:
            tree.links.new(socket.links[0].from_socket, emit.inputs["Color"])
        else:
            v = socket.default_value
            emit.inputs["Color"].default_value = v if hasattr(v, "__len__") else (v, v, v, 1)
        tree.links.new(emit.outputs[0], original_output.inputs["Surface"])
    plane.data.materials.clear()
    plane.data.materials.append(mat)
    bpy.ops.object.select_all(action="DESELECT")
    plane.select_set(True)
    bpy.context.view_layer.objects.active = plane
    bpy.ops.object.bake(type="NORMAL" if channel == "Normal" else "EMIT")
    image.filepath_raw = str(texdir / filename)
    image.file_format = "PNG"
    image.save()
    if emit:
        tree.nodes.remove(emit)
        tree.links.new(original_surface, original_output.inputs["Surface"])
    tree.nodes.remove(target)
    return image

for mat in sorted(materials, key=lambda m: m.name):
    tree = mat.node_tree
    if not tree:
        continue
    shader = next((n for n in tree.nodes if n.type in {"BSDF_PRINCIPLED", "BSDF_ANISOTROPIC"}), None)
    emission = next((n for n in tree.nodes if n.type == "EMISSION"), None)
    output = next((n for n in tree.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None)
    spec = {"base": input_value(shader, "Base Color", input_value(shader, "Color", [0.1, 0.1, 0.1, 1])),
            "metallic": input_value(shader, "Metallic", 1 if shader and shader.type == "BSDF_ANISOTROPIC" else 0),
            "roughness": input_value(shader, "Roughness", 0.5),
            "emission": input_value(emission, "Color", input_value(shader, "Emission Color", [0, 0, 0, 1])),
            "emission_strength": input_value(emission, "Strength", input_value(shader, "Emission Strength", 0)),
            "transparent": mat.name.startswith(("Glass", "Water", "PlasticShinyTransparent")), "textures": {}}
    baked = {}
    if shader and shader.type == "BSDF_PRINCIPLED" and output and output.inputs["Surface"].is_linked and not spec["transparent"]:
        original_surface = output.inputs["Surface"].links[0].from_socket
        for channel, socket in [("BaseColor", "Base Color"), ("Metallic", "Metallic"), ("Roughness", "Roughness"), ("Normal", "Normal")]:
            if shader.inputs[socket].is_linked:
                baked[channel] = bake(mat, shader, channel, output, original_surface)
                spec["textures"][channel] = baked[channel].filepath
    # Keep existing image textures in the plant/boot materials rather than
    # replacing their author-supplied UV textures with a tiling approximation.
    if mat.name in {"Pot", "Leaves", "Trunk_LowPoly", "Vegetation", "ThermoballLaceUpboot_HighPoly"}:
        for channel, fragment in [("BaseColor", "BaseColor"), ("Normal", "NormalGL"), ("Roughness", "Roughness")]:
            image = next((n.image for n in tree.nodes if n.type == "TEX_IMAGE" and n.image and fragment in n.image.name), None)
            if image:
                spec["textures"][channel] = image.filepath
                baked[channel] = image
    if mat.name in {"MonitorDisplay", "News"}:
        image = next((n.image for n in tree.nodes if n.type == "TEX_IMAGE" and n.image), None)
        if image:
            spec["textures"]["Emission"] = image.filepath
            spec["emission_strength"] = 1.5
            baked["Emission"] = image
    manifest["materials"][mat.name] = spec
    # Replace just the exported copy's shader with portable Principled PBR.
    tree.nodes.clear()
    pbr = tree.nodes.new("ShaderNodeBsdfPrincipled")
    dest = tree.nodes.new("ShaderNodeOutputMaterial")
    tree.links.new(pbr.outputs[0], dest.inputs["Surface"])
    pbr.inputs["Base Color"].default_value = spec["base"]
    pbr.inputs["Metallic"].default_value = spec["metallic"]
    pbr.inputs["Roughness"].default_value = spec["roughness"]
    pbr.inputs["Emission Color"].default_value = spec["emission"]
    pbr.inputs["Emission Strength"].default_value = spec["emission_strength"]
    if spec["transparent"]:
        pbr.inputs["Alpha"].default_value = 0.08
        pbr.inputs["Transmission Weight"].default_value = 0.95
    for channel, img in baked.items():
        n = tree.nodes.new("ShaderNodeTexImage")
        n.image = img
        if channel == "Normal":
            normal = tree.nodes.new("ShaderNodeNormalMap")
            tree.links.new(n.outputs["Color"], normal.inputs["Color"])
            tree.links.new(normal.outputs[0], pbr.inputs["Normal"])
        else:
            tree.links.new(n.outputs["Color"], pbr.inputs[{"BaseColor": "Base Color", "Roughness": "Roughness", "Metallic": "Metallic", "Emission": "Emission Color"}[channel]])
    print("MATERIAL_READY", mat.name, list(spec["textures"]), flush=True)

bpy.data.objects.remove(plane, do_unlink=True)
bpy.ops.object.select_all(action="DESELECT")
for obj in meshes:
    obj.hide_render = False
    obj.hide_set(False)
    obj.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.join()
cabin = bpy.context.object
cabin.name = "SM_EndlessJourneyCabin"
cabin.data.transform(Matrix.Translation(-offset))
manifest["polygons"] = len(cabin.data.polygons)
manifest["vertices"] = len(cabin.data.vertices)
bpy.ops.export_scene.fbx(filepath=str(out / "EndlessJourneyCabin.fbx"), use_selection=True,
                         object_types={"MESH"}, axis_forward="-Y", axis_up="Z",
                         use_mesh_modifiers=True, bake_anim=False, path_mode="COPY")
bpy.ops.export_scene.gltf(filepath=str(out / "EndlessJourneyCabin.glb"), export_format="GLB",
                         use_selection=True, export_yup=True, export_apply=True)
(out / "manifest.json").write_text(json.dumps(manifest, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out / "EndlessJourneyGameCopy.blend"))
print("GAME_COPY_READY", out, manifest["polygons"], "polygons", flush=True)
