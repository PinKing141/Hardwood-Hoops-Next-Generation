using System.Collections.Generic;
using System.Linq;
using HardwoodHoops.Core.Domain.Recruiting;

namespace HardwoodHoops.Core.App.Services.Recruiting;

public sealed class RecruitingRankingDataService
{
    private readonly List<RecruitingRankingEntry> _entries;

    public RecruitingRankingDataService()
    {
        _entries = BuildMockEntries();
    }

    public IReadOnlyList<RecruitingRankingEntry> GetTop100(int classYear)
    {
        var list = _entries
            .Where(e => e.ClassYear == classYear)
            .OrderBy(e => e.Rank)
            .ToList();

        if (RecruitingRankingContext.TryGet(classYear, out var current))
        {
            var idx = list.FindIndex(e => e.PlayerName == current.PlayerName);
            if (current.Rank is > 0 and <= 100)
            {
                if (idx >= 0)
                {
                    list[idx] = current;
                }
                else
                {
                    list.Add(current);
                }

                list = list.OrderBy(e => e.Rank).ToList();
            }
        }

        return list.Take(100).ToList();
    }

    public IReadOnlyList<RecruitingRankingEntry> GetBand(int classYear, int maxRank)
    {
        return GetTop100(classYear).Where(e => e.Rank <= maxRank).ToList();
    }

    public RecruitingRankingEntry GetHighlighted(int classYear)
    {
        if (RecruitingRankingContext.TryGet(classYear, out var current) && current.Rank is > 0 and <= 100)
        {
            return current;
        }

        return GetTop100(classYear).First();
    }

    private static List<RecruitingRankingEntry> BuildMockEntries()
    {
        return new List<RecruitingRankingEntry>
        {
            new(1, "Cameron Whitmore", "SG", 77, 198, "Mount Verde (FL)", "Duke", 5, RecruitTrend.Rising, "2 Way 3 Level Wing", new[] { "Floor Spacer", "Shot Creator" }, new string[0], 2027, 0.28f, 0.34f, 0.38f, 0.31f, 0.29f, 0.40f, 0.58f, 0.42f),
            new(2, "Elijah Brooks", "PG", 74, 175, "Sierra Canyon (CA)", "Uncomm", 4, RecruitTrend.Stable, "Playmaker", new[] { "Playmaker" }, new[] { "UCLA", "Arizona" }, 2027, 0.32f, 0.33f, 0.35f, 0.36f, 0.28f, 0.36f, 0.68f, 0.32f),
            new(3, "Malik Bryant", "PG", 76, 182, "Oak Hill (VA)", "Kansas", 4, RecruitTrend.Stable, "Shot Creator", new[] { "Shot Creator" }, new[] { "Kansas" }, 2027, 0.30f, 0.32f, 0.38f, 0.30f, 0.33f, 0.37f, 0.62f, 0.38f),
            new(4, "Jamal Lawson II", "SF", 81, 215, "Prolific Prep (CA)", "Kentucky", 5, RecruitTrend.Rising, "2 Way Wing", new[] { "Lockdown" }, new[] { "Kentucky" }, 2027, 0.33f, 0.34f, 0.33f, 0.28f, 0.26f, 0.46f, 0.54f, 0.46f),
            new(5, "Curtis Hudson", "C", 83, 240, "Sunrise Christian (KS)", "Uncomm", 5, RecruitTrend.Stable, "Rim Protector", new[] { "Rim Protector", "Glass Cleaner" }, new[] { "Kansas", "Baylor" }, 2027, 0.45f, 0.32f, 0.23f, 0.42f, 0.18f, 0.40f, 0.40f, 0.60f),
            new(6, "Kameron Keffer", "SG", 78, 205, "Link Academy (MO)", "UConn", 4, RecruitTrend.Stable, "3 Level", new[] { "Floor Spacer" }, new[] { "UConn" }, 2027, 0.28f, 0.34f, 0.38f, 0.40f, 0.28f, 0.32f, 0.64f, 0.36f),
            new(7, "Favour Ezeh", "SG", 78, 218, "Dagenham Prep (FL)", "Uncomm", 4, RecruitTrend.Rising, "2 Way 3 Level Wing", new[] { "Rim Pressure", "Lockdown" }, new[] { "Florida", "Oregon", "Auburn" }, 2027, 0.28f, 0.34f, 0.38f, 0.31f, 0.29f, 0.40f, 0.62f, 0.38f),
            new(8, "Roy Harping", "PF", 81, 225, "Duncanville (TX)", "Alabama", 4, RecruitTrend.Stable, "Inside Out", new[] { "Rim Pressure" }, new[] { "Alabama" }, 2027, 0.36f, 0.32f, 0.32f, 0.26f, 0.24f, 0.50f, 0.55f, 0.45f),
            new(9, "Jaylen Mercer", "SG", 78, 200, "IMG Academy (FL)", "Uncomm", 4, RecruitTrend.Stable, "Shot Creator", new[] { "Shot Creator" }, new[] { "UNC", "Texas" }, 2027, 0.30f, 0.33f, 0.37f, 0.28f, 0.34f, 0.38f, 0.60f, 0.40f),
            new(10, "Eli Harris", "PG", 75, 170, "La Lumiere (IN)", "Michigan", 4, RecruitTrend.Stable, "Playmaker", new[] { "Playmaker" }, new[] { "Michigan" }, 2027, 0.32f, 0.33f, 0.35f, 0.36f, 0.30f, 0.34f, 0.70f, 0.30f)
        };
    }
}
