using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Career;

namespace HardwoodHoops.Core.App.Services;

public static class FeaturedGameTracker
{
    private static int _featuredGamesPlayed;
    private static readonly List<CareerScheduleCheckpoint> Schedule = new CareerScheduleService().BuildDefaultSchedule();

    public static int FeaturedGamesPlayed => _featuredGamesPlayed;
    public static int TotalFeaturedGames => Schedule.Count;
    public static bool HasUpcomingFeatured => _featuredGamesPlayed < Schedule.Count;

    public static void Increment()
    {
        if (_featuredGamesPlayed < Schedule.Count)
        {
            _featuredGamesPlayed++;
        }
    }

    public static void Reset()
    {
        _featuredGamesPlayed = 0;
    }
}
