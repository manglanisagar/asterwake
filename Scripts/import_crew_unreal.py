"""Import the existing Rocketbox woman and retarget Epic's existing locomotion."""
import unreal
from pathlib import Path
root = Path(unreal.Paths.project_dir()).resolve()
library = unreal.EditorAssetLibrary
assets = unreal.AssetToolsHelpers.get_asset_tools()
directory = "/Game/Characters"
library.make_directory(directory)
unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous(["/Game/Mannequin"], True)

if not library.does_asset_exist(directory + "/SK_Crew"):
    unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
    task = unreal.AssetImportTask()
    task.filename = str(root / "Assets/Source/Crew-Unreal.fbx")
    task.destination_path = directory
    task.destination_name = "SK_Crew"
    task.automated = True
    task.save = True
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    options.set_editor_property("automated_import_should_detect_type", False)
    options.set_editor_property("import_materials", True)
    options.set_editor_property("import_textures", True)
    options.set_editor_property("create_physics_asset", False)
    # Match Epic's source skeleton's +Y forward basis. The character component
    # applies -90 degrees at runtime to face Unreal's gameplay +X direction.
    options.skeletal_mesh_import_data.set_editor_property("import_rotation", unreal.Rotator())
    task.options = options
    task.factory = unreal.FbxFactory()
    assets.import_asset_tasks([task])
    unreal.log("CREW_IMPORTED " + str(task.imported_object_paths))

source = unreal.load_asset("/Game/Mannequin/Character/Mesh/SK_Mannequin")
target = unreal.load_asset(directory + "/SK_Crew_Aligned") or unreal.load_asset(directory + "/SK_Crew")
if not source or not target: raise RuntimeError("Source or target character mesh missing")

source_chains = {
    "Spine": ("spine_01", "spine_03"), "Head": ("neck_01", "head"),
    "LeftArm": ("upperarm_l", "hand_l"), "RightArm": ("upperarm_r", "hand_r"),
    "LeftLeg": ("thigh_l", "ball_l"), "RightLeg": ("thigh_r", "ball_r"),
    "LeftClavicle": ("clavicle_l", "clavicle_l"), "RightClavicle": ("clavicle_r", "clavicle_r")}
target_chains = {
    "Spine": ("Spine", "Spine2"), "Head": ("Neck", "Head"),
    "LeftArm": ("LeftArm", "LeftHand"), "RightArm": ("RightArm", "RightHand"),
    "LeftLeg": ("LeftUpLeg", "LeftToeBase"), "RightLeg": ("RightUpLeg", "RightToeBase"),
    "LeftClavicle": ("LeftShoulder", "LeftShoulder"), "RightClavicle": ("RightShoulder", "RightShoulder")}

def rig(name, mesh, pelvis, chains):
    path = directory + "/" + name
    if library.does_asset_exist(path):
        asset = unreal.load_asset(path)
        unreal.IKRigController.get_controller(asset).set_skeletal_mesh(mesh)
        return asset
    asset = assets.create_asset(name, directory, unreal.IKRigDefinition, unreal.IKRigDefinitionFactory())
    controller = unreal.IKRigController.get_controller(asset)
    controller.set_skeletal_mesh(mesh)
    controller.set_retarget_root(pelvis)
    for chain, (start, end) in chains.items(): controller.add_retarget_chain(chain, start, end, "None")
    library.save_loaded_asset(asset)
    return asset

src_rig = rig("IK_MannequinSource", source, "pelvis", source_chains)
dst_rig = rig("IK_Crew", target, "Hips", target_chains)
path = directory + "/RTG_MannequinToCrew"
if library.does_asset_exist(path):
    retargeter = unreal.load_asset(path)
else:
    retargeter = assets.create_asset("RTG_MannequinToCrew", directory, unreal.IKRetargeter, unreal.IKRetargetFactory())
    controller = unreal.IKRetargeterController.get_controller(retargeter)
    controller.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src_rig)
    controller.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, dst_rig)
    controller.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, source)
    controller.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, target)
    controller.add_default_ops()
    controller.auto_map_chains(unreal.AutoMapChainType.EXACT, True)
    controller.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
    library.save_loaded_asset(retargeter)

controller = unreal.IKRetargeterController.get_controller(retargeter)
controller.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, source)
controller.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, target)
for side in [unreal.RetargetSourceOrTarget.SOURCE, unreal.RetargetSourceOrTarget.TARGET]:
    controller.reset_retarget_pose(controller.get_current_retarget_pose_name(side), [], side)
controller.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
library.save_loaded_asset(retargeter)

inputs = unreal.IKRetargetBatchOperationInputs()
inputs.set_editor_property("assets_to_retarget", [library.find_asset_data("/Game/Mannequin/Animations/ThirdPerson" + name) for name in ["Idle", "Walk", "Run"]])
inputs.set_editor_property("source_mesh", source)
inputs.set_editor_property("target_mesh", target)
inputs.set_editor_property("ik_retarget_asset", retargeter)
inputs.set_editor_property("search", "ThirdPerson")
inputs.set_editor_property("replace", "A_Crew_")
inputs.set_editor_property("target_path", directory + "/Animations")
inputs.set_editor_property("include_referenced_assets", False)
inputs.set_editor_property("overwrite_existing_files", True)
result = unreal.IKRetargetBatchOperation.run_batch_retarget(inputs)
library.save_directory(directory, only_if_is_dirty=True, recursive=True)
unreal.log("CREW_LOCOMOTION_READY " + str([str(r.package_name) for r in result]))
