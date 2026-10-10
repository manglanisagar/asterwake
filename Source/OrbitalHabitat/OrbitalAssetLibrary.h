#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "OrbitalAssetLibrary.generated.h"

class UBlendSpace;

UCLASS()
class ORBITALHABITAT_API UOrbitalAssetLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    // Python's property setter does not rebuild the blend-space sample cache.
    UFUNCTION(BlueprintCallable, Category="Orbital Assets")
    static void FinalizeBlendSpace(UBlendSpace* Asset);
};
