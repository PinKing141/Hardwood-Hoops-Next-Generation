using System;
using System.Collections.Generic;

namespace HardwoodHoops.Core.App.Services;

public sealed record GameBoxScore(
    DateTime PlayedOn,
    string Opponent,
    int HomeScore,
    int AwayScore,
    string PlayerLine,
    bool IsFeatured);

public static class BoxScoreHistory
{
    private static readonly List<GameBoxScore> GamesInternal = new();

    public static IReadOnlyList<GameBoxScore> Games => GamesInternal;

    public static void Add(GameBoxScore entry)
    {
        if (entry is null)
        {
            return;
        }

        GamesInternal.Add(entry);
    }

    public static void Reset()
    {
        GamesInternal.Clear();
    }
}
