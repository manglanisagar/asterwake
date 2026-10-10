# Asterwake

A Mac-first spaceship prototype inspired by the cabin concept in
`Reference/cabin-visual-target.png`.

The Unreal target, source module and app bundle currently retain the internal
name `OrbitalHabitat`.

## Repository and local assets

Git tracks the source, configuration, conversion scripts, small project-owned
Unreal maps/materials, reference image and current screenshots. Downloaded art,
large texture/mesh assets, tools, caches and built applications stay local.
A fresh clone needs those local asset folders restored before it can run the
acquired cabin scene. See [Local asset setup](Docs/LOCAL_ASSETS.md).

## What you can run now

**Build/UnrealMac/Mac/OrbitalHabitat.app** is the standalone Apple Silicon
Unreal build. It contains the existing cabin, the supplied Earth maps and the
Rocketbox woman with Epic's retargeted idle/walk/run motions. It uses local
signing and needs no developer account to run on this Mac. The imported color
maps, smoother Earth geometry and relaxed locomotion are included in the build.

Unreal controls: WASD move, mouse look, Shift faster, V camera, R reset,
L lighting, N day/night, Escape release mouse, click recapture. Cmd-Q quits.
The acquired cabin currently contains one room; its authored entry door is
not yet connected to another room.

**NativePreview/Build/Orbital Habitat.app** is a native Apple Silicon app using
SceneKit over Metal. It is an independently playable visual and movement
prototype, not the final Unreal build. No full Xcode installation is needed
to rebuild it with the installed Swift command-line tools.

The current preview uses MASSX-RZ's existing **Endless Journey** cabin: a bed,
workstation, storage, sink, detailed fittings and Earth-facing window. It uses
the supplied **Earth 16k** asset's maps, prepared at 8K/4K runtime sizes.
This acquired-art scene currently contains one walkable room. The earlier
procedural layout remains available in the source and `OrbitalCabin` map.
The female protagonist is a free Microsoft
Rocketbox-derived rigged avatar. It remains a temporary production asset.

### Controls

| Input | Action |
| --- | --- |
| WASD or arrow keys | Walk |
| Shift | Walk faster |
| Click | Capture the mouse for looking |
| Drag or right drag | Look without locking the cursor |
| Escape | Release the cursor |
| V | First person / third person |
| E | Door interaction in the earlier procedural layout |
| L | Dim cabin lights |
| O | Window shutter in the earlier procedural layout |
| N | Day / night lighting preset |
| Q | High / balanced rendering |
| P | Actual SceneKit renderer statistics |
| R | Reset position and view |
| H | Hide or show overlay |
| Mouse wheel | Adjust third person camera distance |
| Cmd-Q | Quit |

To see the sky: use N for night, L to dim the cabin, then look away from Earth
toward dark space. The star field fades in rather than appearing at full
brightness over daylight Earth.

Rebuild from the project folder:

```sh
NativePreview/build.sh
```

The texture preparation script needs Pillow. It was run using the bundled
Codex Python runtime. Prepared assets are included, so it need not run to
rebuild the app. `Scripts/make_layout.py` regenerates the shared layout.

## Unreal project

`OrbitalHabitat.uproject` targets UE 5.8. The C++ project reads the same ship
layout and provides walking, collision, a camera toggle, door/shutter movement,
and lighting presets. **The C++ editor module builds successfully with the
installed UE 5.8 and Xcode 27.0.** The bootstrap script has run successfully,
creating the startup map and Earth/material assets. The acquired cabin and
supplied Earth maps are imported into `/Game/Maps/EndlessJourneyCabin`, which is
the new default map. The Unreal renderer starts with the installed Metal
toolchain. Packaging uses local Mac signing without a developer account.

1. Run `Scripts/build_unreal.sh` after editing C++.
2. Open the `.uproject` in Unreal Editor. The map and materials are already
   generated. To regenerate missing assets, run `Scripts/bootstrap_unreal.py`
   from the editor Python console.
3. The woman and locomotion clips are already imported. If regenerating them,
   run `Scripts/import_crew_unreal.py` after preparing `Crew-Unreal.fbx` and
   copying Epic's standard Mannequin content. `Scripts/repair_visual_assets_unreal.py`
   creates the aligned mesh and restores its original embedded color maps.
   This retargets Epic's existing idle, walk and run clips to
   `/Game/Characters/Animations`. `Scripts/relax_crew_idle_unreal.py` adapts
   the upright standing posture, lowers the arms and builds a locomotion blend
   space. Third-person movement turns the woman toward her travel direction.
4. The existing artwork is already imported. `Scripts/prepare_cabin.py` exports
   a separate optimized copy; `Scripts/import_cabin_unreal.py` assembles its
   Unreal map; `Scripts/import_earth_unreal.py` applies the supplied Earth maps.
   `Scripts/prepare_earth_mesh.py` exports the supplied planet's smoother geometry.
   See `Docs/EXISTING_ASSETS.md` for provenance and other candidates.
5. `Scripts/finish_cabin_unreal.py` applies material slot corrections and the
   starting camera position to the existing map. Press Play to view the room.

Rebuild the standalone app with `Scripts/package_unreal.sh`. The script builds
the C++ modules, finalizes the local app with Xcode, cooks the assets, and copies
the complete staged bundle into `Build/UnrealMac/Mac`. Original FBX/Blender
source files are excluded from that Unreal bundle.

`Tools/Blender.app` is the official Apple Silicon Blender 5.2.2 LTS build,
downloaded for inspecting and converting existing artwork. Its Blender
Foundation code signature is valid, and its background Python runtime starts.

Mac and iPad rendering profiles are included, but the iPad profile is a starting
configuration only. No iPad build or M1 performance claim has been validated.

## Current limits

- The cabin now uses existing detailed artwork with converted PBR materials.
  Lighting, material fidelity, additional rooms and the final character remain
  production work. It does not yet match the generated concept's photorealism.
- The native avatar has a simple procedural gait. Foot planting, interactions,
  custom clothing, hair and facial animation need production animation work.
- Earth is staged at a scaled distance for the cabin composition. The day/night
  controls are visual presets, not an orbital mechanics simulation. The
  interior currently uses a fixed gravity direction.
- Stars are an artistic sky texture; they are not a calibrated star catalogue.
- The native preview and Unreal project share assets/layout, not rendering or
  movement source. Future feature work belongs in Unreal after setup completes.
- There is no crew AI, planetary landing, or colony simulation in this slice.

See `Docs/ASSET_CREDITS.md` for asset provenance and licenses.
