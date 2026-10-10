#include "OrbitalAssetLibrary.h"
#include "Animation/BlendSpace.h"

void UOrbitalAssetLibrary::FinalizeBlendSpace(UBlendSpace* Asset)
{
#if WITH_EDITOR
    if(Asset) {
        Asset->ResampleData();
        Asset->MarkPackageDirty();
    }
#endif
}
