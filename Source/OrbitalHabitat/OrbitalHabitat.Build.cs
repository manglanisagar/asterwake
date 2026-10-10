using UnrealBuildTool;
public class OrbitalHabitat : ModuleRules
{
    public OrbitalHabitat(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new string[] {"Core", "CoreUObject", "Engine", "InputCore", "Json", "JsonUtilities"});
    }
}
