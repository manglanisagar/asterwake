using UnrealBuildTool;
using System.Collections.Generic;
public class OrbitalHabitatTarget : TargetRules
{
    public OrbitalHabitatTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V7;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("OrbitalHabitat");
    }
}
