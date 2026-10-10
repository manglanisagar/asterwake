#include "OrbitalGameMode.h"
#include "OrbitalCharacter.h"
#include "OrbitalWorld.h"
#include "Engine/World.h"
#include "EngineUtils.h"
AOrbitalGameMode::AOrbitalGameMode() { DefaultPawnClass=AOrbitalCharacter::StaticClass(); }
void AOrbitalGameMode::BeginPlay()
{
    Super::BeginPlay();
    TActorIterator<AOrbitalWorld> Ship(GetWorld());
    if(!Ship) GetWorld()->SpawnActor<AOrbitalWorld>();
}
