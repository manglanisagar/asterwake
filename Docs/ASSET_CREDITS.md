# Asset credits

## Earth and sky

Earth day, night, clouds, and stars/Milky Way textures by **Solar System Scope /
INOVE**, based on NASA imagery and other astronomical references.

- Source: https://www.solarsystemscope.com/textures/
- License: Creative Commons Attribution 4.0 International
- License text: https://creativecommons.org/licenses/by/4.0/
- Changes: resized/recompressed for runtime textures; cloud opacity derived
  in the material shader; textures mapped onto spherical geometry.
- Source JPGs retained in `Assets/Source`.

## Female crew prototype

`Assets/Source/Crew.glb` is **Female_Adult_07** from **Microsoft Rocketbox**,
converted to GLB by the react-ai-voice-avatar project (927tanmay).

- Original: https://github.com/microsoft/Microsoft-Rocketbox
- GLB conversion: https://github.com/927tanmay/react-ai-voice-avatar/tree/main/assets/avatars
- License: MIT. Original copyright and full license are retained alongside assets.
- Changes here: embedded maps extracted and restored as Unreal PBR materials;
  skeleton axes aligned for Unreal retargeting. The native preview adjusts
  bone rotations at runtime for a relaxed stance and a simple walking gait.
- This is a temporary asset, not a custom photorealistic protagonist.
- Unreal locomotion uses retargeted **ThirdPersonIdle**, **ThirdPersonWalk** and
  **ThirdPersonRun** from Epic's installed Mannequin template. Those template
  assets remain subject to Epic's Unreal Engine content license; their motion
  is used in the Unreal build. The native preview retains its separate gait.
  The Unreal idle and walking upper body are adjusted around the woman's own
  reference posture to reduce the template's forward lean and wide arms.

## Earlier character sample

`Michelle.glb` from three.js was downloaded for evaluation and has been
superseded by the Rocketbox character. It is not loaded by the current app.
The downloaded example's independent asset license was not established for
production, so do not include it in a release package.

## Original work

Cabin geometry/layout, procedural material detail textures, game source,
and assembly scripts were created for this project. The visual target image
in `Reference` was generated in this conversation; it is concept art, not a
screenshot of the running game.
## Endless Journey cabin

The existing cabin is **Sci Fi Bedroom / Endless Journey** by **MASSX-RZ**,
downloaded by the user from [CGTrader](https://www.cgtrader.com/free-3d-models/space/spaceship/sci-fi-bedroom-79647903-765e-4dc0-8502-6e3947156e8d)
on October 10, 2026. Licensed under CGTrader Royalty Free (No AI), subject to
the [applicable terms](https://www.cgtrader.com/pages/terms-and-conditions).

The original artwork stays private. Game-copy changes include reduced
subdivision and repeated detail geometry, PBR shader conversion, glass
adaptation, and placing the room in the project's Earth-orbit environment.
The original scene excludes the presentation character and exterior views.


## Supplied Earth asset

**Earth 16k** by **karthic2k1999**, downloaded by the user from
[CGTrader](https://www.cgtrader.com/free-3d-models/plant/other/earth-16k-f2b2ab91-665c-4409-beac-be0f8069af8d)
on October 10, 2026. The listing specifies Royalty Free (No AI). Source maps
are preserved privately under `Assets/ThirdParty/Earth16K/Original`. Runtime
copies use 8K surface/night maps and 4K cloud/normal/roughness maps.

