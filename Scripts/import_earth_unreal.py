"""Apply the supplied Earth texture maps and finish the acquired cabin map."""
import unreal
from pathlib import Path
root = Path(unreal.Paths.project_dir()).resolve()
source = root / "Assets/ThirdParty/Earth16K/GameCopy"
tools = unreal.AssetToolsHelpers.get_asset_tools()
library = unreal.EditorAssetLibrary
editing = unreal.MaterialEditingLibrary

def texture(name, normal=False, linear=False):
    path = "/Game/ThirdParty/Earth16K/" + Path(name).stem.replace("-", "_")
    if not library.does_asset_exist(path):
        task = unreal.AssetImportTask()
        task.filename = str(source / name)
        task.destination_path = "/Game/ThirdParty/Earth16K"
        task.destination_name = Path(path).name
        task.automated = True
        task.save = True
        tools.import_asset_tasks([task])
    result = unreal.load_asset(path)
    result.set_editor_property("max_texture_size", 8192 if "day" in name or "night" in name else 4096)
    if normal:
        result.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        result.set_editor_property("flip_green_channel", True)
    if normal or linear: result.set_editor_property("srgb", False)
    library.save_loaded_asset(result)
    return result

def set_texture(material, parameter, value, linear=False):
    for expr in editing.get_material_expressions(material):
        if isinstance(expr, unreal.MaterialExpressionTextureSampleParameter2D) and str(expr.get_editor_property("parameter_name")) == parameter:
            expr.set_editor_property("texture", value)
            if linear: expr.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
            return
    raise RuntimeError("Missing material texture parameter " + parameter)

earth = unreal.load_asset("/Game/Materials/M_Earth")
set_texture(earth, "DayTexture", texture("earth16-day.jpg"))
set_texture(earth, "NightTexture", texture("earth16-night.jpg"))
normal = editing.create_material_expression(earth, unreal.MaterialExpressionTextureSampleParameter2D)
normal.set_editor_property("parameter_name", "SurfaceNormal")
normal.set_editor_property("texture", texture("earth16-normal.jpg", normal=True))
normal.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
editing.connect_material_property(normal, "", unreal.MaterialProperty.MP_NORMAL)
rough = editing.create_material_expression(earth, unreal.MaterialExpressionTextureSampleParameter2D)
rough.set_editor_property("parameter_name", "SurfaceRoughness")
rough.set_editor_property("texture", texture("earth16-roughness.jpg", linear=True))
rough.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
editing.connect_material_property(rough, "R", unreal.MaterialProperty.MP_ROUGHNESS)
editing.recompile_material(earth)
library.save_loaded_asset(earth)
cloud = unreal.load_asset("/Game/Materials/M_Clouds")
set_texture(cloud, "CloudTexture", texture("earth16-clouds.jpg", linear=True), linear=True)
editing.recompile_material(cloud)
library.save_loaded_asset(cloud)

level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level.load_level("/Game/Maps/EndlessJourneyCabin")
for actor in actors.get_all_level_actors():
    if actor.get_actor_label().startswith("MASSX-RZ"):
        actor.set_actor_rotation(unreal.Rotator(yaw=-90), False)
    if isinstance(actor, unreal.PostProcessVolume):
        settings = actor.get_editor_property("settings")
        settings.set_editor_property("auto_exposure_min_brightness", 5)
        settings.set_editor_property("auto_exposure_max_brightness", 5)
        settings.set_editor_property("override_motion_blur_amount", True)
        settings.set_editor_property("motion_blur_amount", 0)
        actor.set_editor_property("settings", settings)

# The authored scene was designed for one camera. Seal its off-camera gaps.
cube = unreal.load_asset("/Engine/BasicShapes/Cube")
hull = unreal.load_asset("/Game/ThirdParty/EndlessJourney/Materials/M_SteelDark")
for position, size in [
    ((0,-0.09,0),(6.3,0.08,5.5)),
    ((-3.1,1.5,0),(0.05,3.2,5.5)), ((3.1,1.5,0),(0.05,3.2,5.5)),
    ((0,1.5,2.55),(6.3,3.2,0.05)),
    ((-2.12,1.5,-2.78),(1.85,3.2,0.05)), ((2.12,1.5,-2.78),(1.85,3.2,0.05)),
    ((0,0.39,-2.78),(2.4,0.96,0.05)), ((0,2.66,-2.78),(2.4,1.04,0.05)),
    ((0,3.2,0),(6.3,0.05,5.5))]:
    x,y,z = position
    sx,sy,sz = size
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-z*100,x*100,y*100))
    actor.set_actor_label("Outer hull seal")
    actor.static_mesh_component.set_static_mesh(cube)
    actor.static_mesh_component.set_material(0,hull)
    actor.set_actor_scale3d(unreal.Vector(sz,sx,sy))
level.save_current_level()
unreal.log("EARTH16_AND_CABIN_READY")
