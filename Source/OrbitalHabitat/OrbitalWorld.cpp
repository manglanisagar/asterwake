#include "OrbitalWorld.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/StaticMesh.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/World.h"
#include "Engine/PointLight.h"
#include "EngineUtils.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Kismet/GameplayStatics.h"

namespace {
FVector Convert(const TArray<TSharedPtr<FJsonValue>>& A) {return FVector(-A[2]->AsNumber(),A[0]->AsNumber(),A[1]->AsNumber())*100;}
}
AOrbitalWorld::AOrbitalWorld()
{
    PrimaryActorTick.bCanEverTick=true;
    RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}
UStaticMeshComponent* AOrbitalWorld::AddMesh(FString Name,FVector P,FVector S,FString Path,UMaterialInterface* Material,bool Collision)
{
    auto* C=NewObject<UStaticMeshComponent>(this,MakeUniqueObjectName(this,UStaticMeshComponent::StaticClass(),FName(Name)));
    C->SetMobility(EComponentMobility::Movable);C->SetupAttachment(RootComponent);
    C->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,*Path));C->SetMaterial(0,Material);
    C->SetRelativeLocation(P);C->SetRelativeScale3D(S);
    C->SetCollisionEnabled(Collision?ECollisionEnabled::QueryAndPhysics:ECollisionEnabled::NoCollision);
    C->SetCollisionResponseToAllChannels(ECR_Block);C->RegisterComponent();AddInstanceComponent(C);
    return C;
}
void AOrbitalWorld::BeginPlay()
{
    Super::BeginPlay();
    FString Data;
    if(!FFileHelper::LoadFileToString(Data,*(FPaths::ProjectContentDir()/TEXT("RuntimeData/layout.json")))) {UE_LOG(LogTemp,Error,TEXT("Missing shared ship layout"));return;}
    TSharedPtr<FJsonObject> J;
    if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Data),J)) return;
    TMap<FString,UMaterialInstanceDynamic*> Mats;
    auto* Base=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Materials/M_Base.M_Base"));
    if(!Base) {UE_LOG(LogTemp,Error,TEXT("Run Scripts/bootstrap_unreal.py first to create materials and map"));return;}
    for(auto& Pair:J->GetObjectField(TEXT("materials"))->Values) {
        auto Def=Pair.Value->AsObject();auto A=Def->GetArrayField(TEXT("color"));
        auto* M=UMaterialInstanceDynamic::Create(Base,this);
        M->SetVectorParameterValue("BaseColor",FLinearColor(A[0]->AsNumber(),A[1]->AsNumber(),A[2]->AsNumber()));
        M->SetScalarParameterValue("Roughness",Def->GetNumberField(TEXT("roughness")));M->SetScalarParameterValue("Metallic",Def->GetNumberField(TEXT("metalness")));
        if(Def->HasField(TEXT("emission"))) {auto E=Def->GetArrayField(TEXT("emission"));M->SetVectorParameterValue("Emission",FLinearColor(E[0]->AsNumber(),E[1]->AsNumber(),E[2]->AsNumber()));}
        Mats.Add(FString(*Pair.Key),M);
    }
    if(bBuildBlockoutInterior) for(auto V:J->GetArrayField(TEXT("objects"))) {
        auto O=V->AsObject();auto Size=O->GetArrayField(TEXT("size"));
        auto* C=AddMesh(O->GetStringField(TEXT("name")),Convert(O->GetArrayField(TEXT("position"))),
            FVector(Size[2]->AsNumber(),Size[0]->AsNumber(),Size[1]->AsNumber()),TEXT("/Engine/BasicShapes/Cube.Cube"),Mats[O->GetStringField(TEXT("material"))],O->GetBoolField(TEXT("collision")));
        FString Group=O->GetStringField(TEXT("group"));
        if(Group=="door") Doors.Add(C);
        if(Group=="shutter") {Shutters.Add(C);C->SetVisibility(false);}
    }
    auto E=J->GetObjectField(TEXT("earth"));float R=E->GetNumberField(TEXT("radius"));
    const FString PlanetMesh=TEXT("/Game/ThirdParty/Earth16K/SM_EarthSurface.SM_EarthSurface");
    EarthMaterial=UMaterialInstanceDynamic::Create(LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Materials/M_Earth.M_Earth")),this);
    if(EarthMaterial) {
        Earth=AddMesh("Earth",Convert(E->GetArrayField(TEXT("position"))),FVector(R*2),PlanetMesh,EarthMaterial,false);
        if(!bBuildBlockoutInterior) Earth->SetRelativeLocation(FVector(610000,0,-330000));
        Earth->SetCastShadow(false);Earth->SetRelativeRotation(FRotator(0,106,0));
    }
    auto* Clouds=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Materials/M_Clouds.M_Clouds"));
    if(Clouds && Earth) {auto* C=AddMesh("Clouds",Earth->GetRelativeLocation(),FVector((R+8)*2),PlanetMesh,Clouds,false);C->SetCastShadow(false);C->SetRelativeRotation(Earth->GetRelativeRotation());}
    auto* Atmos=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Materials/M_Atmosphere.M_Atmosphere"));
    if(Atmos && Earth) {auto* C=AddMesh("Atmosphere",Earth->GetRelativeLocation(),FVector((R+34)*2),PlanetMesh,Atmos,false);C->SetCastShadow(false);}
    auto* SkyBase=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Materials/M_Stars.M_Stars"));
    if(SkyBase) {SkyMaterial=UMaterialInstanceDynamic::Create(SkyBase,this);auto* C=AddMesh("Starfield",FVector::ZeroVector,FVector(48000),TEXT("/Engine/BasicShapes/Sphere.Sphere"),SkyMaterial,false);C->SetCastShadow(false);}
    Sun=NewObject<UDirectionalLightComponent>(this);Sun->SetupAttachment(RootComponent);Sun->SetIntensity(bBuildBlockoutInterior?4:150);Sun->SetLightColor(FLinearColor(1,0.97,0.92));Sun->SetRelativeRotation(FRotator(-35,-30,0));Sun->RegisterComponent();AddInstanceComponent(Sun);
    if(bBuildBlockoutInterior) for(auto P:{FVector(270,0,250),FVector(0,0,250),FVector(-260,0,250),FVector(-600,0,240),FVector(-1030,0,250)}) {
        auto* L=NewObject<UPointLightComponent>(this);L->SetupAttachment(RootComponent);L->SetRelativeLocation(P);L->SetIntensity(220);L->SetAttenuationRadius(550);L->SetLightColor(FLinearColor(1,0.86,0.68));L->SetCastShadows(false);L->RegisterComponent();AddInstanceComponent(L);Lights.Add(L);
    }
    if(!bBuildBlockoutInterior) {
        for(TActorIterator<APointLight> I(GetWorld());I;++I) {
            if(auto* Light=Cast<UPointLightComponent>(I->GetLightComponent())) Lights.Add(Light);
        }
    }
    for(auto Light:Lights) LightIntensities.Add(Light->Intensity);
    if(!bBuildBlockoutInterior) return;
    auto* Post=GetWorld()->SpawnActor<APostProcessVolume>();Post->bUnbound=true;
    Post->Settings.bOverride_AutoExposureMinBrightness=true;Post->Settings.AutoExposureMinBrightness=0.7;
    Post->Settings.bOverride_AutoExposureMaxBrightness=true;Post->Settings.AutoExposureMaxBrightness=1.3;
    Post->Settings.bOverride_BloomIntensity=true;Post->Settings.BloomIntensity=0.15;
}
void AOrbitalWorld::Tick(float Delta)
{
    Super::Tick(Delta);
    DoorAlpha=FMath::FInterpTo(DoorAlpha,bDoorOpen?1.f:0.f,Delta,7);
    ShutterAlpha=FMath::FInterpTo(ShutterAlpha,bShutterClosed?1.f:0.f,Delta,6);
    for(auto C:Doors) {auto P=C->GetRelativeLocation();P.Y=-140*DoorAlpha;C->SetRelativeLocation(P);C->SetCollisionEnabled(DoorAlpha>0.9?ECollisionEnabled::NoCollision:ECollisionEnabled::QueryAndPhysics);}
    for(auto C:Shutters) {auto P=C->GetRelativeLocation();P.Z=330-162*ShutterAlpha;C->SetRelativeLocation(P);C->SetVisibility(ShutterAlpha>0.01);}
    if(Earth) Earth->AddLocalRotation(FRotator(0,Delta*0.01,0));
    if(SkyMaterial) {
        float Level=bNight&&!bLightsOn ? 0.65f : 0.003f;
        SkyMaterial->SetScalarParameterValue("Brightness",Level);
    }
}
void AOrbitalWorld::Interact(FVector P) {if(FVector::Dist2D(P,FVector(-386,0,0))<200) bDoorOpen=!bDoorOpen;else if(P.X>210) ToggleLights();}
void AOrbitalWorld::ToggleLights() {bLightsOn=!bLightsOn;for(int32 I=0;I<Lights.Num();++I)Lights[I]->SetIntensity(LightIntensities[I]*(bLightsOn?1.f:0.045f));}
void AOrbitalWorld::ToggleShutter() {bShutterClosed=!bShutterClosed;}
void AOrbitalWorld::ToggleNight() {bNight=!bNight;if(Sun){Sun->SetIntensity(bNight?0.1:(bBuildBlockoutInterior?4:150));Sun->SetRelativeRotation(bNight?FRotator(-20,160,0):FRotator(-35,-30,0));}if(EarthMaterial) EarthMaterial->SetScalarParameterValue("NightMode",bNight?1:0);}
