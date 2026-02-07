using System;
using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Games;
using HardwoodHoops.Core.Domain.Players;
using HardwoodHoops.Core.Simulation.PlayByPlay;
using HardwoodHoops.Core.Simulation.Rng;

namespace HardwoodHoops.Core.Simulation.Engines;

public sealed class ShotEngine
{
    private readonly IRng _rng;
    private readonly Func<string, double> _offenseStrength;
    private readonly Func<string, double> _defenseStrength;
    private readonly Dictionary<string, Player> _playerLookup;
    private readonly EventBuilder _eventBuilder;

    public ShotEngine(
        IRng rng,
        Func<string, double> offenseStrength,
        Func<string, double> defenseStrength,
        Dictionary<string, Player>? playerLookup = null,
        EventBuilder? eventBuilder = null)
    {
        _rng = rng;
        _offenseStrength = offenseStrength;
        _defenseStrength = defenseStrength;
        _playerLookup = playerLookup ?? new Dictionary<string, Player>();
        _eventBuilder = eventBuilder ?? new EventBuilder();
    }

    public GameEvent ResolveShot(string offenseTeamId, string defenseTeamId, string? shooterId, string? assistedBy, string playType)
    {
        var offenseStrength = _offenseStrength(offenseTeamId);
        var defenseStrength = _defenseStrength(defenseTeamId);

        var threeBias = playType switch
        {
            "spot_up" => 0.55,
            "post_up" => 0.1,
            _ => 0.35
        };

        var isThree = _rng.NextDouble() < threeBias;
        var baseProb = 0.45 + (offenseStrength - defenseStrength) / 200.0;
        if (isThree)
        {
            baseProb -= 0.05;
        }

        if (playType == "post_up")
        {
            baseProb += 0.02;
        }
        else if (playType == "pnr")
        {
            baseProb += 0.01;
        }

        baseProb += ShooterBonus(shooterId, playType, isThree);
        var makeProb = Math.Clamp(baseProb, 0.20, 0.8);
        var made = _rng.NextDouble() < makeProb;
        var points = isThree ? 3 : 2;
        var isFreeThrow = false;
        var andOne = false;

        if (!made && _rng.NextDouble() < 0.08)
        {
            isFreeThrow = true;
            points = 1;
            isThree = false;
        }

        var eventType = made ? "shot_made" : "shot_missed";
        var description = $"{offenseTeamId} {(made ? "drains" : "misses")} a {points}-pt attempt.";
        var payload = new Dictionary<string, object>
        {
            ["team_id"] = offenseTeamId,
            ["player_id"] = shooterId ?? string.Empty,
            ["assist_player_id"] = made ? assistedBy ?? string.Empty : string.Empty,
            ["points"] = made ? points : 0,
            ["is_three"] = isThree,
            ["play_type"] = playType,
            ["is_free_throw"] = isFreeThrow,
            ["and_one"] = andOne
        };

        return _eventBuilder.Build(eventType, description, payload);
    }

    private double ShooterBonus(string? shooterId, string playType, bool isThree)
    {
        if (shooterId is null || !_playerLookup.TryGetValue(shooterId, out var player))
        {
            return 0.0;
        }

        var attrs = player.Attributes;
        if (isThree)
        {
            return (attrs.ThreePoint - 70) / 300.0;
        }

        if (playType == "post_up")
        {
            return (attrs.Inside - 70) / 300.0 + (attrs.Dunk - 70) / 400.0;
        }

        return (attrs.MidRange - 70) / 300.0 + (attrs.Layup - 70) / 400.0;
    }
}
