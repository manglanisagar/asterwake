"""Run in Unreal Editor's Python console after building the project's C++ module.

exec(open('/Users/sagarmanglani/Projects/OrbitalHabitat/Scripts/bootstrap_unreal.py').read())

Creates project-owned material assets and the empty startup map. Runtime C++
builds the ship from Assets/layout.json. Successfully executed with the installed
UE 5.8 editor; the complete room still awaits production artwork integration.
"""
import unreal
from pathlib import Path

root=Path(unreal.Paths.project_dir()).resolve()
tools=unreal.AssetToolsHelpers.get_asset_tools()
editing=unreal.MaterialEditingLibrary

for path in ['/Game/Maps','/Game/Materials','/Game/Textures','/Game/Characters']:
    unreal.EditorAssetLibrary.make_directory(path)

def texture(filename):
    name=Path(filename).stem.replace('-','_')
    path=f'/Game/Textures/{name}'
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        task=unreal.AssetImportTask()
        task.filename=str(root/'Assets'/'Textures'/filename)
        task.destination_path='/Game/Textures';task.destination_name=name
        task.automated=True;task.save=True;task.replace_existing=False
        tools.import_asset_tasks([task])
    return unreal.load_asset(path)

def material(name):
    path=f'/Game/Materials/{name}'
    if unreal.EditorAssetLibrary.does_asset_exist(path):return None
    return tools.create_asset(name,'/Game/Materials',unreal.Material,unreal.MaterialFactoryNew())

def expression(m,cls,x=0,y=0,**values):
    e=editing.create_material_expression(m,cls,x,y)
    for key,value in values.items():e.set_editor_property(key,value)
    return e

def wire(source,target,input_name=''):
    editing.connect_material_expressions(source,'',target,input_name)

def output(e,m,prop):editing.connect_material_property(e,'',prop)
def save(m):
    editing.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)

m=material('M_Base')
if m:
    base=expression(m,unreal.MaterialExpressionVectorParameter,-400,0,parameter_name='BaseColor',default_value=unreal.LinearColor(0.65,0.65,0.65,1))
    rough=expression(m,unreal.MaterialExpressionScalarParameter,-400,180,parameter_name='Roughness',default_value=0.65)
    metal=expression(m,unreal.MaterialExpressionScalarParameter,-400,300,parameter_name='Metallic',default_value=0.1)
    emiss=expression(m,unreal.MaterialExpressionVectorParameter,-400,420,parameter_name='Emission',default_value=unreal.LinearColor(0,0,0,1))
    output(base,m,unreal.MaterialProperty.MP_BASE_COLOR)
    output(rough,m,unreal.MaterialProperty.MP_ROUGHNESS)
    output(metal,m,unreal.MaterialProperty.MP_METALLIC)
    output(emiss,m,unreal.MaterialProperty.MP_EMISSIVE_COLOR);save(m)

m=material('M_Earth')
if m:
    day=expression(m,unreal.MaterialExpressionTextureSampleParameter2D,-600,0,parameter_name='DayTexture',texture=texture('earth-day.jpg'))
    night=expression(m,unreal.MaterialExpressionTextureSampleParameter2D,-600,250,parameter_name='NightTexture',texture=texture('earth-night.jpg'))
    mode=expression(m,unreal.MaterialExpressionScalarParameter,-600,450,parameter_name='NightMode',default_value=0)
    multiply=expression(m,unreal.MaterialExpressionMultiply,-150,250)
    wire(night,multiply,'A');wire(mode,multiply,'B')
    rough=expression(m,unreal.MaterialExpressionConstant,-150,0,r=0.85)
    output(day,m,unreal.MaterialProperty.MP_BASE_COLOR)
    output(multiply,m,unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    output(rough,m,unreal.MaterialProperty.MP_ROUGHNESS);save(m)

m=material('M_Clouds')
if m:
    m.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
    mask=expression(m,unreal.MaterialExpressionTextureSampleParameter2D,-400,0,parameter_name='CloudTexture',texture=texture('earth-clouds.jpg'))
    white=expression(m,unreal.MaterialExpressionConstant3Vector,-400,250,constant=unreal.LinearColor(1,1,1,1))
    editing.connect_material_property(mask,'R',unreal.MaterialProperty.MP_OPACITY)
    output(white,m,unreal.MaterialProperty.MP_BASE_COLOR);save(m)

m=material('M_Atmosphere')
if m:
    m.set_editor_property('blend_mode',unreal.BlendMode.BLEND_ADDITIVE)
    m.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    fresnel=expression(m,unreal.MaterialExpressionFresnel,-500,0,exponent=5,base_reflect_fraction=0.0)
    blue=expression(m,unreal.MaterialExpressionConstant3Vector,-500,200,constant=unreal.LinearColor(0.06,0.30,0.85,1))
    glow=expression(m,unreal.MaterialExpressionMultiply,-100,100)
    wire(fresnel,glow,'A');wire(blue,glow,'B')
    output(glow,m,unreal.MaterialProperty.MP_EMISSIVE_COLOR);save(m)

m=material('M_Stars')
if m:
    m.set_editor_property('two_sided',True)
    m.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    stars=expression(m,unreal.MaterialExpressionTextureSampleParameter2D,-500,0,parameter_name='StarTexture',texture=texture('stars-milky-way.jpg'))
    strength=expression(m,unreal.MaterialExpressionScalarParameter,-500,250,parameter_name='Brightness',default_value=0.003)
    product=expression(m,unreal.MaterialExpressionMultiply,-100,0)
    wire(stars,product,'A');wire(strength,product,'B')
    output(product,m,unreal.MaterialProperty.MP_EMISSIVE_COLOR);save(m)

# The free character GLB is ready for Interchange import. Import manually and
# name the resulting skeletal mesh /Game/Characters/SK_Crew; create its walking
# animation blueprint before treating the Unreal character as finished.
if not unreal.EditorAssetLibrary.does_asset_exist('/Game/Maps/OrbitalCabin'):
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).new_level('/Game/Maps/OrbitalCabin')
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
unreal.log('Orbital materials and startup map prepared. Press Play to spawn the ship.')
