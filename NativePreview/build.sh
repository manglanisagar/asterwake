#!/bin/zsh
set -euo pipefail
task_root="${0:A:h:h}"
task_app="$task_root/NativePreview/Build/Orbital Habitat.app"
task_developer="${PREVIEW_DEVELOPER_DIR:-/Library/Developer/CommandLineTools}"
mkdir -p "$task_app/Contents/MacOS" "$task_app/Contents/Resources" "$task_root/NativePreview/.build/module-cache"
env DEVELOPER_DIR="$task_developer" xcrun swiftc -swift-version 5 -O -module-cache-path "$task_root/NativePreview/.build/module-cache" \
  -framework AppKit -framework SceneKit -framework QuartzCore \
  "$task_root/NativePreview/Sources/GLBCharacter.swift" "$task_root/NativePreview/Sources/Main.swift" \
  -o "$task_app/Contents/MacOS/OrbitalHabitat"
cat > "$task_app/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>OrbitalHabitat</string>
<key>CFBundleIdentifier</key><string>local.orbitalhabitat.preview</string>
<key>CFBundleName</key><string>Orbital Habitat</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>0.1.0</string>
<key>LSMinimumSystemVersion</key><string>14.0</string>
<key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
mkdir -p "$task_app/Contents/Resources/Assets/Source" "$task_app/Contents/Resources/Assets/Textures"
cp "$task_root/Assets/layout.json" "$task_app/Contents/Resources/Assets/layout.json"
ditto "$task_root/Assets/Textures" "$task_app/Contents/Resources/Assets/Textures"
for task_file in Crew.glb Rocketbox-LICENSE.txt avatar-conversion-LICENSE.txt avatar-LICENSE.md; do
  cp "$task_root/Assets/Source/$task_file" "$task_app/Contents/Resources/Assets/Source/$task_file"
done
if [[ -f "$task_root/Assets/ThirdParty/EndlessJourney/GameCopy/EndlessJourneyCabin.glb" ]]; then
  cp "$task_root/Assets/ThirdParty/EndlessJourney/GameCopy/EndlessJourneyCabin.glb" "$task_app/Contents/Resources/Assets/Source/EndlessJourneyCabin.glb"
fi
if [[ -d "$task_root/Assets/ThirdParty/Earth16K/GameCopy" ]]; then
  ditto "$task_root/Assets/ThirdParty/Earth16K/GameCopy" "$task_app/Contents/Resources/Assets/Textures"
fi
codesign --force --deep --sign - "$task_app"
print "Built $task_app"
