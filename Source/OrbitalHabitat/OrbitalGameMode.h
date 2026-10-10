#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "OrbitalGameMode.generated.h"
UCLASS()
class ORBITALHABITAT_API AOrbitalGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AOrbitalGameMode();
    virtual void BeginPlay() override;
};
