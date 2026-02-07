using System.Collections.Generic;

namespace HardwoodHoops.Core.Integration;

public record IntegrationMappingEntry(string Source, string Target, string Notes);

public static class IntegrationMapping
{
    public static IReadOnlyList<IntegrationMappingEntry> DomainEntries { get; } = new[]
    {
        new IntegrationMappingEntry("courthoops/domain/player/entity.py", "Domain/Players/Player.cs", "Player + attributes/tendencies/personality models."),
        new IntegrationMappingEntry("courthoops/domain/player/overall.py", "Domain/Players/OverallCalculator.cs", "True/public overall logic."),
        new IntegrationMappingEntry("courthoops/domain/team/entity.py", "Domain/Teams/Team.cs", "Team model and roster."),
        new IntegrationMappingEntry("courthoops/domain/game/state.py", "Domain/Games/GameState.cs", "Game state with events, fatigue, fouls."),
        new IntegrationMappingEntry("courthoops/domain/game/events.py", "Domain/Games/Event.cs", "Event type + payload."),
        new IntegrationMappingEntry("courthoops/domain/recruiting/models.py", "Domain/Recruiting/RecruitingInterest.cs", "Interest + commitment models."),
    };

    public static IReadOnlyList<IntegrationMappingEntry> SimulationEntries { get; } = new[]
    {
        new IntegrationMappingEntry("courthoops/simulation/engine/game_engine.py", "Simulation/Engines/GameEngine.cs", "Possession loop and clock control."),
        new IntegrationMappingEntry("courthoops/simulation/engine/possession_engine.py", "Simulation/Engines/PossessionEngine.cs", "Play selection + event flow."),
        new IntegrationMappingEntry("courthoops/simulation/engine/shot_engine.py", "Simulation/Engines/ShotEngine.cs", "Shot resolution + free throws."),
        new IntegrationMappingEntry("courthoops/simulation/engine/foul_engine.py", "Simulation/Engines/FoulEngine.cs", "Foul checks + bonus logic."),
        new IntegrationMappingEntry("courthoops/simulation/engine/rebound_engine.py", "Simulation/Engines/ReboundEngine.cs", "Rebound resolution."),
    };

    public static IReadOnlyList<IntegrationMappingEntry> ServiceEntries { get; } = new[]
    {
        new IntegrationMappingEntry("courthoops/app/services/world_pipeline_service.py", "App/Services/WorldPipelineService.cs", "Offseason pipeline."),
        new IntegrationMappingEntry("courthoops/app/services/recruiting_service.py", "App/Services/RecruitingService.cs", "Interest/visits/commitments."),
        new IntegrationMappingEntry("courthoops/app/services/progression_service.py", "App/Services/ProgressionService.cs", "Growth + decline."),
        new IntegrationMappingEntry("courthoops/app/services/injury_service.py", "App/Services/InjuryService.cs", "Injury + recovery."),
        new IntegrationMappingEntry("courthoops/app/services/season_service.py", "App/Services/SeasonService.cs", "Schedule simulation + box scores."),
        new IntegrationMappingEntry("courthoops/app/services/role_affinity_service.py", "App/Services/RoleAffinityService.cs", "Role affinities."),
        new IntegrationMappingEntry("courthoops/app/services/build_name_service.py", "App/Services/BuildNameService.cs", "Build naming rules."),
        new IntegrationMappingEntry("courthoops/app/services/scouting_service.py", "App/Services/ScoutingService.cs", "Scouting reports."),
        new IntegrationMappingEntry("courthoops/app/services/player_evaluation_service.py", "App/Services/PlayerEvaluationService.cs", "OVR evaluation."),
    };

    public static IReadOnlyList<IntegrationMappingEntry> UiEntries { get; } = new[]
    {
        new IntegrationMappingEntry("NextToAdd.md", "UI/Recruiting/ClassRankingsView.*", "Class rankings banded UI."),
        new IntegrationMappingEntry("NextToAdd.md", "UI/Scouting/ShotDietView.*", "Shot diet preference UI."),
    };

    public static IReadOnlyList<IntegrationMappingEntry> InfraEntries { get; } = new[]
    {
        new IntegrationMappingEntry("courthoops/infra/utils/rng.py", "Simulation/Rng/IRng.cs", "Deterministic RNG abstraction."),
    };

    public static IReadOnlyList<string> ExplicitExclusions { get; } = new[]
    {
        "courthoops/infra/persistence/* (SQLAlchemy/Alembic specifics)",
        "courthoops/cli/* (Textual CLI)",
        "courthoops/tests/* (Python test suite)",
        "courthoops/data/* (large name pools)",
    };
}
