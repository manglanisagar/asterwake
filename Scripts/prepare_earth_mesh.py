"""Export the downloaded Earth geometry at Unreal's 50 cm reference radius."""
import bpy
from pathlib import Path
root = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root / 'Assets/ThirdParty/Earth16K/Original/earth.blend'))
bpy.ops.object.select_all(action='DESELECT')
mesh = bpy.data.objects['Sphere.001']
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh
# Preserve the source UVs and normals; normalize around the planet center.
mesh.location = (0, 0, 0)
mesh.rotation_euler = (0, 0, 0)
mesh.scale = (0.5, 0.5, 0.5)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
bpy.ops.export_scene.fbx(filepath=str(root / 'Assets/ThirdParty/Earth16K/GameCopy/EarthSurface.fbx'), use_selection=True, object_types={'MESH'}, axis_forward='-Y', axis_up='Z', bake_anim=False, path_mode='AUTO')
print('EARTH_MESH_EXPORTED', len(mesh.data.polygons), tuple(mesh.dimensions))
