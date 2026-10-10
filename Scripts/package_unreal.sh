#!/bin/zsh
set -euo pipefail
task_root="${0:A:h:h}"
task_engine="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"
"$task_engine/Engine/Build/BatchFiles/Mac/Build.sh" OrbitalHabitatEditor Mac Development "$task_root/OrbitalHabitat.uproject" -NoUBA -WaitMutex
# Finalize the bundle with Xcode outside Unreal's build executor. This avoids
# the failing nested Xcode pre-action in the installed engine/toolchain pair.
env UE_BUILD_FROM_XCODE=1 "$task_engine/Engine/Build/BatchFiles/Mac/Build.sh" OrbitalHabitat Mac Development "$task_root/OrbitalHabitat.uproject" -NoUBA -WaitMutex
task_workspace="$task_root/Intermediate/ProjectFiles/OrbitalHabitat_Mac_OrbitalHabitat.xcworkspace"
if [[ ! -d "$task_workspace" ]]; then
  "$task_engine/Engine/Build/BatchFiles/Mac/GenerateProjectFiles.sh" "-project=$task_root/OrbitalHabitat.uproject" -game -platforms=Mac -DeployOnly -NoIntellisense -NoDotNet -projectfileformat=XCode
  task_workspace="$task_root/Intermediate/ProjectFiles/OrbitalHabitat_Mac.xcworkspace"
fi
xcodebuild build -workspace "$task_workspace" -scheme OrbitalHabitat -configuration Development \
  -destination 'generic/platform=macOS' UE_XCODE_BUILD_MODE=PostBuildSync CODE_SIGN_IDENTITY=- CODE_SIGN_STYLE=Manual
"$task_engine/Engine/Build/BatchFiles/RunUAT.sh" BuildCookRun \
  "-project=$task_root/OrbitalHabitat.uproject" -platform=Mac -architecture=arm64 \
  -clientconfig=Development -skipbuild -cook -stage -pak \
  -unattended -nop4 -utf8output
mkdir -p "$task_root/Build/UnrealMac/Mac"
ditto "$task_root/Saved/StagedBuilds/Mac/OrbitalHabitat.app" "$task_root/Build/UnrealMac/Mac/OrbitalHabitat.app"
print "Packaged $task_root/Build/UnrealMac/Mac/OrbitalHabitat.app"
