using System.Collections.Generic;

namespace HardwoodHoops.Core.Domain.Players;

public record PlayerTendencies(
    double ShotSelection,
    double Aggression,
    IReadOnlyList<double> ShotProfile,
    IReadOnlyList<double> RimAggression,
    IReadOnlyList<double> ShotCreation,
    IReadOnlyList<double> PlaymakingBias,
    IReadOnlyList<double> PassProfile,
    IReadOnlyList<double> DefensiveStyle,
    IReadOnlyList<double> HelpDefense,
    IReadOnlyList<double> ReboundBias,
    IReadOnlyList<double> AthleticUsage
)
{
    public static PlayerTendencies Default() => new(
        ShotSelection: 0.5,
        Aggression: 0.5,
        ShotProfile: new[] { 0.4, 0.25, 0.35 },
        RimAggression: new[] { 0.6, 0.4 },
        ShotCreation: new[] { 0.4, 0.25, 0.35 },
        PlaymakingBias: new[] { 0.4, 0.35, 0.25 },
        PassProfile: new[] { 0.4, 0.25, 0.35 },
        DefensiveStyle: new[] { 0.45, 0.35, 0.20 },
        HelpDefense: new[] { 0.35, 0.35, 0.30 },
        ReboundBias: new[] { 0.4, 0.2, 0.4 },
        AthleticUsage: new[] { 0.3, 0.25, 0.25, 0.2 }
    );
}
