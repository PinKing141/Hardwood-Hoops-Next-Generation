using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Recruiting;

namespace HardwoodHoops.Core.App.Services.Recruiting;

public static class RecruitingRankingContext
{
    public static RecruitingRankingEntry? CurrentEntry { get; private set; }

    public static void UpdateCurrent(RecruitingRankingEntry entry)
    {
        CurrentEntry = entry;
    }

    public static void Clear()
    {
        CurrentEntry = null;
    }

    public static bool TryGet(int classYear, out RecruitingRankingEntry entry)
    {
        if (CurrentEntry is not null && CurrentEntry.ClassYear == classYear)
        {
            entry = CurrentEntry;
            return true;
        }

        entry = null!;
        return false;
    }
}
