"""Adapt the template idle into a relaxed, upright cabin stance.

Preserves the imported clip's small motion while centering it on the woman's
own reference posture and lowering her upper arms. The source clip is retained.
"""
import math
import unreal
L=unreal.EditorAssetLibrary
pose_api=unreal.AnimPoseExtensions
source=unreal.load_asset('/Game/Characters/Animations/A_Crew_Idle')
path='/Game/Characters/Animations/A_Crew_RelaxedIdle'
clip=unreal.load_asset(path) if L.does_asset_exist(path) else L.duplicate_asset(source.get_path_name().split('.')[0],path)
mesh=unreal.load_asset('/Game/Characters/SK_Crew_Aligned')
ref=pose_api.get_reference_pose(mesh.get_editor_property('skeleton'))
model=clip.get_editor_property('data_model_interface')
controller=clip.get_editor_property('controller')
if not controller:
    controller=unreal.new_object(unreal.AnimDataController,outer=clip)
    controller.set_model(model)
rate=model.get_frame_rate()
frames=model.get_number_of_keys()
step=rate.denominator/rate.numerator

# Quaternion operations use Unreal's xyzw representation.
def q(t): return (t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w)
def inv(a): return (-a[0],-a[1],-a[2],a[3])
def mul(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return (w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z)
def norm(a):
 n=math.sqrt(sum(x*x for x in a));return tuple(x/n for x in a)
def xyz(v):return (v.x,v.y,v.z)
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def between(a,b):
 a=norm(a);b=norm(b)
 cross=(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
 return norm((*cross,1+sum(x*y for x,y in zip(a,b))))
def bone(name,world=False):
 return pose_api.get_bone_pose(ref,name,unreal.AnimPoseSpaces.WORLD if world else unreal.AnimPoseSpaces.LOCAL)

bones=['Hips','Spine','Spine1','Spine2','Neck','Head',
 'LeftShoulder','RightShoulder','LeftArm','RightArm','LeftForeArm','RightForeArm','LeftHand','RightHand',
 'LeftUpLeg','RightUpLeg','LeftLeg','RightLeg','LeftFoot','RightFoot','LeftToeBase','RightToeBase']
poses=[pose_api.get_anim_pose_at_time(source,i*step,unreal.AnimPoseEvaluationOptions()) for i in range(frames)]
tracks={name:[pose_api.get_bone_pose(p,name,unreal.AnimPoseSpaces.LOCAL) for p in poses] for name in bones}
neutral={name:q(bone(name)) for name in bones}
for side in ['Left','Right']:
 upper=bone(side+'Arm',True); lower=bone(side+'ForeArm',True);hand=bone(side+'Hand',True)
 sign=1 if lower.translation.x-upper.translation.x>0 else -1
 upper_rot=mul(between(sub(xyz(lower.translation),xyz(upper.translation)),(sign*0.10,0.025,-1)),q(upper))
 lower_rot=mul(between(sub(xyz(hand.translation),xyz(lower.translation)),(sign*0.05,0.16,-1)),q(lower))
 neutral[side+'Arm']=mul(inv(q(bone(side+'Shoulder',True))),upper_rot)
 neutral[side+'ForeArm']=mul(inv(upper_rot),lower_rot)

controller.open_bracket('Relax cabin idle posture',False)
for name,keys in tracks.items():
 first=keys[0];r=bone(name);positions=[];rotations=[];scales=[]
 if name=='Hips':
  # Retargeted clips normalize the extra FBX armature root to the origin.
  # The reference skeleton stores the pelvis height on that parent instead.
  # Preserve the neutral pelvis's component-space height in this clip.
  r.translation=bone(name,True).translation
 correction=mul(neutral[name],inv(q(first)))
 for k in keys:
  # Reference translations preserve the body's own proportions. The original
  # breathing/weight shift remains small enough for a quiet standing pose.
  movement=0.18 if name=='Hips' else 0.4
  positions.append(unreal.Vector(r.translation.x+(k.translation.x-first.translation.x)*movement,
                                 r.translation.y+(k.translation.y-first.translation.y)*movement,
                                 r.translation.z+(k.translation.z-first.translation.z)*movement))
  rotation=norm(mul(correction,q(k)))
  rotations.append(unreal.Quat(*rotation));scales.append(r.scale3d)
 if not controller.set_bone_track_keys(name,positions,rotations,scales,False):
  raise RuntimeError('Could not update idle bone '+name)
controller.close_bracket(False)
L.save_loaded_asset(clip)
unreal.log('RELAXED_CREW_IDLE_SAVED '+str(frames))
# The walk keeps its leg motion and pelvis translation. Relax only its
# upper-body center pose so it blends naturally with the quiet cabin idle.
walk_source=unreal.load_asset('/Game/Characters/Animations/A_Crew_Walk')
walk_path='/Game/Characters/Animations/A_Crew_RelaxedWalk'
walk=unreal.load_asset(walk_path) if L.does_asset_exist(walk_path) else L.duplicate_asset(walk_source.get_path_name().split('.')[0],walk_path)
walk_model=walk.get_editor_property('data_model_interface')
walk_controller=walk.get_editor_property('controller')
if not walk_controller: walk_controller=unreal.new_object(unreal.AnimDataController,outer=walk)
walk_controller.set_model(walk_model)
walk_rate=walk_model.get_frame_rate();walk_step=walk_rate.denominator/walk_rate.numerator
walk_poses=[pose_api.get_anim_pose_at_time(walk_source,i*walk_step,unreal.AnimPoseEvaluationOptions()) for i in range(walk_model.get_number_of_keys())]
walk_controller.open_bracket('Relax walking upper body',False)
for name in bones:
 if name=='Hips' or 'Leg' in name or 'Foot' in name or 'Toe' in name: continue
 keys=[pose_api.get_bone_pose(p,name,unreal.AnimPoseSpaces.LOCAL) for p in walk_poses]
 correction=mul(neutral[name],inv(q(keys[0])))
 walk_controller.set_bone_track_keys(name,[k.translation for k in keys],
   [unreal.Quat(*norm(mul(correction,q(k)))) for k in keys],[k.scale3d for k in keys],False)
walk_controller.close_bracket(False);L.save_loaded_asset(walk)

blend_path='/Game/Characters/Animations/BS_Crew_Locomotion'
if L.does_asset_exist(blend_path):
 blend=unreal.load_asset(blend_path)
else:
 factory=unreal.BlendSpaceFactory1D()
 factory.target_skeleton=mesh.get_editor_property('skeleton');factory.preview_skeletal_mesh=mesh
 blend=unreal.AssetToolsHelpers.get_asset_tools().create_asset('BS_Crew_Locomotion','/Game/Characters/Animations',unreal.BlendSpace1D,factory)
parameters=list(blend.get_editor_property('blend_parameters'))
parameter=parameters[0]
parameter.set_editor_property('display_name','Speed')
parameter.set_editor_property('min',0);parameter.set_editor_property('max',270)
parameter.set_editor_property('grid_num',9);parameter.set_editor_property('snap_to_grid',False)
parameters[0]=parameter;blend.set_editor_property('blend_parameters',parameters)
samples=[]
for animation,speed in [(clip,0),(walk,150),(unreal.load_asset('/Game/Characters/Animations/A_Crew_Run'),270)]:
 sample=unreal.BlendSample()
 sample.set_editor_property('animation',animation);sample.set_editor_property('sample_value',unreal.Vector(speed,0,0))
 sample.set_editor_property('rate_scale',1)
 samples.append(sample)
blend.set_editor_property('sample_data',samples)
blend.set_editor_property('target_weight_interpolation_speed_per_sec',6.0)
unreal.OrbitalAssetLibrary.finalize_blend_space(blend)
L.save_loaded_asset(blend)
unreal.log('RELAXED_CREW_LOCOMOTION_SAVED '+str(blend))
unreal.SystemLibrary.quit_editor()
