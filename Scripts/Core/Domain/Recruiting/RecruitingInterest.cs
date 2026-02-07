using System.Collections.Generic;

namespace HardwoodHoops.Core.Domain.Recruiting;

public sealed class RecruitingInterest
{
    public RecruitingInterest(string playerId, string teamId, double interest, double fitScore)
    {
        PlayerId = playerId;
        TeamId = teamId;
        Interest = interest;
        FitScore = fitScore;
    }

    public string PlayerId { get; }
    public string TeamId { get; }
    public double Interest { get; set; }
    public double FitScore { get; }
    public bool OfferMade { get; set; }
    public bool Committed { get; set; }
    public int Visits { get; set; }
    public List<int> VisitHistory { get; } = new();
    public List<int> OfferHistory { get; } = new();
    public double? PublicRating { get; set; }
    public double? TrueRating { get; set; }
    public int? ClassRank { get; set; }
    public string? Region { get; set; }
}
