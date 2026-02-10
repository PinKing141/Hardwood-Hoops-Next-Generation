using System;
using System.Collections.Generic;
using Godot;
using HardwoodHoops.Core;
using HardwoodHoops.Core.Domain.Games;
using HardwoodHoops.Core.Infra.Persistence.Local;
using HardwoodHoops.Core.Profiles;
using HardwoodHoops.Core.Simulation;

namespace HardwoodHoops.Diagnostics;

public sealed class ValidationReport
{
    public List<string> Errors { get; } = new();
    public List<string> Warnings { get; } = new();
    public bool IsOk => Errors.Count == 0;
}

public static class ValidationRunner
{
    public static ValidationReport RunAll()
    {
        var report = new ValidationReport();
        RunPersistenceChecks(report);
        RunUiContractChecks(report);
        RunSimulationSmoke(report);
        return report;
    }

    private static void RunPersistenceChecks(ValidationReport report)
    {
        var repo = new JsonGameRepository();
        var gameId = $"VALID-{Guid.NewGuid():N}";
        var state = new GameState(gameId, "HOME", "AWAY");
        state.RecordEvent(new GameEvent("tip", "Tip off", new Dictionary<string, object>(), 0));

        try
        {
            repo.Save(state);
            var loaded = repo.GetById(gameId);
            if (loaded is null || loaded.GameId != gameId)
            {
                report.Errors.Add("Persistence: GameState round-trip failed.");
            }
        }
        catch (Exception ex)
        {
            report.Errors.Add($"Persistence: exception during save/load - {ex.Message}");
        }
    }

    private static void RunUiContractChecks(ValidationReport report)
    {
        CheckScene(report, "res://Scenes/Main.tscn", new[]
        {
            "Margin/Tabs/LiveFeed/Feed",
            "Margin/Tabs/LiveFeed/Header/Clock",
            "Margin/Tabs/LiveFeed/Score",
            "Margin/Tabs/LockerRoom/PlayerHeader/NameLabel",
            "Margin/Tabs/LockerRoom/PlayerHeader/PositionLabel",
            "Margin/Tabs/LockerRoom/PlayerHeader/CareerLabel",
            "Margin/Tabs/LockerRoom/PlayerHeader/HypeLabel",
            "Margin/Tabs/LockerRoom/PlayerHeader/StarsLabel",
            "Margin/Tabs/LockerRoom/PlayerHeader/RankLabel",
            "Margin/Tabs/LockerRoom/PlayerHeader/TrendLabel",
            "Margin/Tabs/LockerRoom/OvrSection/OvrRow/PublicOvrBox/PublicOvrValue",
            "Margin/Tabs/LockerRoom/OvrSection/OvrRow/PrivateOvrBox/PrivateOvrValue",
            "Margin/Tabs/LockerRoom/ArchetypeLabel",
            "Margin/Tabs/LockerRoom/AttributeScroll/AttributeGrid",
            "Margin/Tabs/Scouting/ScoutingDetail",
            "Margin/Tabs/ShotDiet/ShotDietSummary",
            "Margin/Tabs/ShotDiet/ShotDietDetail"
        });

        CheckScene(report, "res://Scenes/MainMenu.tscn", new[]
        {
            "Center/Options/NewGameButton",
            "Center/Options/LoadGameButton",
            "Center/Options/SettingsButton",
            "Center/Options/ExitButton"
        });

        CheckScene(report, "res://Scenes/CharacterCreation.tscn", new[]
        {
            "Root/Scroll/Content/Fields/NameRow/NameInput",
            "Root/Scroll/Content/Fields/PositionRow/PositionOption",
            "Root/Actions/BackButton",
            "Root/Actions/StartButton"
        });
    }

    private static void CheckScene(ValidationReport report, string scenePath, string[] requiredNodes)
    {
        var packed = ResourceLoader.Load<PackedScene>(scenePath);
        if (packed is null)
        {
            report.Errors.Add($"UI: missing scene {scenePath}");
            return;
        }

        using var instance = packed.Instantiate();
        foreach (var nodePath in requiredNodes)
        {
            if (instance.GetNodeOrNull(nodePath) is null)
            {
                report.Errors.Add($"UI: missing node {nodePath} in {scenePath}");
            }
        }
    }

    private static void RunSimulationSmoke(ValidationReport report)
    {
        try
        {
            var rng = new Random(7);
            var player = PlayerProfile.CreateSample("Test", Position.PointGuard, CareerPhase.HighSchool);
            var defender = PlayerProfile.CreateSample("Defender", Position.ShootingGuard, CareerPhase.HighSchool);
            var simulation = new SimulationEngine();

            var score = 0;
            for (var i = 0; i < 10; i++)
            {
                var gameEvent = simulation.SimulatePossession(player, defender, rng);
                score += Math.Max(0, gameEvent.Points);
            }

            if (score < 0)
            {
                report.Errors.Add("Simulation: score underflow.");
            }
        }
        catch (Exception ex)
        {
            report.Errors.Add($"Simulation: exception - {ex.Message}");
        }
    }
}
