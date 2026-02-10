using System;
using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Games;
using HardwoodHoops.Core.Domain.Players;
using HardwoodHoops.Core.Simulation.PlayByPlay;
using HardwoodHoops.Core.Simulation.Rng;
using DomainGameEvent = HardwoodHoops.Core.Domain.Games.GameEvent;

namespace HardwoodHoops.Core.Simulation.Engines;

public sealed class FoulEngine
{
    private readonly IRng _rng;
    private readonly Func<string, double> _offenseStrength;
    private readonly Func<string, double> _defenseStrength;
    private readonly Dictionary<string, Player> _playerLookup;
    private readonly EventBuilder _eventBuilder;

    public FoulEngine(
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

    public DomainGameEvent? MaybeCommitFoul(
        string offenseTeamId,
        string defenseTeamId,
        int period,
        string? defenderId,
        string? shooterId,
        string? playType,
        Dictionary<string, int>? teamFouls)
    {
        var defenseStrength = _defenseStrength(defenseTeamId);
        var offenseStrength = _offenseStrength(offenseTeamId);
        var foulProb = 0.08 + (offenseStrength - defenseStrength) / 300.0;

        if (defenderId is not null && _playerLookup.TryGetValue(defenderId, out var defender))
        {
            foulProb += (100 - defender.Attributes.DefensiveIq) / 1000.0;
            foulProb += (100 - defender.Attributes.DecisionDiscipline) / 1200.0;
        }

        foulProb = Math.Clamp(foulProb, 0.02, 0.2);
        if (_rng.NextDouble() >= foulProb)
        {
            return null;
        }

        var shootingFoul = false;
        var ftAttempts = 0;
        var bonus = teamFouls is not null && teamFouls.TryGetValue(defenseTeamId, out var fouls) && fouls >= 7;
        if (bonus && _rng.NextDouble() < 0.6)
        {
            shootingFoul = true;
            ftAttempts = 2;
        }
        else if (_rng.NextDouble() < 0.55)
        {
            shootingFoul = true;
            if (playType == "spot_up" && _rng.NextDouble() < 0.25)
            {
                ftAttempts = 3;
            }
            else
            {
                ftAttempts = 2;
            }
        }

        var andOne = shootingFoul && _rng.NextDouble() < 0.2;
        var payload = new Dictionary<string, object>
        {
            ["team_id"] = defenseTeamId,
            ["player_id"] = defenderId ?? string.Empty,
            ["period"] = period,
            ["type"] = "personal",
            ["shooting_foul"] = shootingFoul,
            ["ft_attempts"] = ftAttempts,
            ["fouled_player_id"] = shooterId ?? string.Empty,
            ["and_one"] = andOne
        };

        return _eventBuilder.Build("foul", $"{defenseTeamId} commits a foul.", payload);
    }
}
