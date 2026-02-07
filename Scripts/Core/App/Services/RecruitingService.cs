using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Recruiting;
using HardwoodHoops.Core.Simulation.Rng;

namespace HardwoodHoops.Core.App.Services;

public sealed class RecruitingService
{
    private readonly IRng _rng;
    private readonly Dictionary<string, double> _regionBias;
    private readonly double _interestDecay;
    private readonly int _maxVisits;
    private readonly (int start, int end) _earlySigningWeeks;
    private readonly int _lateSigningStart;

    public RecruitingService(
        IRng rng,
        Dictionary<string, double>? regionBias = null,
        double interestDecay = 0.02,
        int maxVisits = 5,
        (int start, int end)? earlySigningWeeks = null,
        int lateSigningStart = 8)
    {
        _rng = rng;
        _regionBias = regionBias ?? new Dictionary<string, double>();
        _interestDecay = interestDecay;
        _maxVisits = maxVisits;
        _earlySigningWeeks = earlySigningWeeks ?? (3, 4);
        _lateSigningStart = lateSigningStart;
    }

    public RecruitingInterest EvaluateProspect(
        string playerId,
        string teamId,
        double fitScore,
        int classRank,
        string region)
    {
        var trueRating = 90 - classRank * 0.05 + fitScore * 10;
        var publicRating = NoisyRating(trueRating, classRank);
        var baseInterest = fitScore * 0.3 + _regionBias.GetValueOrDefault(region);
        return new RecruitingInterest(playerId, teamId, baseInterest, fitScore)
        {
            OfferMade = false,
            Committed = false,
            Visits = 0,
            PublicRating = publicRating,
            TrueRating = trueRating,
            ClassRank = classRank,
            Region = region
        };
    }

    public double RegionBiasedInterestValue(double value, string? recruitRegion, string? teamRegion)
    {
        if (string.IsNullOrWhiteSpace(recruitRegion) || string.IsNullOrWhiteSpace(teamRegion))
        {
            return value;
        }

        if (recruitRegion.ToLowerInvariant() == teamRegion.ToLowerInvariant())
        {
            return value + 0.05;
        }

        return System.Math.Max(0.0, value - 0.02);
    }

    public RecruitingInterest TickInterest(
        RecruitingInterest interaction,
        bool offered,
        bool visit,
        int? week,
        string? recruitRegion,
        string? teamRegion)
    {
        var delta = offered ? 0.05 : 0.0;
        if (visit && interaction.Visits < _maxVisits)
        {
            delta += 0.1;
            interaction.Visits += 1;
            if (week.HasValue)
            {
                interaction.VisitHistory.Add(week.Value);
            }
        }
        if (offered && week.HasValue)
        {
            interaction.OfferHistory.Add(week.Value);
        }

        var interest = interaction.Interest + delta + interaction.FitScore * 0.02;
        interest = RegionBiasedInterestValue(interest, recruitRegion, teamRegion);
        interaction.Interest = System.Math.Min(1.0, interest);
        interaction.OfferMade |= offered;
        return interaction;
    }

    public List<RecruitingInterest> DecayInterest(IEnumerable<RecruitingInterest> interactions)
    {
        var updated = new List<RecruitingInterest>();
        foreach (var inter in interactions)
        {
            var decayAmount = _interestDecay * (1 - inter.FitScore);
            inter.Interest = System.Math.Max(0.0, inter.Interest - decayAmount);
            updated.Add(inter);
        }
        return updated;
    }

    public CommitmentDecision? CommitIfReady(RecruitingInterest interaction, bool signingWindowOpen)
    {
        if (!signingWindowOpen)
        {
            return null;
        }
        var threshold = 0.75 + (interaction.Visits * 0.02);
        if (interaction.Interest >= threshold)
        {
            interaction.Committed = true;
            return new CommitmentDecision(interaction.PlayerId, interaction.TeamId, true, "Reached interest threshold");
        }
        return null;
    }

    public CommitmentDecision? ResolveCompetition(
        IEnumerable<RecruitingInterest> interactions,
        string? signingWindow = null)
    {
        var list = new List<RecruitingInterest>(interactions);
        if (list.Count == 0)
        {
            return null;
        }

        var windowThreshold = signingWindow switch
        {
            "early" => 0.6,
            "late" => 0.5,
            _ => 0.0
        };

        list.Sort((a, b) =>
        {
            var interestCompare = b.Interest.CompareTo(a.Interest);
            if (interestCompare != 0) return interestCompare;
            var ratingCompare = (b.TrueRating ?? 0).CompareTo(a.TrueRating ?? 0);
            if (ratingCompare != 0) return ratingCompare;
            return _rng.NextDouble().CompareTo(0.5);
        });

        var winner = list[0];
        if (!string.IsNullOrWhiteSpace(signingWindow) && winner.Interest < windowThreshold)
        {
            return null;
        }

        winner.Committed = true;
        return new CommitmentDecision(winner.PlayerId, winner.TeamId, true, $"Won {signingWindow ?? "open"} window competition");
    }

    public List<RecruitingInterest> BuildProspectBoard(IEnumerable<RecruitingInterest> interactions)
    {
        var list = new List<RecruitingInterest>(interactions);
        list.Sort((a, b) =>
        {
            var publicCompare = (b.PublicRating ?? 0).CompareTo(a.PublicRating ?? 0);
            if (publicCompare != 0) return publicCompare;
            return (a.ClassRank ?? 9999).CompareTo(b.ClassRank ?? 9999);
        });
        return list;
    }

    public List<RecruitingInterest> BuildAiBoard(IEnumerable<RecruitingInterest> interactions)
    {
        var list = new List<RecruitingInterest>(interactions);
        list.Sort((a, b) =>
        {
            var trueCompare = (b.TrueRating ?? 0).CompareTo(a.TrueRating ?? 0);
            if (trueCompare != 0) return trueCompare;
            return b.Interest.CompareTo(a.Interest);
        });
        return list;
    }

    public List<CommitmentDecision> AdvanceWeek(IEnumerable<RecruitingInterest> interactions, int week)
    {
        var decayed = DecayInterest(interactions);
        string? signingWindow = null;
        if (week >= _earlySigningWeeks.start && week <= _earlySigningWeeks.end)
        {
            signingWindow = "early";
        }
        else if (week >= _lateSigningStart)
        {
            signingWindow = "late";
        }

        var decisions = new List<CommitmentDecision>();
        if (!string.IsNullOrWhiteSpace(signingWindow))
        {
            var grouped = new Dictionary<string, List<RecruitingInterest>>();
            foreach (var inter in decayed)
            {
                grouped.TryAdd(inter.PlayerId, new List<RecruitingInterest>());
                grouped[inter.PlayerId].Add(inter);
            }

            foreach (var list in grouped.Values)
            {
                var decision = ResolveCompetition(list, signingWindow);
                if (decision is not null)
                {
                    decisions.Add(decision);
                }
            }
        }

        return decisions;
    }

    public List<RecruitingInterest> OpenTransferPortal(
        IEnumerable<RecruitingInterest> interactions,
        double leaveProbability = 0.1)
    {
        var reopened = new List<RecruitingInterest>();
        foreach (var inter in interactions)
        {
            if (!inter.Committed)
            {
                continue;
            }
            var leaveChance = leaveProbability + (0.5 - inter.FitScore) * 0.2;
            if (_rng.NextDouble() < System.Math.Max(0.0, leaveChance))
            {
                inter.Committed = false;
                inter.OfferMade = true;
                inter.Interest = System.Math.Max(inter.Interest * 0.6, 0.2);
                reopened.Add(inter);
            }
        }
        return reopened;
    }

    private double NoisyRating(double trueRating, int? classRank)
    {
        var noise = (_rng.NextDouble() - 0.5) * 5.0;
        var rankNoise = classRank.HasValue ? (_rng.NextDouble() - 0.5) * 0.1 * classRank.Value : 0.0;
        return System.Math.Max(25.0, System.Math.Min(99.0, trueRating + noise - rankNoise * 0.1));
    }
}
