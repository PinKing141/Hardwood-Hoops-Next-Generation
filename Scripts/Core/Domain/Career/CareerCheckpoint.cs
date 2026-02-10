using HardwoodHoops.Core.Domain.Recruiting;

namespace HardwoodHoops.Core.Domain.Career;

public enum CareerStage
{
    JuniorHighSchool,
    AauCircuit,
    SeniorHighSchool
}

public sealed class CareerCheckpoint
{
    public CareerCheckpoint(
        CareerStage stage,
        FeaturedImportance importance,
        bool scoutPresence,
        bool highVisibility,
        bool isRankingUpdate,
        bool isStarUpdate,
        bool isFeatured)
    {
        Stage = stage;
        Importance = importance;
        ScoutPresence = scoutPresence;
        HighVisibility = highVisibility;
        IsRankingUpdate = isRankingUpdate;
        IsStarUpdate = isStarUpdate;
        IsFeatured = isFeatured;
    }

    public CareerStage Stage { get; }
    public FeaturedImportance Importance { get; }
    public bool ScoutPresence { get; }
    public bool HighVisibility { get; }
    public bool IsRankingUpdate { get; }
    public bool IsStarUpdate { get; }
    public bool IsFeatured { get; }
}
