using UnrealBuildTool;
using System.Collections.Generic;
public class OrbitalHabitatEditorTarget : TargetRules
{
    public OrbitalHabitatEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V7;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("OrbitalHabitat");
    }
}
