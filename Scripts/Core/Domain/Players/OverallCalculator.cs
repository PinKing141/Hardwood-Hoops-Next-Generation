using System;

namespace HardwoodHoops.Core.Domain.Players;

public static class OverallCalculator
{
    public static (double trueOvr, double publicOvr) ComputePublicOverall(Player player, string role = "wing")
    {
        var trueOvr = ComputeTrueOverall(player, role);
        var consistency = player.Attributes.Consistency;
        var potential = player.Attributes.Potential;
        var bias = (potential - 50) * 0.03;
        var noiseRange = Math.Max(3.0, (100 - consistency) * 0.07);
        var pseudo = (player.PlayerId.GetHashCode() & 0x7fffffff) % 100 / 100.0;
        var noise = (pseudo - 0.5) * 2 * noiseRange;
        var publicOvr = ClampRating(trueOvr + bias + noise);
        return (trueOvr, publicOvr);
    }

    public static double ComputeTrueOverall(Player player, string role = "wing")
    {
        var attrs = player.Attributes;
        var roleMultiplier = RoleBias(role);

        var offenseScore = WeightedAverage(
            new (string key, double weight)[]
            {
                ("layup", 8),
                ("dunk", 7),
                ("inside", 7 * roleMultiplier.Inside),
                ("mid", 5 * roleMultiplier.MidRange),
                ("three", 5 * roleMultiplier.ThreePoint),
                ("free", 3),
                ("off_reb", 5 * roleMultiplier.OffensiveRebound),
                ("ball_control", 5 * roleMultiplier.BallControl),
                ("passing", 10 * roleMultiplier.Passing),
            },
            key => key switch
            {
                "layup" => attrs.Layup,
                "dunk" => attrs.Dunk,
                "inside" => attrs.Inside,
                "mid" => attrs.MidRange,
                "three" => attrs.ThreePoint,
                "free" => attrs.FreeThrow,
                "off_reb" => attrs.OffensiveRebound,
                "ball_control" => attrs.BallControl,
                "passing" => attrs.Passing,
                _ => 50
            });

        var defenseScore = WeightedAverage(
            new (string key, double weight)[]
            {
                ("perimeter", 8 * roleMultiplier.PerimeterDefense),
                ("interior", 8 * roleMultiplier.InteriorDefense),
                ("def_reb", 6 * roleMultiplier.DefensiveRebound),
                ("steal", 4),
                ("block", 4 * roleMultiplier.Block),
            },
            key => key switch
            {
                "perimeter" => attrs.PerimeterDefense,
                "interior" => attrs.InteriorDefense,
                "def_reb" => attrs.DefensiveRebound,
                "steal" => attrs.Steal,
                "block" => attrs.Block,
                _ => 50
            });

        var athleticScore = WeightedAverage(
            new (string key, double weight)[]
            {
                ("speed", 6),
                ("agility", 5),
                ("vertical", 4),
                ("strength", 3),
                ("stamina", 2),
            },
            key => key switch
            {
                "speed" => attrs.Speed,
                "agility" => attrs.Agility,
                "vertical" => attrs.Vertical,
                "strength" => attrs.Strength,
                "stamina" => attrs.Stamina,
                _ => 50
            });

        var mentalScore = WeightedAverage(
            new (string key, double weight)[]
            {
                ("off_iq", 8),
                ("def_iq", 5),
                ("hustle", 2),
            },
            key => key switch
            {
                "off_iq" => attrs.OffensiveIq,
                "def_iq" => attrs.DefensiveIq,
                "hustle" => attrs.Hustle,
                _ => 50
            });

        var overall = 0.35 * offenseScore + 0.30 * defenseScore + 0.20 * athleticScore + 0.15 * mentalScore;
        return ClampRating(overall);
    }

    private static double WeightedAverage((string key, double weight)[] weights, Func<string, double> selector)
    {
        double totalWeight = 0;
        double score = 0;
        foreach (var (key, weight) in weights)
        {
            totalWeight += weight;
            score += weight * selector(key);
        }

        if (totalWeight <= 0)
        {
            return 50.0;
        }

        return score / totalWeight;
    }

    private static double ClampRating(double value)
    {
        return Math.Max(25.0, Math.Min(99.0, value));
    }

    private static RoleMultiplier RoleBias(string role)
    {
        return role switch
        {
            "guard" => new RoleMultiplier(
                BallControl: 1.05,
                Passing: 1.05,
                ThreePoint: 1.05,
                MidRange: 1.0,
                Inside: 0.95,
                OffensiveRebound: 1.0,
                DefensiveRebound: 1.0,
                InteriorDefense: 1.0,
                Block: 0.95,
                PerimeterDefense: 1.0),
            "wing" => new RoleMultiplier(
                BallControl: 1.0,
                Passing: 1.0,
                ThreePoint: 1.02,
                MidRange: 1.05,
                Inside: 1.0,
                OffensiveRebound: 1.0,
                DefensiveRebound: 1.0,
                InteriorDefense: 1.0,
                Block: 1.0,
                PerimeterDefense: 1.05),
            "big" => new RoleMultiplier(
                BallControl: 1.0,
                Passing: 1.0,
                ThreePoint: 0.95,
                MidRange: 1.0,
                Inside: 1.05,
                OffensiveRebound: 1.05,
                DefensiveRebound: 1.05,
                InteriorDefense: 1.05,
                Block: 1.05,
                PerimeterDefense: 1.0),
            _ => new RoleMultiplier(
                BallControl: 1.0,
                Passing: 1.0,
                ThreePoint: 1.0,
                MidRange: 1.0,
                Inside: 1.0,
                OffensiveRebound: 1.0,
                DefensiveRebound: 1.0,
                InteriorDefense: 1.0,
                Block: 1.0,
                PerimeterDefense: 1.0)
        };
    }

    private readonly record struct RoleMultiplier(
        double BallControl,
        double Passing,
        double ThreePoint,
        double MidRange,
        double Inside,
        double OffensiveRebound,
        double DefensiveRebound,
        double InteriorDefense,
        double Block,
        double PerimeterDefense
    );
}
