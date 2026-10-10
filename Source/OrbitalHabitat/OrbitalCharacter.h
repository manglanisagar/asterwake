#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "OrbitalCharacter.generated.h"
class UCameraComponent;
class USpringArmComponent;
class UAnimationAsset;
UCLASS()
class ORBITALHABITAT_API AOrbitalCharacter : public ACharacter
{
    GENERATED_BODY()
public:
    AOrbitalCharacter();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
private:
    UPROPERTY() TObjectPtr<UCameraComponent> Camera;
    UPROPERTY() TObjectPtr<USpringArmComponent> Arm;
    UPROPERTY() TObjectPtr<UAnimationAsset> IdleAnimation;
    UPROPERTY() TObjectPtr<UAnimationAsset> WalkAnimation;
    UPROPERTY() TObjectPtr<UAnimationAsset> RunAnimation;
    UPROPERTY() TObjectPtr<UAnimationAsset> ActiveAnimation;
    UPROPERTY() TObjectPtr<UAnimationAsset> LocomotionAnimation;
    void Forward(float V);
    void Right(float V);
    void Interact();
    void Lights();
    void Shutter();
    void Night();
    void CameraMode();
    void SprintStart();
    void SprintEnd();
    void Reset();
    void ReleaseMouse();
    void CaptureMouse();
    void LookYaw(float Value);
    void LookPitch(float Value);
    bool bThirdPerson=true;
    bool bMouseCaptured=true;
    FTransform StartingTransform;
    FRotator StartingView;
};
