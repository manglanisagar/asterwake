"""Inspect the supplied planet asset with Blender auto execution disabled."""
import bpy
import json
from pathlib import Path
report = {"objects": [], "images": [], "texts": []}
for obj in bpy.data.objects:
    report["objects"].append({"name": obj.name, "type": obj.type,
                              "polygons": len(obj.data.polygons) if obj.type == "MESH" else None,
                              "materials": [s.material.name if s.material else None for s in obj.material_slots],
                              "dimensions": list(obj.dimensions)})
for image in bpy.data.images:
    report["images"].append({"name": image.name, "file": image.filepath,
                             "packed": bool(image.packed_file), "size": list(image.size)})
for text in bpy.data.texts:
    report["texts"].append({"name": text.name, "auto_run": text.use_module,
                            "length": len(text.as_string())})
out = Path(__file__).resolve().parents[1]/"Saved/earth-source-report.json"
out.write_text(json.dumps(report, indent=2))
print("EARTH_SOURCE_REPORT", json.dumps(report))
