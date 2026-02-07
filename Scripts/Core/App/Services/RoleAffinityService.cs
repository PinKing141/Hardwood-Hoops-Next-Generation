using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Players;

namespace HardwoodHoops.Core.App.Services;

public sealed class RoleAffinityService
{
    private readonly Dictionary<string, Dictionary<string, double>> _roleVectors;

    public RoleAffinityService()
    {
        _roleVectors = DefaultRoleVectors();
    }

    public Dictionary<string, double> ComputeAffinities(Player player)
    {
        var t = player.Tendencies;
        var attrs = player.Attributes;
        var affinities = new Dictionary<string, double>();

        foreach (var (role, vec) in _roleVectors)
        {
            double score = 0;
            score += vec.GetValueOrDefault("shot_close") * t.ShotProfile[0];
            score += vec.GetValueOrDefault("shot_mid") * t.ShotProfile[1];
            score += vec.GetValueOrDefault("shot_three") * t.ShotProfile[2];
            score += vec.GetValueOrDefault("rim_dunk") * t.RimAggression[1];
            score += vec.GetValueOrDefault("creation_drive") * t.ShotCreation[2];
            score += vec.GetValueOrDefault("creation_catch") * t.ShotCreation[0];
            score += vec.GetValueOrDefault("playmaking_pass") * t.PlaymakingBias[1];
            score += vec.GetValueOrDefault("defense_disrupt") * t.DefensiveStyle[1];
            score += vec.GetValueOrDefault("defense_gamble") * t.DefensiveStyle[2];
            score += vec.GetValueOrDefault("help_early") * t.HelpDefense[0];
            score += vec.GetValueOrDefault("rebound_crash") * t.ReboundBias[0];
            score += vec.GetValueOrDefault("athletic_straight") * t.AthleticUsage[0];
            score += vec.GetValueOrDefault("athletic_vertical") * t.AthleticUsage[2];
            score += vec.GetValueOrDefault("finishing") * (attrs.Layup + attrs.Dunk + attrs.Inside) / 300.0;
            score += vec.GetValueOrDefault("shooting") * (attrs.MidRange + attrs.ThreePoint + attrs.FreeThrow) / 300.0;
            score += vec.GetValueOrDefault("playmaking_attr") * (attrs.BallControl + attrs.Passing) / 200.0;
            score += vec.GetValueOrDefault("defense_attr") * (attrs.PerimeterDefense + attrs.InteriorDefense + attrs.Steal + attrs.Block) / 400.0;
            score += vec.GetValueOrDefault("rebounding_attr") * (attrs.OffensiveRebound + attrs.DefensiveRebound) / 200.0;
            score += vec.GetValueOrDefault("athletic_attr") * (attrs.Speed + attrs.Agility + attrs.Vertical) / 300.0;
            affinities[role] = score;
        }

        var total = 0.0;
        foreach (var value in affinities.Values)
        {
            total += value;
        }

        if (total > 0)
        {
            var keys = new List<string>(affinities.Keys);
            foreach (var key in keys)
            {
                affinities[key] /= total;
            }
        }

        return affinities;
    }

    public Dictionary<string, Dictionary<string, double>> ComputeAffinitiesForIds(
        IEnumerable<string> playerIds,
        Dictionary<string, Player> playerLookup)
    {
        var results = new Dictionary<string, Dictionary<string, double>>();
        foreach (var id in playerIds)
        {
            if (playerLookup.TryGetValue(id, out var player))
            {
                results[id] = ComputeAffinities(player);
            }
        }

        return results;
    }

    public Dictionary<string, double> TopRoles(Player player, int n = 3)
    {
        var affinities = ComputeAffinities(player);
        var sorted = new List<KeyValuePair<string, double>>(affinities);
        sorted.Sort((a, b) => b.Value.CompareTo(a.Value));
        var results = new Dictionary<string, double>();
        for (var i = 0; i < sorted.Count && i < n; i++)
        {
            results[sorted[i].Key] = sorted[i].Value;
        }

        return results;
    }

    private static Dictionary<string, Dictionary<string, double>> DefaultRoleVectors()
    {
        return new Dictionary<string, Dictionary<string, double>>
        {
            ["rim_pressure_wing"] = new()
            {
                ["shot_close"] = 0.25,
                ["shot_mid"] = 0.1,
                ["shot_three"] = 0.05,
                ["rim_dunk"] = 0.25,
                ["creation_drive"] = 0.25,
                ["athletic_straight"] = 0.05,
                ["athletic_vertical"] = 0.05,
                ["finishing"] = 0.2,
                ["athletic_attr"] = 0.1
            },
            ["spot_up_shooter"] = new()
            {
                ["shot_close"] = 0.05,
                ["shot_mid"] = 0.15,
                ["shot_three"] = 0.35,
                ["creation_catch"] = 0.25,
                ["playmaking_pass"] = 0.05,
                ["shooting"] = 0.25
            },
            ["secondary_creator"] = new()
            {
                ["shot_mid"] = 0.15,
                ["shot_three"] = 0.15,
                ["creation_drive"] = 0.2,
                ["creation_catch"] = 0.1,
                ["playmaking_pass"] = 0.25,
                ["playmaking_attr"] = 0.25
            },
            ["primary_creator"] = new()
            {
                ["creation_drive"] = 0.25,
                ["creation_catch"] = 0.1,
                ["shot_mid"] = 0.1,
                ["shot_three"] = 0.1,
                ["playmaking_pass"] = 0.25,
                ["playmaking_attr"] = 0.25,
                ["athletic_straight"] = 0.05
            },
            ["defensive_stopper"] = new()
            {
                ["defense_disrupt"] = 0.2,
                ["defense_gamble"] = 0.05,
                ["help_early"] = 0.15,
                ["rebound_crash"] = 0.1,
                ["defense_attr"] = 0.35,
                ["athletic_attr"] = 0.15
            },
            ["glass_cleaner"] = new()
            {
                ["rebound_crash"] = 0.35,
                ["athletic_vertical"] = 0.1,
                ["finishing"] = 0.1,
                ["rebounding_attr"] = 0.35,
                ["defense_attr"] = 0.1
            },
            ["stretch_big"] = new()
            {
                ["shot_mid"] = 0.15,
                ["shot_three"] = 0.3,
                ["creation_catch"] = 0.2,
                ["rebound_crash"] = 0.1,
                ["shooting"] = 0.25
            }
        };
    }
}
