"""Inspect downloaded artwork without modifying the original Blender file."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
report = {"units": {"system": bpy.context.scene.unit_settings.system,
                    "scale": bpy.context.scene.unit_settings.scale_length},
          "render_engine": bpy.context.scene.render.engine,
          "camera": bpy.context.scene.camera.name if bpy.context.scene.camera else None,
          "objects": [], "images": [], "materials": []}
for obj in bpy.context.scene.objects:
    item = {"name": obj.name, "type": obj.type, "hidden_render": obj.hide_render,
            "location": list(obj.location), "rotation": list(obj.rotation_euler),
            "scale": list(obj.scale), "dimensions": list(obj.dimensions)}
    if obj.type == "MESH":
        bounds = [obj.matrix_world @ Vector(p) for p in obj.bound_box]
        item.update(vertices=len(obj.data.vertices), polygons=len(obj.data.polygons),
                    bounds_min=[min(p[i] for p in bounds) for i in range(3)],
                    bounds_max=[max(p[i] for p in bounds) for i in range(3)],
                    materials=[s.material.name if s.material else None for s in obj.material_slots],
                    modifiers=[{"name": m.name, "type": m.type,
                                "viewport": m.show_viewport, "render": m.show_render,
                                "levels": getattr(m, "levels", None),
                                "render_levels": getattr(m, "render_levels", None)} for m in obj.modifiers])
    elif obj.type == "LIGHT":
        item.update(light_type=obj.data.type, energy=obj.data.energy, color=list(obj.data.color))
    elif obj.type == "CAMERA":
        item.update(lens=obj.data.lens)
    report["objects"].append(item)
for img in bpy.data.images:
    report["images"].append({"name": img.name, "path": img.filepath,
                             "packed": bool(img.packed_file), "size": list(img.size)})
for mat in bpy.data.materials:
    nodes = []
    if mat.use_nodes:
        for n in mat.node_tree.nodes:
            nodes.append({"name": n.name, "type": n.bl_idname,
                          "image": n.image.name if n.type == "TEX_IMAGE" and n.image else None,
                          "inputs": {i.name: list(i.default_value) if hasattr(i.default_value, "__len__") and not isinstance(i.default_value, str) else i.default_value
                                     for i in n.inputs if hasattr(i, "default_value") and not i.is_linked and isinstance(i.default_value, (float, int, str, Vector, bpy.types.bpy_prop_array))},
                          "links": [{"from": l.from_node.name, "socket": l.from_socket.name, "to": l.to_socket.name} for i in n.inputs for l in i.links]})
    report["materials"].append({"name": mat.name, "nodes": nodes})
out = root / "Saved" / "cabin-source-report.json"
out.write_text(json.dumps(report, indent=2, default=str))
print("CABIN_REPORT", out, "objects", len(report["objects"]), "materials", len(report["materials"]))
