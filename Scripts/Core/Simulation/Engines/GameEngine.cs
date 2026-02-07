using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Games;

namespace HardwoodHoops.Core.Simulation.Engines;

public sealed class GameEngine : IGameEngine<GameState, GameEvent>
{
    private readonly PossessionEngine _possessionEngine;

    public GameEngine(PossessionEngine possessionEngine)
    {
        _possessionEngine = possessionEngine;
    }

    public IReadOnlyList<GameEvent> Simulate(GameState gameState)
    {
        var events = new List<GameEvent>();
        EnsureLineups(gameState);
        var possessions = 20;
        for (var i = 0; i < possessions; i++)
        {
            var offense = i % 2 == 0 ? gameState.HomeTeamId : gameState.AwayTeamId;
            var defense = i % 2 == 0 ? gameState.AwayTeamId : gameState.HomeTeamId;
            var offenseLineup = gameState.OnFloor.GetValueOrDefault(offense, new List<string>());
            var defenseLineup = gameState.OnFloor.GetValueOrDefault(defense, new List<string>());

            if (offenseLineup.Count == 0)
            {
                continue;
            }

            var possessionEvents = _possessionEngine.RunPossession(
                gameState,
                offense,
                defense,
                offenseLineup,
                defenseLineup);

            foreach (var gameEvent in possessionEvents)
            {
                ApplyEvent(gameState, gameEvent);
                events.Add(gameEvent);
            }

            TickFatigue(gameState);
            gameState.ClockSeconds = System.Math.Max(0, gameState.ClockSeconds - 24);
            if (gameState.ClockSeconds == 0)
            {
                break;
            }
        }

        return events;
    }

    private static void EnsureLineups(GameState gameState)
    {
        foreach (var (teamId, roster) in gameState.Rosters)
        {
            if (gameState.OnFloor.ContainsKey(teamId))
            {
                continue;
            }

            var starters = roster.Count > 5 ? roster.GetRange(0, 5) : new List<string>(roster);
            var bench = roster.Count > 5 ? roster.GetRange(5, roster.Count - 5) : new List<string>();
            gameState.OnFloor[teamId] = starters;
            gameState.Bench[teamId] = bench;
            foreach (var playerId in roster)
            {
                gameState.FatigueByPlayer.TryAdd(playerId, 0.0);
                gameState.FoulsByPlayer.TryAdd(playerId, 0);
                gameState.Injuries.TryAdd(playerId, false);
                gameState.MinutesPlayed.TryAdd(playerId, 0.0);
            }

            gameState.TeamFouls.TryAdd(teamId, 0);
        }
    }

    private static void TickFatigue(GameState gameState)
    {
        const double possessionMinutes = 24.0 / 60.0;
        foreach (var (teamId, lineup) in gameState.OnFloor)
        {
            foreach (var playerId in lineup)
            {
                gameState.FatigueByPlayer[playerId] = gameState.FatigueByPlayer.GetValueOrDefault(playerId, 0.0) + 5.0;
                gameState.MinutesPlayed[playerId] = gameState.MinutesPlayed.GetValueOrDefault(playerId, 0.0) + possessionMinutes;
            }

            foreach (var playerId in gameState.Bench.GetValueOrDefault(teamId, new List<string>()))
            {
                gameState.FatigueByPlayer[playerId] = System.Math.Max(gameState.FatigueByPlayer.GetValueOrDefault(playerId, 0.0) - 3.0, 0.0);
            }
        }
    }

    private static void ApplyEvent(GameState gameState, GameEvent gameEvent)
    {
        gameState.RecordEvent(gameEvent);
        if (gameEvent.EventType == "shot_made")
        {
            var payload = gameEvent.Payload;
            var teamId = payload.TryGetValue("team_id", out var teamObj) ? teamObj?.ToString() : null;
            var points = payload.TryGetValue("points", out var ptsObj) ? System.Convert.ToInt32(ptsObj) : 0;
            if (teamId == gameState.HomeTeamId)
            {
                gameState.Score["home"] += points;
            }
            else if (teamId == gameState.AwayTeamId)
            {
                gameState.Score["away"] += points;
            }
        }
        else if (gameEvent.EventType == "foul")
        {
            var payload = gameEvent.Payload;
            var playerId = payload.TryGetValue("player_id", out var playerObj) ? playerObj?.ToString() : null;
            if (!string.IsNullOrWhiteSpace(playerId))
            {
                gameState.FoulsByPlayer[playerId] = gameState.FoulsByPlayer.GetValueOrDefault(playerId, 0) + 1;
            }

            var teamId = payload.TryGetValue("team_id", out var teamObj) ? teamObj?.ToString() : null;
            if (!string.IsNullOrWhiteSpace(teamId))
            {
                gameState.TeamFouls[teamId] = gameState.TeamFouls.GetValueOrDefault(teamId, 0) + 1;
            }
        }
    }
}
