# Local assets and rebuilding

Asterwake's Git repository contains code and project setup. The downloaded
asset library and application builds are excluded from Git. No Git LFS files
or external asset uploads are part of this checkpoint.

## Keep these folders on this Mac or in a private backup

| Folder | Contents |
| --- | --- |
| `Assets/Source` | Original Earth/sky images, character GLB/FBX and extracted character maps; small license files remain tracked |
| `Assets/Textures` | Prepared textures for the native preview and earlier Unreal scene |
| `Assets/ThirdParty/EndlessJourney` | Downloaded cabin originals, textures, optimized exports and conversion manifest |
| `Assets/ThirdParty/Earth16K` | Supplied Earth originals, runtime maps and smoother planet FBX |
| `Content/ThirdParty` | Imported Unreal cabin geometry/materials/textures and Earth assets |
| `Content/Characters` | Imported woman, restored materials, skeletons, retarget setup and corrected locomotion |
| `Content/Mannequin` | Epic's source animation and mannequin assets |
| `Content/Textures` | Imported textures used by the earlier scene and orbital sky |

GitHub does **not** back up these folders. The files remain in the current
checkout; `.gitignore` only prevents Git from adding them.

`Tools`, `Binaries`, `Intermediate`, `DerivedDataCache`, `Saved`,
`Build/UnrealMac`, and the native preview's build/cache folders are also local.
Older preview screenshots and generated Xcode/icon resources are excluded.
The customized Mac `Info.Template.plist` is tracked.

## Resume on this Mac

The asset folders are already present. Use Unreal 5.8 and the installed Xcode
and Metal toolchain, then run:

```sh
Scripts/package_unreal.sh
```

For the separate native preview:

```sh
NativePreview/build.sh
```

## Rebuild after cloning elsewhere

1. Install the compatible Unreal, Xcode and Metal toolchain on the destination
   Mac. Set `UE_ROOT` if Unreal is installed in a different location.
2. Restore the asset folders above from this Mac or a private backup, keeping
   the same paths relative to the project root.
3. Build with `Scripts/package_unreal.sh`. The standalone app appears under
   `Build/UnrealMac/Mac/OrbitalHabitat.app`.

If the imported Unreal folders were not backed up, the conversion/import
scripts can regenerate them from the local artwork. The main order is:

1. Prepare the cabin with Blender using `Scripts/prepare_cabin.py`; prepare the
   texture maps and character FBX from the corresponding source assets.
2. Build the C++ editor module with `Scripts/build_unreal.sh`.
3. Run `Scripts/bootstrap_unreal.py`, `Scripts/import_cabin_unreal.py`, and
   `Scripts/import_earth_unreal.py` in Unreal's Python environment.
4. Restore Epic's standard Mannequin template content at `Content/Mannequin`.
   Export the planet with `Scripts/prepare_earth_mesh.py`, then run
   `Scripts/repair_visual_assets_unreal.py`.
5. Apply `Scripts/finish_cabin_unreal.py` and
   `Scripts/relax_crew_idle_unreal.py`, then package the app.

Use Blender's `--disable-autoexec` option when processing downloaded scenes.
The supplied source folders and conversion manifests are still required;
these scripts do not automatically download the third-party library.

See [Asset credits](ASSET_CREDITS.md) for download sources and licenses. Preserve
the vendor terms when backing up or moving the files; the acquired cabin and
Earth source assets are not distributed through this repository.
