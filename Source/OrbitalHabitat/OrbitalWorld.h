#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "OrbitalWorld.generated.h"
class UStaticMeshComponent;
class UPointLightComponent;
class UDirectionalLightComponent;
class UMaterialInstanceDynamic;
class UMaterialInterface;
UCLASS()
class ORBITALHABITAT_API AOrbitalWorld : public AActor
{
    GENERATED_BODY()
public:
    AOrbitalWorld();
    virtual void BeginPlay() override;
    virtual void Tick(float Delta) override;
    void Interact(FVector Position);
    void ToggleLights();
    void ToggleShutter();
    void ToggleNight();
    UPROPERTY(EditAnywhere, Category="Orbital") bool bBuildBlockoutInterior=true;
private:
    UStaticMeshComponent* AddMesh(FString Name,FVector Position,FVector Scale,FString MeshPath,UMaterialInterface* Material,bool Collision);
    UPROPERTY() TArray<TObjectPtr<UStaticMeshComponent>> Doors;
    UPROPERTY() TArray<TObjectPtr<UStaticMeshComponent>> Shutters;
    UPROPERTY() TArray<TObjectPtr<UPointLightComponent>> Lights;
    TArray<float> LightIntensities;
    UPROPERTY() TObjectPtr<UDirectionalLightComponent> Sun;
    UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> EarthMaterial;
    UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> SkyMaterial;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> Earth;
    bool bDoorOpen=false,bShutterClosed=false,bLightsOn=true,bNight=false;
    float DoorAlpha=0,ShutterAlpha=0;
};
