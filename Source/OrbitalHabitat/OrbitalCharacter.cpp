#include "OrbitalCharacter.h"
#include "OrbitalWorld.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/InputComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "EngineUtils.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/PlayerStart.h"
#include "Animation/AnimationAsset.h"
#include "Animation/AnimSingleNodeInstance.h"

namespace { AOrbitalWorld* FindShip(UWorld* World) { TActorIterator<AOrbitalWorld> I(World); return I ? *I : nullptr; } }
AOrbitalCharacter::AOrbitalCharacter()
{
    PrimaryActorTick.bCanEverTick=true;
    GetCapsuleComponent()->InitCapsuleSize(24,88);
    GetCharacterMovement()->MaxWalkSpeed=150;
    GetCharacterMovement()->MaxStepHeight=18;
    GetCharacterMovement()->BrakingDecelerationWalking=900;
    GetMesh()->SetRelativeLocation(FVector(0,0,-88));
    GetMesh()->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    Arm=CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraArm"));
    Arm->SetupAttachment(GetRootComponent());Arm->bUsePawnControlRotation=true;
    Arm->TargetArmLength=220;Arm->SocketOffset=FVector(0,32,5);
    Arm->SetRelativeLocation(FVector(0,0,10));Arm->ProbeSize=12;
    Camera=CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
    Camera->SetupAttachment(Arm);Camera->FieldOfView=72;
    bUseControllerRotationYaw=false;
    GetCharacterMovement()->bOrientRotationToMovement=true;
    GetCharacterMovement()->RotationRate=FRotator(0,540,0);
}
void AOrbitalCharacter::BeginPlay()
{
    Super::BeginPlay();
    TActorIterator<APlayerStart> Start(GetWorld());
    if(!Start) SetActorLocation(FVector(-80,10,92));
    SetActorRotation(FRotator(0,GetActorRotation().Yaw,0));
    StartingTransform=GetActorTransform();
    StartingView=Start?Start->GetActorRotation():FRotator::ZeroRotator;
    StartingView.Pitch=-15;
    if(auto* PC=Cast<APlayerController>(GetController())) {PC->SetControlRotation(StartingView);PC->SetInputMode(FInputModeGameOnly());PC->bShowMouseCursor=false;}
    if(auto* Mesh=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/Characters/SK_Crew_Aligned.SK_Crew_Aligned"))) {
        GetMesh()->SetSkeletalMesh(Mesh);GetMesh()->SetRelativeLocation(FVector(0,0,-88));
        GetMesh()->SetRelativeRotation(FRotator(0,-90,0));GetMesh()->SetOwnerNoSee(!bThirdPerson);
        IdleAnimation=LoadObject<UAnimationAsset>(nullptr,TEXT("/Game/Characters/Animations/A_Crew_RelaxedIdle.A_Crew_RelaxedIdle"));
        WalkAnimation=LoadObject<UAnimationAsset>(nullptr,TEXT("/Game/Characters/Animations/A_Crew_Walk.A_Crew_Walk"));
        RunAnimation=LoadObject<UAnimationAsset>(nullptr,TEXT("/Game/Characters/Animations/A_Crew_Run.A_Crew_Run"));
        LocomotionAnimation=LoadObject<UAnimationAsset>(nullptr,TEXT("/Game/Characters/Animations/BS_Crew_Locomotion.BS_Crew_Locomotion"));
        if(LocomotionAnimation) {GetMesh()->PlayAnimation(LocomotionAnimation,true);ActiveAnimation=LocomotionAnimation;}
        else if(IdleAnimation) {GetMesh()->PlayAnimation(IdleAnimation,true);ActiveAnimation=IdleAnimation;}
    }
}
void AOrbitalCharacter::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    const float Speed=GetVelocity().Size2D();
    if(LocomotionAnimation) {
        if(auto* Instance=GetMesh()->GetSingleNodeInstance()) Instance->SetBlendSpacePosition(FVector(Speed,0,0));
        return;
    }
    UAnimationAsset* Desired=Speed<5?IdleAnimation.Get():(Speed>210?RunAnimation.Get():WalkAnimation.Get());
    if(Desired && Desired!=ActiveAnimation) {GetMesh()->PlayAnimation(Desired,true);ActiveAnimation=Desired;}
    if(auto* Instance=GetMesh()->GetSingleNodeInstance()) Instance->SetPlayRate(Speed<5?1:FMath::Clamp(Speed/(Speed>210?270:150),0.5f,1.8f));
}
void AOrbitalCharacter::SetupPlayerInputComponent(UInputComponent* Input)
{
    Super::SetupPlayerInputComponent(Input);
    Input->BindAxis("Forward",this,&AOrbitalCharacter::Forward);
    Input->BindAxis("Right",this,&AOrbitalCharacter::Right);
    Input->BindAxis("Yaw",this,&AOrbitalCharacter::LookYaw);
    Input->BindAxis("Pitch",this,&AOrbitalCharacter::LookPitch);
    Input->BindAction("Interact",IE_Pressed,this,&AOrbitalCharacter::Interact);
    Input->BindAction("Lights",IE_Pressed,this,&AOrbitalCharacter::Lights);
    Input->BindAction("Shutter",IE_Pressed,this,&AOrbitalCharacter::Shutter);
    Input->BindAction("Night",IE_Pressed,this,&AOrbitalCharacter::Night);
    Input->BindAction("Camera",IE_Pressed,this,&AOrbitalCharacter::CameraMode);
    Input->BindAction("Sprint",IE_Pressed,this,&AOrbitalCharacter::SprintStart);
    Input->BindAction("Sprint",IE_Released,this,&AOrbitalCharacter::SprintEnd);
    Input->BindAction("Reset",IE_Pressed,this,&AOrbitalCharacter::Reset);
    Input->BindAction("ReleaseMouse",IE_Pressed,this,&AOrbitalCharacter::ReleaseMouse);
    Input->BindAction("CaptureMouse",IE_Pressed,this,&AOrbitalCharacter::CaptureMouse);
}
void AOrbitalCharacter::Forward(float V) {AddMovementInput(FRotationMatrix(FRotator(0,GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::X),V);}
void AOrbitalCharacter::Right(float V) {AddMovementInput(FRotationMatrix(FRotator(0,GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::Y),V);}
void AOrbitalCharacter::Interact() {if(auto* W=FindShip(GetWorld())) W->Interact(GetActorLocation());}
void AOrbitalCharacter::Lights() {if(auto* W=FindShip(GetWorld())) W->ToggleLights();}
void AOrbitalCharacter::Shutter() {if(auto* W=FindShip(GetWorld())) W->ToggleShutter();}
void AOrbitalCharacter::Night() {if(auto* W=FindShip(GetWorld())) W->ToggleNight();}
void AOrbitalCharacter::CameraMode() {bThirdPerson=!bThirdPerson;Arm->TargetArmLength=bThirdPerson?220:0;Arm->SetRelativeLocation(FVector(0,0,bThirdPerson?10:70));Arm->SocketOffset=bThirdPerson?FVector(0,32,5):FVector::ZeroVector;GetMesh()->SetOwnerNoSee(!bThirdPerson);bUseControllerRotationYaw=!bThirdPerson;GetCharacterMovement()->bOrientRotationToMovement=bThirdPerson;}
void AOrbitalCharacter::SprintStart() {GetCharacterMovement()->MaxWalkSpeed=270;}
void AOrbitalCharacter::SprintEnd() {GetCharacterMovement()->MaxWalkSpeed=150;}
void AOrbitalCharacter::Reset() {GetCharacterMovement()->StopMovementImmediately();SetActorTransform(StartingTransform);if(GetController()) GetController()->SetControlRotation(StartingView);}
void AOrbitalCharacter::ReleaseMouse() {bMouseCaptured=false;if(auto* PC=Cast<APlayerController>(GetController())) {PC->SetInputMode(FInputModeGameAndUI());PC->bShowMouseCursor=true;}}
void AOrbitalCharacter::CaptureMouse() {bMouseCaptured=true;if(auto* PC=Cast<APlayerController>(GetController())) {PC->SetInputMode(FInputModeGameOnly());PC->bShowMouseCursor=false;}}
void AOrbitalCharacter::LookYaw(float Value) {if(bMouseCaptured) AddControllerYawInput(Value);}
void AOrbitalCharacter::LookPitch(float Value) {if(bMouseCaptured) AddControllerPitchInput(Value);}
