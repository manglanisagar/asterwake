# Existing artwork for the realistic prototype

Reviewed October 9, 2026. No paid assets have been purchased.

## First choice: a complete cabin

[Sci Fi Bedroom — MASSX-RZ](https://www.cgtrader.com/free-3d-models/space/spaceship/sci-fi-bedroom-79647903-765e-4dc0-8502-6e3947156e8d)

- Listed as free. Native Blender scene, FBX, USD and texture files.
- The published render has a practical metal cabin, bed beneath a large framed
  window, workstation, wall storage and personal objects. This is the closest
  free scene found to the project's visual target.
- The woman and exterior views in the listing images are excluded. Earth and
  the protagonist must be supplied separately.
- This is artwork for one room. It still needs game collision, an entrance,
  lighting adapted for Unreal, and adjoining rooms.
- The user downloaded the scene, textures and FBX archive on October 10, 2026.
  Originals are preserved under `Assets/ThirdParty/EndlessJourney/Original`.
- A separate game copy has been exported with portable PBR material maps. The
  evaluated scene was reduced from about 13.6 million to 2.2 million polygons.
  This is an initial geometry reduction, not an M1 performance validation.
- Obtain the Blender scene and accompanying texture package; FBX is a useful
  exchange copy. Keep the original archive and the license locally.
- The published polygon count is over six million. Inspect evaluated geometry
  and subdivision modifiers before import; don't assume the raw scene is a
  suitable iPad asset.

License: Royalty Free (No AI). CGTrader's [terms, sections 21A, 21B and
24](https://www.cgtrader.com/pages/terms-and-conditions) permit incorporation
into games and prohibit model redistribution and use for machine learning or
training neural networks. Keep source artwork private and distribute cooked
game content. Do not feed this asset into generative asset tools.

## Useful alternatives

| Asset | Availability | Fit and import considerations |
| --- | --- | --- |
| [Sci-Fi Bedroom — dylanheyes](https://sketchfab.com/3d-models/sci-fi-bedroom-9bf95b0af80244d693c22d160e5c5405) | Free, CC BY 4.0; Sketchfab sign-in needed | Complete room, about 431,000 triangles. Alternative if the first cabin proves difficult to convert. Needs attribution and a replacement exterior view. |
| [The Nomad — OuterSpaceSimon](https://www.blendkit.com/asset-gallery-detail/6ae41daa-3da1-4dc0-9210-18a246a65524/) | Free, royalty-free; Blendkit account/add-on | Complete rigged ship with an interior, about 698,000 polygons and a 496 MiB download. Its space-caravan design is smaller than the intended large ship. Blender conversion required. |
| [Scifi Hallway — Epic Games](https://www.fab.com/listings/e3cadcef-7709-4e6d-9f56-d6fb2156cb67) | Free Unreal sample | Existing detailed corridor and Unreal materials. Potential adjoining-room asset source. Check download version and license before migration into UE 5.8. |
| [Sci-Fi Living Room — Tirgames Assets](https://www.fab.com/listings/3ac29c64-44e4-469c-bce5-de93ffe0f58d) | Paid, approval required | Unreal interior with bedroom, work area, bathroom, modular pieces and door Blueprints. No connecting corridors or outer ship walls. Exact license price has not been verified. |
| [Space Tourism Spaceship Interior — Farom Studio](https://www.fab.com/listings/85a7f2b6-8499-472c-b7fa-870f123a26e7) | Paid, approval required | Complete modular spaceship interior, Unreal format. Fab search displayed a starting price of $29.99 before tax; confirm the selected license and Mac project compatibility before purchase. |

## Character and planet

Use an existing MetaHuman preset assembled for games as the intended realistic
female character. Epic's [assembly documentation](https://dev.epicgames.com/documentation/metahuman/assembly)
provides High, Medium and Low game optimization options. Its
[UE 5.8 release notes](https://dev.epicgames.com/documentation/metahuman/metahuman-5-8-release-notes-in-unreal-engine)
describe Mac support. The existing Rocketbox character remains a temporary
movement-preview asset; MetaHuman content is not installed in this project yet.

Earth's existing day, cloud and night maps are already downloaded. See
[ASSET_CREDITS.md](ASSET_CREDITS.md). Adapt the material, scale and sun angle to
the acquired cabin's window instead of using a flat Earth photograph.

## Integration order

1. Acquire the cabin from its official download flow and preserve its license.
2. Inspect the existing Blender scene: units, room bounds, texture dependencies,
   glass/window objects and subdivision cost. Keep the source unchanged.
3. Export a separate game copy with textures. Import as separate meshes and
   materials into Unreal so doors, glass and collision can be adjusted.
4. Preserve the author's room composition. Replace the exterior view with the
   Earth scene and install the walking pawn at a valid PlayerStart.
5. Use an optimized existing human and animation library. Add adjoining rooms
   with the same material language after the first cabin reaches the target.

Published renders demonstrate artwork quality, not this Mac's real-time
performance. The asset has to be rendered in Unreal before claiming that it
matches the reference or meets an M4/M1 frame budget.
