"""Apply material slot corrections to the existing map without reimporting it."""
import unreal
import re

library = unreal.EditorAssetLibrary
directory = "/Game/ThirdParty/EndlessJourney"
mesh = unreal.load_asset(directory + "/SM_EndlessJourneyCabin")
slots = []
for slot in mesh.get_editor_property("static_materials"):
    name = str(slot.get_editor_property("imported_material_slot_name"))
    safe = re.sub(r"[^A-Za-z0-9_]", "_", name)
    material = unreal.load_asset(directory + "/Materials/M_" + safe)
    if not material:
        raise RuntimeError("Missing cabin material " + name)
    slot.set_editor_property("material_interface", material)
    slots.append(slot)
mesh.set_editor_property("static_materials", slots)
library.save_loaded_asset(mesh)
unreal.log("CABIN_MATERIAL_SLOTS_SAVED " + str(len(slots)))

level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level.load_level("/Game/Maps/EndlessJourneyCabin")
for actor in actors.get_all_level_actors():
    if isinstance(actor, unreal.PlayerStart):
        actor.set_actor_location(unreal.Vector(-30, 0, 96), False, False)
        actor.set_actor_rotation(unreal.Rotator(), False)
level.save_current_level()

# Log the imported skeletal pose while finishing this conversion so that
# unexpected translation/scale can be diagnosed before the next app build.
for name in ["Idle", "Walk", "Run"]:
    animation = unreal.load_asset("/Game/Characters/Animations/A_Crew_" + name)
    pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(animation, 0.0, unreal.AnimPoseEvaluationOptions())
    for bone in ["Hips", "Head", "LeftFoot", "RightFoot"]:
        transform = unreal.AnimPoseExtensions.get_bone_pose(pose, bone, unreal.AnimPoseSpaces.WORLD)
        unreal.log("CREW_POSE " + name + " " + bone + " " + str(transform))
unreal.SystemLibrary.quit_editor()
