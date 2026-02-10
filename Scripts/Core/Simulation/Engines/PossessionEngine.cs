using System;
using System.Collections.Generic;
using System.Linq;
using HardwoodHoops.Core.Domain.Games;
using HardwoodHoops.Core.Simulation.PlayByPlay;
using HardwoodHoops.Core.Simulation.Rng;
using DomainGameEvent = HardwoodHoops.Core.Domain.Games.GameEvent;

namespace HardwoodHoops.Core.Simulation.Engines;

public sealed class PossessionEngine
{
    private readonly ShotEngine _shotEngine;
    private readonly ReboundEngine _reboundEngine;
    private readonly FoulEngine _foulEngine;
    private readonly IRng _rng;
    private readonly EventBuilder _eventBuilder;

    public PossessionEngine(
        ShotEngine shotEngine,
        ReboundEngine reboundEngine,
        FoulEngine foulEngine,
        IRng rng,
        EventBuilder? eventBuilder = null)
    {
        _shotEngine = shotEngine;
        _reboundEngine = reboundEngine;
        _foulEngine = foulEngine;
        _rng = rng;
        _eventBuilder = eventBuilder ?? new EventBuilder();
    }

    public IReadOnlyList<DomainGameEvent> RunPossession(
        GameState gameState,
        string offenseTeamId,
        string defenseTeamId,
        IReadOnlyList<string> offenseLineup,
        IReadOnlyList<string> defenseLineup)
    {
        var events = new List<DomainGameEvent>();
        var (playType, shooter) = SelectPlayAndShooter(offenseLineup, _rng);
        var assistedBy = SelectAssister(offenseLineup, shooter, playType, _rng);
        var defender = defenseLineup.Count > 0 ? defenseLineup[_rng.NextInt(0, defenseLineup.Count - 1)] : null;

        if (_rng.NextDouble() < 0.05 && defenseLineup.Count > 0)
        {
            var stealer = defender ?? defenseLineup[_rng.NextInt(0, defenseLineup.Count - 1)];
            events.Add(BuildEvent("steal", defenseTeamId, stealer, gameState.Period));
            events.Add(BuildEvent("turnover", offenseTeamId, shooter, gameState.Period));
            return events;
        }

        var foul = _foulEngine.MaybeCommitFoul(
            offenseTeamId,
            defenseTeamId,
            gameState.Period,
            defender,
            shooter,
            playType,
            gameState.TeamFouls);

        if (foul is not null)
        {
            events.Add(foul);
            var payload = foul.Payload;
            if (payload.TryGetValue("shooting_foul", out var shooting) && shooting is bool isShooting && isShooting)
            {
                var attempts = payload.TryGetValue("ft_attempts", out var value) ? Convert.ToInt32(value) : 2;
                var fouled = payload.TryGetValue("fouled_player_id", out var fouledId) ? fouledId?.ToString() : shooter;
                for (var i = 0; i < attempts; i++)
                {
                    events.Add(ShootFreeThrow(offenseTeamId, gameState.Period, fouled, _rng));
                }
            }

            return events;
        }

        var shotEvent = _shotEngine.ResolveShot(offenseTeamId, defenseTeamId, shooter, assistedBy, playType);
        events.Add(shotEvent);

        if (shotEvent.EventType == "shot_missed" && defenseLineup.Count > 0)
        {
            if (_rng.NextDouble() < 0.1)
            {
                var blocker = defender ?? defenseLineup[_rng.NextInt(0, defenseLineup.Count - 1)];
                events.Add(BuildEvent("block", defenseTeamId, blocker, gameState.Period));
            }
        }

        if (shotEvent.EventType == "shot_missed")
        {
            var rebounderPool = _rng.NextDouble() < 0.25 ? offenseLineup : defenseLineup;
            var rebounder = rebounderPool.Count > 0 ? rebounderPool[_rng.NextInt(0, rebounderPool.Count - 1)] : null;
            events.Add(_reboundEngine.ResolveRebound(
                offenseTeamId,
                defenseTeamId,
                gameState.Period,
                rebounder,
                offenseLineup,
                defenseLineup,
                gameState.FatigueByPlayer,
                gameState.FoulsByPlayer));
        }

        return events;
    }

    private static (string playType, string? shooter) SelectPlayAndShooter(IReadOnlyList<string> offenseLineup, IRng rng)
    {
        if (offenseLineup.Count == 0)
        {
            return ("spot_up", null);
        }

        var shooter = offenseLineup[rng.NextInt(0, offenseLineup.Count - 1)];
        var playTypes = new[] { "pnr", "post_up", "spot_up" };
        var playType = playTypes[rng.NextInt(0, playTypes.Length - 1)];
        return (playType, shooter);
    }

    private string? SelectAssister(IReadOnlyList<string> offenseLineup, string? shooter, string playType, IRng rng)
    {
        if (offenseLineup.Count <= 1 || shooter is null)
        {
            return null;
        }

        var chance = playType is "spot_up" or "pnr" ? 0.5 : 0.3;
        if (rng.NextDouble() >= chance)
        {
            return null;
        }

        var candidates = offenseLineup.Where(id => id != shooter).ToList();
        return candidates.Count == 0 ? null : candidates[rng.NextInt(0, candidates.Count - 1)];
    }

    private DomainGameEvent BuildEvent(string eventType, string teamId, string? playerId, int period)
    {
        var payload = new Dictionary<string, object>
        {
            ["team_id"] = teamId,
            ["player_id"] = playerId ?? string.Empty,
            ["period"] = period
        };

        return _eventBuilder.Build(eventType, eventType.Replace("_", " "), payload);
    }

    private static DomainGameEvent ShootFreeThrow(string offenseTeamId, int period, string? shooterId, IRng rng)
    {
        var make = rng.NextDouble() < 0.75;
        var payload = new Dictionary<string, object>
        {
            ["team_id"] = offenseTeamId,
            ["player_id"] = shooterId ?? string.Empty,
            ["points"] = make ? 1 : 0,
            ["period"] = period,
            ["is_three"] = false,
            ["play_type"] = "free_throw",
            ["is_free_throw"] = true
        };

        var description = $"{offenseTeamId} {(make ? "makes" : "misses")} a free throw.";
        return new EventBuilder().Build(make ? "shot_made" : "shot_missed", description, payload);
    }

    private IRng GetRng() => _rng;
}
