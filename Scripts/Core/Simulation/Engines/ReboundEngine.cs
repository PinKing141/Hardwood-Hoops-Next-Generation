using System;
using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Games;
using HardwoodHoops.Core.Domain.Players;
using HardwoodHoops.Core.Simulation.PlayByPlay;
using HardwoodHoops.Core.Simulation.Rng;
using DomainGameEvent = HardwoodHoops.Core.Domain.Games.GameEvent;

namespace HardwoodHoops.Core.Simulation.Engines;

public sealed class ReboundEngine
{
    private readonly IRng _rng;
    private readonly Func<string, double> _offenseStrength;
    private readonly Func<string, double> _defenseStrength;
    private readonly Dictionary<string, Player> _playerLookup;
    private readonly EventBuilder _eventBuilder;

    public ReboundEngine(
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

    public DomainGameEvent ResolveRebound(
        string offenseTeamId,
        string defenseTeamId,
        int period,
        string? rebounderId,
        IReadOnlyList<string> offenseLineup,
        IReadOnlyList<string> defenseLineup,
        Dictionary<string, double> fatigueByPlayer,
        Dictionary<string, int> foulsByPlayer)
    {
        var offenseStrength = _offenseStrength(offenseTeamId);
        var defenseStrength = _defenseStrength(defenseTeamId);
        var offRebProb = 0.25 + (offenseStrength - defenseStrength) / 300.0;

        var offAvg = AverageRebound(offenseLineup, true, fatigueByPlayer, foulsByPlayer);
        var defAvg = AverageRebound(defenseLineup, false, fatigueByPlayer, foulsByPlayer);
        offRebProb += (offAvg - defAvg) / 800.0;

        if (!string.IsNullOrWhiteSpace(rebounderId))
        {
            if (offenseLineup.Contains(rebounderId))
            {
                offRebProb += ReboundBonus(rebounderId, true, fatigueByPlayer, foulsByPlayer);
            }
            else if (defenseLineup.Contains(rebounderId))
            {
                offRebProb -= ReboundBonus(rebounderId, false, fatigueByPlayer, foulsByPlayer);
            }
        }

        offRebProb = Math.Clamp(offRebProb, 0.1, 0.6);
        var offenseBoard = _rng.NextDouble() < offRebProb;
        var reboundSide = offenseBoard ? offenseLineup : defenseLineup;
        var chosenRebounder = PickRebounder(reboundSide, offenseBoard, fatigueByPlayer, foulsByPlayer) ?? rebounderId ?? string.Empty;

        var teamId = offenseBoard ? offenseTeamId : defenseTeamId;
        var payload = new Dictionary<string, object>
        {
            ["team_id"] = teamId,
            ["player_id"] = chosenRebounder,
            ["period"] = period
        };

        return _eventBuilder.Build("rebound", $"{teamId} controls the rebound.", payload);
    }

    private double ReboundBonus(string playerId, bool offense, Dictionary<string, double> fatigue, Dictionary<string, int> fouls)
    {
        if (!_playerLookup.TryGetValue(playerId, out var player))
        {
            return 0.0;
        }

        var fatiguePenalty = fatigue.GetValueOrDefault(playerId, 0.0) * 0.003;
        var foulPenalty = Math.Max(fouls.GetValueOrDefault(playerId, 0) - 3, 0) * 0.03;
        var intent = ReboundIntentMultiplier(player, offense);
        if (offense)
        {
            return (player.Attributes.OffensiveRebound - 70) / 500.0 * intent - fatiguePenalty - foulPenalty;
        }

        return (player.Attributes.DefensiveRebound - 70) / 500.0 * intent - fatiguePenalty - foulPenalty;
    }

    private double AverageRebound(IReadOnlyList<string> ids, bool offense, Dictionary<string, double> fatigue, Dictionary<string, int> fouls)
    {
        if (ids.Count == 0)
        {
            return 0.0;
        }

        double total = 0.0;
        foreach (var playerId in ids)
        {
            if (!_playerLookup.TryGetValue(playerId, out var player))
            {
                continue;
            }

            var attrs = player.Attributes;
            var baseValue = offense ? (double)attrs.OffensiveRebound : attrs.DefensiveRebound;
            baseValue += (attrs.Vertical - 50) * 0.2 + (attrs.Strength - 50) * 0.15;
            baseValue -= fatigue.GetValueOrDefault(playerId, 0.0) * 0.2;
            baseValue *= ReboundIntentMultiplier(player, offense);
            baseValue -= Math.Max(fouls.GetValueOrDefault(playerId, 0) - 3, 0) * 1.5;
            total += baseValue;
        }

        return total / Math.Max(ids.Count, 1);
    }

    private string? PickRebounder(IReadOnlyList<string> ids, bool offense, Dictionary<string, double> fatigue, Dictionary<string, int> fouls)
    {
        if (ids.Count == 0)
        {
            return null;
        }

        var weights = new List<double>(ids.Count);
        foreach (var playerId in ids)
        {
            if (!_playerLookup.TryGetValue(playerId, out var player))
            {
                weights.Add(1.0);
                continue;
            }

            var attrs = player.Attributes;
            var baseValue = offense ? (double)attrs.OffensiveRebound : attrs.DefensiveRebound;
            baseValue += (attrs.Vertical - 50) * 0.4 + (attrs.Strength - 50) * 0.25;
            baseValue -= fatigue.GetValueOrDefault(playerId, 0.0) * 0.3;
            baseValue *= ReboundIntentMultiplier(player, offense);
            baseValue -= Math.Max(fouls.GetValueOrDefault(playerId, 0) - 3, 0) * 2.0;
            weights.Add(Math.Max(baseValue, 1.0));
        }

        return _rng.ChoiceWeighted(ids, weights);
    }

    private static double ReboundIntentMultiplier(Player player, bool offense)
    {
        var tendencies = player.Tendencies;
        var crash = tendencies.ReboundBias[0];
        var leak = tendencies.ReboundBias[1];
        if (offense)
        {
            return 1.0 + crash * 0.4 - leak * 0.3;
        }

        return 1.0 + crash * 0.25 - leak * 0.35;
    }
}
