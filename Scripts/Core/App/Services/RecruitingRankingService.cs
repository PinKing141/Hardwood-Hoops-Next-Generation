using System;
using HardwoodHoops.Core.Domain.Recruiting;

namespace HardwoodHoops.Core.App.Services;

public sealed class RecruitingRankingService
{
    public RecruitingCheckpointResult EvaluateCheckpoint(RecruitingCheckpointInput input)
    {
        var stageWeight = input.Stage switch
        {
            RecruitingStage.JuniorHighSchool => 4,
            RecruitingStage.AauCircuit => 8,
            _ => 10
        };

        var importanceWeight = input.Importance == FeaturedImportance.Playoff ? 4 : 0;
        var scoutWeight = input.ScoutPresence ? 3 : 0;
        var visibilityWeight = input.HighVisibility ? 3 : 0;
        var opponentWeight = Math.Clamp(input.OpponentQuality, 1, 5) - 3;

        var performanceWeight = input.Performance switch
        {
            PerformanceDelta.MajorPositive => 10,
            PerformanceDelta.Positive => 5,
            PerformanceDelta.Negative => -5,
            PerformanceDelta.MajorNegative => -10,
            _ => 0
        };

        var delta = stageWeight + importanceWeight + scoutWeight + visibilityWeight + opponentWeight + performanceWeight;
        return new RecruitingCheckpointResult(delta, input.Performance);
    }

    public void ApplyCheckpoint(ProspectProfile profile, RecruitingCheckpointInput input)
    {
        var result = EvaluateCheckpoint(input);
        profile.ApplyCheckpoint(result, input);
    }
}
