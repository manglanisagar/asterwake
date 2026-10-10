"""Restore GLB color maps, unify retarget axes, and import the supplied planet."""
import unreal
from pathlib import Path
root = Path(unreal.Paths.project_dir()).resolve()
assets = unreal.AssetToolsHelpers.get_asset_tools()
library = unreal.EditorAssetLibrary
editing = unreal.MaterialEditingLibrary

def import_file(filename, path, name, options=None, replace=False):
    task=unreal.AssetImportTask()
    task.filename=str(filename); task.destination_path=path; task.destination_name=name
    task.automated=True; task.save=True; task.replace_existing=replace
    task.replace_existing_settings=replace
    if options:
        task.options=options; task.factory=unreal.FbxFactory()
    assets.import_asset_tasks([task])
    return unreal.load_asset(path+'/'+name)

unreal.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
options=unreal.FbxImportUI()
options.import_mesh=True; options.import_as_skeletal=True
options.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH
options.automated_import_should_detect_type=False
options.import_materials=False; options.import_textures=False; options.create_physics_asset=False
options.skeletal_mesh_import_data.import_rotation=unreal.Rotator()
options.skeletal_mesh_import_data.set_editor_property('update_skeleton_reference_pose',True)
crew=import_file(root/'Assets/Source/Crew-Unreal.fbx', '/Game/Characters', 'SK_Crew_Aligned', options, True)
unreal.log('CREW_IMPORT_BOUNDS '+str(crew.get_bounds()))

for part in ['body','head','opacity']:
    base='f007_'+part
    tex=import_file(root/'Assets/Source/CrewTextures'/(base+'_color.png'), '/Game/Characters/Textures', base+'_Color')
    tex.set_editor_property('never_stream',True)
    library.save_loaded_asset(tex)
    material=unreal.load_asset('/Game/Characters/'+base)
    editing.delete_all_material_expressions(material)
    sample=editing.create_material_expression(material,unreal.MaterialExpressionTextureSample)
    sample.texture=tex
    editing.connect_material_property(sample,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
    rough=editing.create_material_expression(material,unreal.MaterialExpressionConstant);rough.r=0.86
    editing.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
    material.set_editor_property('two_sided',True)
    material.set_editor_property('used_with_skeletal_mesh',True)
    if part=='opacity':
        material.set_editor_property('blend_mode',unreal.BlendMode.BLEND_MASKED)
        editing.connect_material_property(sample,'A',unreal.MaterialProperty.MP_OPACITY_MASK)
    else:
        normal=unreal.load_asset('/Game/Characters/'+base+'_normal')
        if normal:
            normal.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
            normal.set_editor_property('srgb',False);normal.set_editor_property('flip_green_channel',True)
            library.save_loaded_asset(normal)
            n=editing.create_material_expression(material,unreal.MaterialExpressionTextureSample)
            n.texture=normal;n.sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
            editing.connect_material_property(n,'RGB',unreal.MaterialProperty.MP_NORMAL)
    editing.recompile_material(material);library.save_loaded_asset(material)
    unreal.log('CREW_TEXTURE_RESTORED '+base)

slots=[]
for slot in crew.get_editor_property('materials'):
    name=str(slot.get_editor_property('material_slot_name'))
    material=unreal.load_asset('/Game/Characters/'+name)
    if not material: raise RuntimeError('Missing crew material '+name)
    slot.set_editor_property('material_interface',material)
    slots.append(slot)
crew.set_editor_property('materials',slots)
library.save_loaded_asset(crew)

exec((root/'Scripts/import_crew_unreal.py').read_text())

options=unreal.FbxImportUI()
options.import_mesh=True;options.import_as_skeletal=False
options.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
options.automated_import_should_detect_type=False
options.import_materials=False;options.import_textures=False
options.static_mesh_import_data.auto_generate_collision=False
options.static_mesh_import_data.generate_lightmap_u_vs=False
options.static_mesh_import_data.normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
planet=import_file(root/'Assets/ThirdParty/Earth16K/GameCopy/EarthSurface.fbx','/Game/ThirdParty/Earth16K','SM_EarthSurface',options)
planet.set_material(0,unreal.load_asset('/Game/Materials/M_Earth'))
library.save_loaded_asset(planet)
for path in library.list_assets('/Game/ThirdParty/Earth16K',recursive=True):
    texture=unreal.load_asset(path)
    if isinstance(texture,unreal.Texture2D):
        texture.set_editor_property('never_stream',True)
        library.save_loaded_asset(texture)
for name in ['M_Earth','M_Clouds']:
    material=unreal.load_asset('/Game/Materials/'+name)
    for e in editing.get_material_expressions(material):
        if isinstance(e,unreal.MaterialExpressionTextureSampleParameter2D):
            unreal.log('PLANET_TEXTURE '+name+' '+str(e.get_editor_property('parameter_name'))+' '+str(e.get_editor_property('texture')))
unreal.log('VISUAL_ASSETS_REPAIRED '+str(planet.get_bounds()))
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level.load_level('/Game/Maps/EndlessJourneyCabin')
for actor in actors.get_all_level_actors():
    if isinstance(actor,unreal.PlayerStart):
        actor.set_actor_rotation(unreal.Rotator(),False)
level.save_current_level()
unreal.SystemLibrary.quit_editor()
