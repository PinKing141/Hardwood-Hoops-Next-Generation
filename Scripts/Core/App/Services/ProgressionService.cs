using System;
using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Players;

namespace HardwoodHoops.Core.App.Services;

public sealed class ProgressionService
{
    private readonly RoleAffinityService _roleAffinity;
    private readonly double _maxGrowth;
    private readonly int _declineStartAge;
    private readonly double _declineRate;
    private readonly Dictionary<string, double> _positionDecline;

    public ProgressionService(
        RoleAffinityService? roleAffinity = null,
        double maxGrowth = 2.5,
        int declineStartAge = 24,
        double declineRate = 1.0,
        Dictionary<string, double>? positionDecline = null)
    {
        _roleAffinity = roleAffinity ?? new RoleAffinityService();
        _maxGrowth = maxGrowth;
        _declineStartAge = declineStartAge;
        _declineRate = declineRate;
        _positionDecline = positionDecline ?? new Dictionary<string, double>
        {
            ["guard"] = 1.0,
            ["wing"] = 1.0,
            ["forward"] = 1.05,
            ["center"] = 1.1
        };
    }

    public void ApplyGrowth(IEnumerable<Player> players, Dictionary<string, string>? positionMap = null)
    {
        positionMap ??= new Dictionary<string, string>();
        foreach (var player in players)
        {
            var affinities = _roleAffinity.ComputeAffinities(player);
            var primary = affinities.Count > 0 ? MaxKey(affinities) : null;
            var softCaps = RoleSoftCaps().GetValueOrDefault(primary ?? string.Empty, new Dictionary<string, double>());
            var attrMod = (player.Attributes.Potential - 50) / 100.0;
            var consistencyMod = (player.Attributes.Consistency - 50) / 200.0;
            var disciplineMod = (player.Attributes.DecisionDiscipline - 50) / 200.0;
            var growthScalar = Math.Max(0.5, 1.0 + attrMod + consistencyMod + disciplineMod);

            foreach (var (attr, cap) in softCaps)
            {
                var current = GetAttribute(player, attr);
                var growth = current >= cap ? Math.Min(0.5, _maxGrowth * 0.2) : Math.Min(_maxGrowth, cap - current);
                growth *= growthScalar;
                SetAttribute(player, attr, Math.Min(99, current + growth));
            }

            var age = AgeFromClassYear(player.ClassYear);
            if (age.HasValue && age.Value >= _declineStartAge)
            {
                var pos = positionMap.GetValueOrDefault(player.PlayerId, string.Empty).ToLowerInvariant();
                var posFactor = _positionDecline.GetValueOrDefault(pos, 1.0);
                var declineAmount = _declineRate * posFactor * ((age.Value - _declineStartAge + 1) * 0.2);
                foreach (var attr in new[] { "speed", "agility", "vertical", "stamina", "strength" })
                {
                    var value = GetAttribute(player, attr);
                    SetAttribute(player, attr, Math.Max(25, value - declineAmount));
                }
            }
        }
    }

    private static int? AgeFromClassYear(string classYear)
    {
        var mapping = new Dictionary<string, int>
        {
            ["FR"] = 18,
            ["SO"] = 19,
            ["JR"] = 20,
            ["SR"] = 21
        };
        if (string.IsNullOrWhiteSpace(classYear))
        {
            return null;
        }
        var tokens = classYear.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        var token = tokens[^1];
        return mapping.GetValueOrDefault(token);
    }

    private static string MaxKey(Dictionary<string, double> values)
    {
        var bestKey = string.Empty;
        var bestValue = double.MinValue;
        foreach (var (key, value) in values)
        {
            if (value > bestValue)
            {
                bestValue = value;
                bestKey = key;
            }
        }
        return bestKey;
    }

    private static Dictionary<string, Dictionary<string, double>> RoleSoftCaps()
    {
        return new Dictionary<string, Dictionary<string, double>>
        {
            ["rim_pressure_wing"] = new() { ["dunk"] = 92, ["speed"] = 90, ["perimeter_defense"] = 85 },
            ["spot_up_shooter"] = new() { ["three_point"] = 95, ["free_throw"] = 92, ["perimeter_defense"] = 80 },
            ["primary_creator"] = new() { ["ball_control"] = 95, ["passing"] = 95, ["speed"] = 90 },
            ["secondary_creator"] = new() { ["ball_control"] = 90, ["passing"] = 90, ["three_point"] = 90 },
            ["stretch_big"] = new() { ["three_point"] = 90, ["mid_range"] = 90, ["defensive_rebound"] = 85 },
            ["glass_cleaner"] = new() { ["defensive_rebound"] = 95, ["offensive_rebound"] = 92, ["strength"] = 90 },
            ["defensive_stopper"] = new() { ["perimeter_defense"] = 95, ["interior_defense"] = 90, ["steal"] = 90, ["block"] = 90 }
        };
    }

    private static double GetAttribute(Player player, string attr)
    {
        var attrs = player.Attributes;
        return attr switch
        {
            "dunk" => attrs.Dunk,
            "speed" => attrs.Speed,
            "perimeter_defense" => attrs.PerimeterDefense,
            "three_point" => attrs.ThreePoint,
            "free_throw" => attrs.FreeThrow,
            "ball_control" => attrs.BallControl,
            "passing" => attrs.Passing,
            "mid_range" => attrs.MidRange,
            "defensive_rebound" => attrs.DefensiveRebound,
            "offensive_rebound" => attrs.OffensiveRebound,
            "strength" => attrs.Strength,
            "interior_defense" => attrs.InteriorDefense,
            "steal" => attrs.Steal,
            "block" => attrs.Block,
            "agility" => attrs.Agility,
            "vertical" => attrs.Vertical,
            "stamina" => attrs.Stamina,
            _ => 50
        };
    }

    private static void SetAttribute(Player player, string attr, double value)
    {
        var attrs = player.Attributes with { };
        var updated = attr switch
        {
            "dunk" => attrs with { Dunk = (int)value },
            "speed" => attrs with { Speed = (int)value },
            "perimeter_defense" => attrs with { PerimeterDefense = (int)value },
            "three_point" => attrs with { ThreePoint = (int)value },
            "free_throw" => attrs with { FreeThrow = (int)value },
            "ball_control" => attrs with { BallControl = (int)value },
            "passing" => attrs with { Passing = (int)value },
            "mid_range" => attrs with { MidRange = (int)value },
            "defensive_rebound" => attrs with { DefensiveRebound = (int)value },
            "offensive_rebound" => attrs with { OffensiveRebound = (int)value },
            "strength" => attrs with { Strength = (int)value },
            "interior_defense" => attrs with { InteriorDefense = (int)value },
            "steal" => attrs with { Steal = (int)value },
            "block" => attrs with { Block = (int)value },
            "agility" => attrs with { Agility = (int)value },
            "vertical" => attrs with { Vertical = (int)value },
            "stamina" => attrs with { Stamina = (int)value },
            _ => attrs
        };
        player.Attributes = updated;
    }
}
