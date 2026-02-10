namespace HardwoodHoops.Core.Domain.Recruiting;

public sealed record RecruitingRankingEntry(
    int Rank,
    string PlayerName,
    string Position,
    int HeightInches,
    int WeightLbs,
    string Program,
    string Commitment,
    int Stars,
    RecruitTrend Trend,
    string Build,
    string[] Tags,
    string[] Offers,
    int ClassYear,
    float ShotClose,
    float ShotMid,
    float ShotThree,
    float CreationCatch,
    float CreationPull,
    float CreationDrive,
    float RimLayup,
    float RimDunk);
