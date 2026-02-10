using System;
using System.Collections.Generic;

namespace HardwoodHoops.Core.Domain.Recruiting;

public enum RecruitTrend
{
    Rising,
    Stable,
    Falling
}

public enum PerformanceDelta
{
    MajorPositive,
    Positive,
    Neutral,
    Negative,
    MajorNegative
}

public enum RecruitingStage
{
    JuniorHighSchool,
    AauCircuit,
    SeniorHighSchool
}

public enum FeaturedImportance
{
    RegularSeason,
    Playoff
}

public sealed class ProspectProfile
{
    private readonly Queue<PerformanceDelta> _recentDeltas = new();
    private int _rankUpdateStreak;

    public ProspectProfile(string playerId, int classYear)
    {
        PlayerId = playerId;
        ClassYear = classYear;
        ExposureScore = 45;
        InternalStars = 3;
        Trend = RecruitTrend.Stable;
        HypePoints = 50;
    }

    public string PlayerId { get; }
    public int ClassYear { get; }
    public int ExposureScore { get; private set; }
    public int InternalStars { get; private set; }
    public int VisibleStars => Math.Clamp(InternalStars, 3, 5);
    public int? NationalRank { get; private set; }
    public RecruitTrend Trend { get; private set; }
    public int HypePoints { get; private set; }
    public string? LastUpdateMessage { get; private set; }

    public void ApplyCheckpoint(RecruitingCheckpointResult result, RecruitingCheckpointInput input)
    {
        LastUpdateMessage = null;
        ExposureScore = Clamp(ExposureScore + result.ExposureDelta, 0, 100);
        UpdateMomentum(result.Performance);
        if (input.IsStarUpdate)
        {
            UpdateStars(result, input);
        }
        if (input.IsRankingUpdate)
        {
            UpdateRank(result, input);
        }
        UpdateHype();
    }

    public void ApplyInactivityDecay()
    {
        var decay = NationalRank.HasValue ? 1 : 2;
        ExposureScore = Clamp(ExposureScore - decay, 0, 100);
        UpdateHype();
    }

    private void UpdateMomentum(PerformanceDelta delta)
    {
        _recentDeltas.Enqueue(delta);
        while (_recentDeltas.Count > 3)
        {
            _recentDeltas.Dequeue();
        }

        var score = 0;
        foreach (var entry in _recentDeltas)
        {
            score += entry switch
            {
                PerformanceDelta.MajorPositive => 2,
                PerformanceDelta.Positive => 1,
                PerformanceDelta.Negative => -1,
                PerformanceDelta.MajorNegative => -2,
                _ => 0
            };
        }

        Trend = score switch
        {
            >= 2 => RecruitTrend.Rising,
            <= -2 => RecruitTrend.Falling,
            _ => RecruitTrend.Stable
        };
    }

    private void UpdateStars(RecruitingCheckpointResult result, RecruitingCheckpointInput input)
    {
        var previous = InternalStars;
        var promoted = false;

        if (InternalStars <= 3)
        {
            if (NationalRank.HasValue || (input.Stage == RecruitingStage.AauCircuit && result.Performance >= PerformanceDelta.Positive))
            {
                InternalStars = 4;
                promoted = true;
            }
        }
        else if (InternalStars == 4)
        {
            if (NationalRank.HasValue && NationalRank.Value <= 25 && Trend == RecruitTrend.Rising && ExposureScore >= 85)
            {
                InternalStars = 5;
                promoted = true;
            }
        }

        if (!promoted && InternalStars >= 4)
        {
            if (Trend == RecruitTrend.Falling && ExposureScore < (InternalStars == 5 ? 78 : 60))
            {
                InternalStars -= 1;
            }
        }

        InternalStars = Math.Clamp(InternalStars, 0, 5);
        if (InternalStars != previous)
        {
            LastUpdateMessage = $"Star rating updated to {VisibleStars}-star.";
        }
    }

    private void UpdateRank(RecruitingCheckpointResult result, RecruitingCheckpointInput input)
    {
        var eligible = ExposureScore >= 60
            && result.Performance is PerformanceDelta.MajorPositive or PerformanceDelta.Positive
            && Trend != RecruitTrend.Falling;

        if (!eligible)
        {
            if (NationalRank.HasValue)
            {
                var drop = result.Performance is PerformanceDelta.MajorNegative ? 8 : 4;
                NationalRank = Math.Min(100, NationalRank.Value + drop);
                if (NationalRank > 100 || ExposureScore < 55)
                {
                    NationalRank = null;
                    LastUpdateMessage = "Fell out of the National Top 100.";
                }
            }
            return;
        }

        var projected = 110 - (ExposureScore - 55) * 2;
        if (Trend == RecruitTrend.Rising)
        {
            projected -= 4;
        }
        else if (Trend == RecruitTrend.Falling)
        {
            projected += 4;
        }

        var clamped = Clamp(projected, 1, 100);

        if (!NationalRank.HasValue)
        {
            var entryBandMin = input.HighVisibility && result.Performance == PerformanceDelta.MajorPositive ? 26 : 51;
            var entryBandMax = input.HighVisibility && result.Performance == PerformanceDelta.MajorPositive ? 50 : 100;
            NationalRank = Clamp(clamped, entryBandMin, entryBandMax);
            _rankUpdateStreak = 1;
            LastUpdateMessage = "Entered the National Top 100.";
            return;
        }

        var band = RankBandFor(NationalRank.Value);
        var canCross = input.HighVisibility && result.Performance == PerformanceDelta.MajorPositive;
        var targetBand = canCross ? BetterBand(band) : band;
        var bandRange = BandRange(targetBand);
        var withinBand = Clamp(clamped, bandRange.min, bandRange.max);
        var maxShift = 8;
        var bounded = Clamp(withinBand, NationalRank.Value - maxShift, NationalRank.Value + maxShift);
        NationalRank = bounded;
        _rankUpdateStreak++;
    }

    private void UpdateHype()
    {
        var trendBonus = Trend switch
        {
            RecruitTrend.Rising => 8,
            RecruitTrend.Falling => -8,
            _ => 0
        };

        HypePoints = Clamp((int)Math.Round(ExposureScore * 1.1) + (InternalStars * 4) + trendBonus, 0, 120);
    }

    private static int Clamp(int value, int min, int max)
    {
        return Math.Clamp(value, min, max);
    }

    private static int RankBandFor(int rank)
    {
        if (rank <= 10) return 10;
        if (rank <= 25) return 25;
        if (rank <= 50) return 50;
        return 100;
    }

    private static int BetterBand(int band)
    {
        return band switch
        {
            100 => 50,
            50 => 25,
            25 => 10,
            _ => 10
        };
    }

    private static (int min, int max) BandRange(int band)
    {
        return band switch
        {
            10 => (1, 10),
            25 => (11, 25),
            50 => (26, 50),
            _ => (51, 100)
        };
    }
}

public readonly struct RecruitingCheckpointInput
{
    public RecruitingCheckpointInput(
        RecruitingStage stage,
        FeaturedImportance importance,
        bool scoutPresence,
        PerformanceDelta performance,
        int opponentQuality,
        bool isRankingUpdate = false,
        bool isStarUpdate = false,
        bool highVisibility = false)
    {
        Stage = stage;
        Importance = importance;
        ScoutPresence = scoutPresence;
        Performance = performance;
        OpponentQuality = opponentQuality;
        IsRankingUpdate = isRankingUpdate;
        IsStarUpdate = isStarUpdate;
        HighVisibility = highVisibility;
    }

    public RecruitingStage Stage { get; }
    public FeaturedImportance Importance { get; }
    public bool ScoutPresence { get; }
    public PerformanceDelta Performance { get; }
    public int OpponentQuality { get; }
    public bool IsRankingUpdate { get; }
    public bool IsStarUpdate { get; }
    public bool HighVisibility { get; }
}

public readonly struct RecruitingCheckpointResult
{
    public RecruitingCheckpointResult(int exposureDelta, PerformanceDelta performance)
    {
        ExposureDelta = exposureDelta;
        Performance = performance;
    }

    public int ExposureDelta { get; }
    public PerformanceDelta Performance { get; }
}
