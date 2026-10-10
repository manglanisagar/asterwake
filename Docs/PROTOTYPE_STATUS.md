# Prototype status — October 10, 2026

## Complete

- Installed Unreal 5.8, full Xcode and Apple's Metal toolchain on this M4 Mac.
- Preserved the user-supplied cabin and Earth originals and their provenance.
- Converted the existing cabin's PBR materials and reduced its evaluated
  geometry from approximately 13.6 million to 2.2 million polygons.
- Imported the cabin into Unreal, sealed the gaps outside its presentation
  camera, and set the walking start and Earth-facing camera direction.
- Prepared 8K day/night and 4K cloud/normal/roughness maps from the supplied
  Earth package; imported them into the native preview and Unreal.
- Imported the existing Rocketbox female character and retargeted Epic's
  existing idle, walk and run animation clips to her skeleton.
- Added mouse release/recapture, camera switching, lighting and night presets.
- Built a complete standalone Unreal Mac app with cooked runtime assets.
- Corrected the cabin's material slot assignments, including transparent glass.
- Restored the woman's original body, face and hair color maps; imported a
  fresh mesh in the animation source's coordinate system and retargeted again.
- Replaced Unreal's coarse default planet sphere with the supplied Earth
  geometry and kept its hero texture maps resident at their prepared sizes.
- Adapted the standing and walking upper body for a relaxed cabin posture;
  added locomotion blending and turning toward the movement direction.
- Inspected the corrected running Unreal app from the back and side. Captured
  the actual game window in `Docs/unreal-cabin-preview.jpg` and the upright
  side profile in `Docs/unreal-character-stance.jpg`.
- Updated the separate native Mac preview and captured its actual render in
  `Docs/existing-cabin-preview.png`.

## Pending

- Tune lighting/materials against the original generated reference. Current
  art and the temporary character do not constitute final photorealism.
- Add connecting doors and additional functional rooms using matching assets.
- Profile and optimize the M1/iPad version; no M1 frame-rate claim is validated.

No paid assets were purchased. No unit-test suite was added or run.
