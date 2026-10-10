#!/bin/zsh
set -euo pipefail
task_root="${0:A:h:h}"
task_engine="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"
task_xcode="$(xcode-select -p)"
if [[ "$task_xcode" != *Xcode*.app/Contents/Developer ]]; then
  print -u2 "Full Xcode is required. Install an Epic-compatible Xcode version and select it with xcode-select."
  exit 1
fi
if [[ ! -x "$task_engine/Engine/Build/BatchFiles/Mac/Build.sh" ]]; then
  print -u2 "Unreal Engine installation is not complete at $task_engine"
  exit 1
fi
"$task_engine/Engine/Build/BatchFiles/Mac/Build.sh" OrbitalHabitatEditor Mac Development "$task_root/OrbitalHabitat.uproject" -WaitMutex
print "C++ module built. Open the project and run Scripts/bootstrap_unreal.py in the editor Python console."
