using System;
using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Games;
using HardwoodHoops.Core.Domain.Players;
using HardwoodHoops.Core.Infra.Persistence;
using HardwoodHoops.Core.Simulation.Engines;

namespace HardwoodHoops.Core.App.Services;

public sealed class SeasonService
{
    private readonly IGameRepository<GameState> _gameRepo;
    private readonly IPlayByPlayRepository<GameEvent> _pbpRepo;
    private readonly IBoxScoreRepository<BoxScore> _boxScoreRepo;
    private readonly IGameEngineFactory<GameState, GameEvent> _engineFactory;
    private readonly InjuryService _injuryService;

    public SeasonService(
        IGameRepository<GameState> gameRepo,
        IPlayByPlayRepository<GameEvent> pbpRepo,
        IBoxScoreRepository<BoxScore> boxScoreRepo,
        IGameEngineFactory<GameState, GameEvent> engineFactory,
        InjuryService? injuryService = null)
    {
        _gameRepo = gameRepo;
        _pbpRepo = pbpRepo;
        _boxScoreRepo = boxScoreRepo;
        _engineFactory = engineFactory;
        _injuryService = injuryService ?? new InjuryService();
    }

    public List<BoxScore> SimulateSchedule(
        IEnumerable<(string gameId, string homeTeamId, string awayTeamId)> schedule,
        Dictionary<string, List<string>> rosters,
        Dictionary<string, Player> playerLookup,
        bool fatigueCarryover = true,
        bool injuryRecovery = true)
    {
        var boxScores = new List<BoxScore>();
        var fatigueState = new Dictionary<string, double>();
        var injuryState = new Dictionary<string, bool>();
        var injuryDaysState = new Dictionary<string, int>();

        foreach (var (gameId, homeId, awayId) in schedule)
        {
            var gameState = new GameState(gameId, homeId, awayId)
            {
                Rosters = new Dictionary<string, List<string>>(rosters)
            };

            if (fatigueCarryover)
            {
                foreach (var (pid, value) in fatigueState)
                {
                    gameState.FatigueByPlayer[pid] = value;
                }
                foreach (var (pid, hurt) in injuryState)
                {
                    gameState.Injuries[pid] = hurt;
                }
                foreach (var (pid, days) in injuryDaysState)
                {
                    if (playerLookup.TryGetValue(pid, out var player))
                    {
                        player.InjuryDays = days;
                        player.Injured = injuryState.GetValueOrDefault(pid, false);
                    }
                }
            }

            var injuries = _injuryService.ApplyGameInjuries(playerLookup.Values, gameState.FatigueByPlayer);
            foreach (var (pid, duration) in injuries)
            {
                gameState.Injuries[pid] = true;
                if (playerLookup.TryGetValue(pid, out var player))
                {
                    player.InjuryDays = Math.Max(player.InjuryDays, duration);
                    player.Injured = true;
                }
            }

            var engine = _engineFactory.Create(new GameEngineContext<GameState>(gameState, new Dictionary<string, object>()));
            var events = engine.Simulate(gameState);
            _pbpRepo.SaveEvents(gameId, events);
            _gameRepo.Save(gameState);

            var payload = BuildBoxScorePayload(gameState, events);
            var boxScore = new BoxScore(
                gameId,
                homeId,
                awayId,
                gameState.Score["home"],
                gameState.Score["away"],
                payload);
            _boxScoreRepo.Save(boxScore);
            boxScores.Add(boxScore);

            if (fatigueCarryover)
            {
                fatigueState = new Dictionary<string, double>(gameState.FatigueByPlayer);
                injuryState = new Dictionary<string, bool>(gameState.Injuries);
                if (injuryRecovery)
                {
                    var recovered = _injuryService.ApplySeasonRecovery(playerLookup.Values);
                    foreach (var (pid, recoveredNow) in recovered)
                    {
                        if (recoveredNow)
                        {
                            injuryState[pid] = false;
                        }
                        injuryDaysState[pid] = playerLookup.TryGetValue(pid, out var player) ? player.InjuryDays : 0;
                    }
                }
            }
        }

        return boxScores;
    }

    private static Dictionary<string, object> BuildBoxScorePayload(GameState gameState, IReadOnlyList<GameEvent> events)
    {
        var playerTeam = new Dictionary<string, string>();
        foreach (var (teamId, roster) in gameState.Rosters)
        {
            foreach (var playerId in roster)
            {
                playerTeam[playerId] = teamId;
            }
        }

        var players = new Dictionary<string, Dictionary<string, int>>();
        foreach (var (pid, teamId) in playerTeam)
        {
            players[pid] = new Dictionary<string, int>
            {
                ["points"] = 0,
                ["fgm"] = 0,
                ["fga"] = 0,
                ["rebounds"] = 0,
                ["assists"] = 0,
                ["steals"] = 0,
                ["blocks"] = 0,
                ["turnovers"] = 0,
                ["fouls"] = 0,
                ["three_m"] = 0,
                ["three_a"] = 0
            };
        }

        var teams = new Dictionary<string, Dictionary<string, int>>
        {
            [gameState.HomeTeamId] = new Dictionary<string, int> { ["points"] = 0 },
            [gameState.AwayTeamId] = new Dictionary<string, int> { ["points"] = 0 }
        };

        foreach (var gameEvent in events)
        {
            var payload = gameEvent.Payload;
            var teamId = payload.TryGetValue("team_id", out var teamObj) ? teamObj?.ToString() : null;
            var playerId = payload.TryGetValue("player_id", out var playerObj) ? playerObj?.ToString() : null;

            if (gameEvent.EventType == "shot_made")
            {
                var points = payload.TryGetValue("points", out var ptsObj) ? Convert.ToInt32(ptsObj) : 0;
                var isThree = payload.TryGetValue("is_three", out var threeObj) && Convert.ToBoolean(threeObj);
                if (teamId is not null && teams.ContainsKey(teamId))
                {
                    teams[teamId]["points"] += points;
                }
                if (playerId is not null && players.ContainsKey(playerId))
                {
                    players[playerId]["points"] += points;
                    players[playerId]["fgm"] += 1;
                    players[playerId]["fga"] += 1;
                    if (isThree)
                    {
                        players[playerId]["three_m"] += 1;
                        players[playerId]["three_a"] += 1;
                    }
                }
                var assistId = payload.TryGetValue("assist_player_id", out var assistObj) ? assistObj?.ToString() : null;
                if (!string.IsNullOrWhiteSpace(assistId) && players.ContainsKey(assistId))
                {
                    players[assistId]["assists"] += 1;
                }
            }
            else if (gameEvent.EventType == "shot_missed")
            {
                if (playerId is not null && players.ContainsKey(playerId))
                {
                    players[playerId]["fga"] += 1;
                    var isThree = payload.TryGetValue("is_three", out var threeObj) && Convert.ToBoolean(threeObj);
                    if (isThree)
                    {
                        players[playerId]["three_a"] += 1;
                    }
                }
            }
            else if (gameEvent.EventType == "rebound" && playerId is not null && players.ContainsKey(playerId))
            {
                players[playerId]["rebounds"] += 1;
            }
            else if (gameEvent.EventType == "steal" && playerId is not null && players.ContainsKey(playerId))
            {
                players[playerId]["steals"] += 1;
            }
            else if (gameEvent.EventType == "block" && playerId is not null && players.ContainsKey(playerId))
            {
                players[playerId]["blocks"] += 1;
            }
            else if (gameEvent.EventType == "turnover" && playerId is not null && players.ContainsKey(playerId))
            {
                players[playerId]["turnovers"] += 1;
            }
            else if (gameEvent.EventType == "foul" && playerId is not null && players.ContainsKey(playerId))
            {
                players[playerId]["fouls"] += 1;
            }
        }

        return new Dictionary<string, object>
        {
            ["players"] = players,
            ["teams"] = teams
        };
    }
}
