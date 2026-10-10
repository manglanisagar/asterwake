"""Import the converted existing cabin and prepare its walkable Unreal map."""
import unreal
import json
import re
import math
from pathlib import Path

root = Path(unreal.Paths.project_dir()).resolve()
source = root / "Assets/ThirdParty/EndlessJourney/GameCopy"
data = json.loads((source / "manifest.json").read_text())
assets = unreal.AssetToolsHelpers.get_asset_tools()
edit = unreal.MaterialEditingLibrary
library = unreal.EditorAssetLibrary
directory = "/Game/ThirdParty/EndlessJourney"
library.make_directory(directory)

def safe(value): return re.sub(r"[^A-Za-z0-9_]", "_", value)
def texture(filename, channel):
    name = safe(Path(filename).stem) + ("_Normal" if channel == "Normal" and "Normal" not in filename else "")
    path = f"{directory}/Textures/{name}"
    if not library.does_asset_exist(path):
        task = unreal.AssetImportTask()
        task.filename = filename
        task.destination_path = directory + "/Textures"
        task.destination_name = name
        task.automated = True
        task.save = True
        assets.import_asset_tasks([task])
    result = unreal.load_asset(path)
    if channel in {"Normal", "Roughness", "Metallic"}:
        result.set_editor_property("srgb", False)
    if channel == "Normal":
        result.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        result.set_editor_property("flip_green_channel", True)
    result.set_editor_property("max_texture_size", 2048)
    library.save_loaded_asset(result)
    return result

def node(mat, cls, **values):
    result = edit.create_material_expression(mat, cls, -400, 0)
    for key, value in values.items(): result.set_editor_property(key, value)
    return result
def constant(mat, value):
    if isinstance(value, list):
        return node(mat, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(*value[:3], 1))
    return node(mat, unreal.MaterialExpressionConstant, r=float(value))

materials = {}
for name, spec in data["materials"].items():
    path = directory + "/Materials/M_" + safe(name)
    if library.does_asset_exist(path):
        mat = unreal.load_asset(path)
    else:
        mat = assets.create_asset("M_" + safe(name), directory + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
        for channel, key, prop in [("BaseColor", "base", unreal.MaterialProperty.MP_BASE_COLOR),
                                   ("Metallic", "metallic", unreal.MaterialProperty.MP_METALLIC),
                                   ("Roughness", "roughness", unreal.MaterialProperty.MP_ROUGHNESS),
                                   ("Normal", None, unreal.MaterialProperty.MP_NORMAL)]:
            if channel in spec["textures"]:
                tex = texture(spec["textures"][channel], channel)
                expr = node(mat, unreal.MaterialExpressionTextureSampleParameter2D, parameter_name=channel, texture=tex)
                if channel == "Normal": expr.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
                elif channel in {"Metallic", "Roughness"}: expr.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
            elif key:
                expr = constant(mat, spec[key])
            else:
                continue
            edit.connect_material_property(expr, "", prop)
        if spec["emission_strength"] > 0:
            color = node(mat, unreal.MaterialExpressionTextureSampleParameter2D, parameter_name="Emission", texture=texture(spec["textures"]["Emission"], "Emission")) if "Emission" in spec["textures"] else constant(mat, spec["emission"])
            strength = constant(mat, min(spec["emission_strength"], 8))
            mult = node(mat, unreal.MaterialExpressionMultiply)
            edit.connect_material_expressions(color, "", mult, "A")
            edit.connect_material_expressions(strength, "", mult, "B")
            edit.connect_material_property(mult, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        if spec["transparent"]:
            mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
            mat.set_editor_property("two_sided", True)
            edit.connect_material_property(constant(mat, 0.06), "", unreal.MaterialProperty.MP_OPACITY)
        if name in {"Leaves", "Vegetation", "Paper"}: mat.set_editor_property("two_sided", True)
        edit.recompile_material(mat)
        library.save_loaded_asset(mat)
    materials[name] = mat

mesh_path = directory + "/SM_EndlessJourneyCabin"
if not library.does_asset_exist(mesh_path):
    unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
    task = unreal.AssetImportTask()
    task.filename = str(source / "EndlessJourneyCabin.fbx")
    task.destination_path = directory
    task.destination_name = "SM_EndlessJourneyCabin"
    task.automated = True
    task.save = True
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("automated_import_should_detect_type", False)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    options.static_mesh_import_data.set_editor_property("generate_lightmap_u_vs", False)
    options.static_mesh_import_data.set_editor_property("auto_generate_collision", False)
    options.static_mesh_import_data.set_editor_property("normal_import_method", unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
    task.options = options
    task.factory = unreal.FbxFactory()
    assets.import_asset_tasks([task])
    unreal.log("CABIN_IMPORTED_PATHS " + str(task.imported_object_paths))
mesh = unreal.load_asset(mesh_path)
if not mesh: raise RuntimeError("Cabin mesh import did not create the expected asset")
slots = []
for slot in mesh.get_editor_property("static_materials"):
    name = str(slot.get_editor_property("imported_material_slot_name"))
    mat = materials.get(name) or next((m for n, m in materials.items() if safe(n) == name), None)
    if mat: slot.set_editor_property("material_interface", mat)
    else: unreal.log_warning("Unmatched source material: " + name)
    # Unreal arrays return copies of structs while iterating. Preserve the
    # edited copy explicitly before replacing the array in one rebuild.
    slots.append(slot)
mesh.set_editor_property("static_materials", slots)
mesh.get_editor_property("body_setup").set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
library.save_loaded_asset(mesh)
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level.new_level("/Game/Maps/EndlessJourneyCabin")
room = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector())
room.set_actor_label("MASSX-RZ — Endless Journey cabin")
room.static_mesh_component.set_static_mesh(mesh)
room.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
room.set_actor_rotation(unreal.Rotator(yaw=-90), False)
ship_class = unreal.load_class(None, "/Script/OrbitalHabitat.OrbitalWorld")
ship = actors.spawn_actor_from_class(ship_class, unreal.Vector())
ship.set_editor_property("build_blockout_interior", False)
ship.set_actor_label("Earth and orbital sky")
start = actors.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(-30, 0, 96), unreal.Rotator())
start.set_actor_label("Crew walking start")

# Use a few practical lights; emissive details remain in the imported artwork.
for name, position, color, intensity in [
    ("Ceiling practical", (-20, 0, 260), (0.85, 0.89, 1), 850),
    ("Cabin warm practical", (155, -200, 220), (1, 0.65, 0.45), 500),
    ("Earth window fill", (235, 0, 165), (0.3, 0.55, 1), 550),
    ("Entry practical", (-175, 0, 245), (0.85, 0.9, 1), 400)]:
    actor = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*position))
    actor.set_actor_label(name)
    light = actor.point_light_component
    light.set_mobility(unreal.ComponentMobility.MOVABLE)
    light.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
    light.set_editor_property("intensity", intensity)
    light.set_editor_property("attenuation_radius", 650)
    light.set_editor_property("light_color", unreal.LinearColor(*color, 1).to_color())
    light.set_editor_property("source_radius", 12)
    light.set_editor_property("cast_shadows", True)
post = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector())
post.set_editor_property("unbound", True)
settings = post.get_editor_property("settings")
settings.set_editor_property("override_auto_exposure_min_brightness", True)
settings.set_editor_property("auto_exposure_min_brightness", 5)
settings.set_editor_property("override_auto_exposure_max_brightness", True)
settings.set_editor_property("auto_exposure_max_brightness", 5)
settings.set_editor_property("override_bloom_intensity", True)
settings.set_editor_property("bloom_intensity", 0.15)
post.set_editor_property("settings", settings)
actors.set_actor_selection_state(room, True)
level.save_current_level()
library.save_directory(directory, only_if_is_dirty=True, recursive=True)
unreal.log("EXISTING_CABIN_MAP_READY /Game/Maps/EndlessJourneyCabin")
