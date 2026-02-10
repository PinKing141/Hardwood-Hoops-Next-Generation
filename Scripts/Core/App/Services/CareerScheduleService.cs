using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Career;
using HardwoodHoops.Core.Domain.Recruiting;

namespace HardwoodHoops.Core.App.Services;

public sealed class CareerScheduleService
{
    public IReadOnlyList<CareerCheckpoint> BuildDefaultSchedule()
    {
        var checkpoints = new List<CareerCheckpoint>();

        AddStage(checkpoints, CareerStage.JuniorHighSchool, regularCount: 7, playoffCount: 2, scoutPresence: false, highVisibility: false);
        AddAauStage(checkpoints, events: 3, gamesPerEvent: 2);
        AddSeniorStage(checkpoints, regularCount: 8, playoffCount: 3);

        return checkpoints;
    }

    private static void AddStage(
        List<CareerCheckpoint> checkpoints,
        CareerStage stage,
        int regularCount,
        int playoffCount,
        bool scoutPresence,
        bool highVisibility)
    {
        for (var i = 0; i < regularCount; i++)
        {
            checkpoints.Add(new CareerCheckpoint(
                stage,
                FeaturedImportance.RegularSeason,
                scoutPresence,
                highVisibility,
                isRankingUpdate: false,
                isStarUpdate: false,
                isFeatured: true));
        }

        for (var i = 0; i < playoffCount; i++)
        {
            checkpoints.Add(new CareerCheckpoint(
                stage,
                FeaturedImportance.Playoff,
                scoutPresence: true,
                highVisibility: true,
                isRankingUpdate: false,
                isStarUpdate: false,
                isFeatured: true));
        }
    }

    private static void AddAauStage(List<CareerCheckpoint> checkpoints, int events, int gamesPerEvent)
    {
        for (var evt = 0; evt < events; evt++)
        {
            for (var game = 0; game < gamesPerEvent; game++)
            {
                var isEventEnd = game == gamesPerEvent - 1;
                var isFinalEvent = evt == events - 1 && isEventEnd;
                checkpoints.Add(new CareerCheckpoint(
                    CareerStage.AauCircuit,
                    FeaturedImportance.RegularSeason,
                    scoutPresence: true,
                    highVisibility: true,
                    isRankingUpdate: isEventEnd,
                    isStarUpdate: isFinalEvent,
                    isFeatured: true));
            }
        }
    }

    private static void AddSeniorStage(List<CareerCheckpoint> checkpoints, int regularCount, int playoffCount)
    {
        for (var i = 0; i < regularCount; i++)
        {
            var midSeason = i == 3;
            var endRegular = i == regularCount - 1;
            checkpoints.Add(new CareerCheckpoint(
                CareerStage.SeniorHighSchool,
                FeaturedImportance.RegularSeason,
                scoutPresence: true,
                highVisibility: true,
                isRankingUpdate: midSeason || endRegular,
                isStarUpdate: midSeason || endRegular,
                isFeatured: true));
        }

        for (var i = 0; i < playoffCount; i++)
        {
            checkpoints.Add(new CareerCheckpoint(
                CareerStage.SeniorHighSchool,
                FeaturedImportance.Playoff,
                scoutPresence: true,
                highVisibility: true,
                isRankingUpdate: false,
                isStarUpdate: false,
                isFeatured: true));
        }
    }
}
