using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Career;

namespace HardwoodHoops.Core.App.Services;

public sealed class FeaturedGameCalendarService
{
    public FeaturedGameCalendar BuildSampleCalendar()
    {
        var games = new List<FeaturedGameEntry>();
        var week = 1;

        AddStage(games, CareerStage.JuniorHighSchool, ref week, 10, 3);
        AddStage(games, CareerStage.AauCircuit, ref week, 8, 4, televised: true);
        AddStage(games, CareerStage.SeniorHighSchool, ref week, 12, 4, televised: true);

        return new FeaturedGameCalendar(games);
    }

    public FeaturedGameCalendar BuildFromSchedule(IReadOnlyList<Domain.Career.CareerCheckpoint> schedule)
    {
        var games = new List<FeaturedGameEntry>();
        var week = 1;
        foreach (var checkpoint in schedule)
        {
            games.Add(new FeaturedGameEntry(
                week,
                $"Opponent {week}",
                checkpoint.Stage,
                checkpoint.IsFeatured,
                checkpoint.HighVisibility));
            week++;
        }

        return new FeaturedGameCalendar(games);
    }

    private static void AddStage(
        List<FeaturedGameEntry> games,
        CareerStage stage,
        ref int week,
        int totalGames,
        int featuredGames,
        bool televised = false)
    {
        for (var i = 0; i < totalGames; i++)
        {
            var isFeatured = i < featuredGames;
            games.Add(new FeaturedGameEntry(
                week,
                $"Opponent {week}",
                stage,
                isFeatured,
                televised && isFeatured && i % 2 == 0));
            week++;
        }
    }
}
