using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Career;

namespace HardwoodHoops.Core.Domain.Career;

public sealed class FeaturedGameEntry
{
    public FeaturedGameEntry(int week, string opponent, CareerStage stage, bool isFeatured, bool isTelevised)
    {
        Week = week;
        Opponent = opponent;
        Stage = stage;
        IsFeatured = isFeatured;
        IsTelevised = isTelevised;
    }

    public int Week { get; }
    public string Opponent { get; }
    public CareerStage Stage { get; }
    public bool IsFeatured { get; }
    public bool IsTelevised { get; }
}

public sealed class FeaturedGameCalendar
{
    public FeaturedGameCalendar(IReadOnlyList<FeaturedGameEntry> games)
    {
        Games = games;
    }

    public IReadOnlyList<FeaturedGameEntry> Games { get; }
}
