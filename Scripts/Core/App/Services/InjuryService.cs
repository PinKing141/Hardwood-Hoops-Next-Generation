using System;
using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Players;

namespace HardwoodHoops.Core.App.Services;

public sealed class InjuryService
{
    private readonly double _baseRate;

    public InjuryService(double baseRate = 0.01)
    {
        _baseRate = baseRate;
    }

    private static readonly List<(string name, string severity, int minDays, int maxDays)> InjuryCatalog = new()
    {
        ("ankle sprain", "day-to-day", 1, 3),
        ("concussion protocol", "day-to-day", 1, 6),
        ("hamstring tweak", "short-term", 3, 8),
        ("shoulder strain", "short-term", 4, 10),
        ("knee sprain", "multi-week", 10, 21),
        ("stress fracture", "long-term", 21, 45)
    };

    public Dictionary<string, int> ApplyGameInjuries(IEnumerable<Player> players, Dictionary<string, double> fatigueByPlayer)
    {
        var injuries = new Dictionary<string, int>();
        var rng = new Random();
        foreach (var player in players)
        {
            var fatigue = fatigueByPlayer.GetValueOrDefault(player.PlayerId, 0.0);
            var chance = _baseRate + (player.Attributes.InjuryProneness / 100.0) * 0.02 + (fatigue / 100.0) * 0.01;
            if (rng.NextDouble() < chance)
            {
                var (duration, injuryType, severity) = AssignInjury(player, fatigue, rng);
                injuries[player.PlayerId] = duration;
                player.Injured = true;
                player.InjuryDays = duration;
                player.InjuryType = injuryType;
                player.InjurySeverity = severity;
                player.InjuryStatus = $"{severity} ({injuryType}, {duration}d)";
            }
        }

        return injuries;
    }

    public Dictionary<string, bool> ApplySeasonRecovery(IEnumerable<Player> players)
    {
        var recovered = new Dictionary<string, bool>();
        var rng = new Random();
        foreach (var player in players)
        {
            if (!player.Injured && player.InjuryDays <= 0)
            {
                recovered[player.PlayerId] = false;
                continue;
            }

            player.InjuryDays = Math.Max(player.InjuryDays - 1, 0);
            var chance = 0.5 + (1 - player.Attributes.InjuryProneness / 100.0) * 0.3 + player.Personality.WorkEthic * 0.2;
            var recoveredNow = player.InjuryDays == 0 && rng.NextDouble() < chance;
            if (recoveredNow)
            {
                player.Injured = false;
                player.InjuryType = null;
                player.InjurySeverity = null;
                player.InjuryStatus = null;
            }
            else
            {
                player.InjuryStatus = $"{player.InjurySeverity ?? "injured"} ({player.InjuryType ?? "injury"}, {player.InjuryDays}d)";
            }

            recovered[player.PlayerId] = recoveredNow;
        }

        return recovered;
    }

    private static (int duration, string injuryType, string severity) AssignInjury(Player player, double fatigue, Random rng)
    {
        var severityBias = (player.Attributes.InjuryProneness / 100.0) * 0.5 + (fatigue / 100.0) * 0.35;
        var weights = new List<double>();
        foreach (var entry in InjuryCatalog)
        {
            var tier = entry.severity switch
            {
                "day-to-day" => 0,
                "short-term" => 1,
                "multi-week" => 2,
                "long-term" => 3,
                _ => 1
            };
            var baseWeight = tier switch
            {
                0 => 1.0,
                1 => 0.7,
                2 => 0.4,
                _ => 0.2
            };
            weights.Add(baseWeight * (1.0 + severityBias * (0.3 + 0.25 * tier)));
        }

        var selected = WeightedChoice(InjuryCatalog, weights, rng);
        var scale = 1.0 + (player.Attributes.InjuryProneness / 100.0) * 0.3;
        var duration = (int)(rng.Next(selected.minDays, selected.maxDays + 1) * scale);
        duration = Math.Max(duration, 1);
        return (duration, selected.name, selected.severity);
    }

    private static (string name, string severity, int minDays, int maxDays) WeightedChoice(
        IReadOnlyList<(string name, string severity, int minDays, int maxDays)> items,
        IReadOnlyList<double> weights,
        Random rng)
    {
        double total = 0;
        foreach (var weight in weights)
        {
            total += Math.Max(0, weight);
        }

        if (total <= 0)
        {
            return items[0];
        }

        var roll = rng.NextDouble() * total;
        double cumulative = 0;
        for (var i = 0; i < items.Count; i++)
        {
            cumulative += Math.Max(0, weights[i]);
            if (roll <= cumulative)
            {
                return items[i];
            }
        }

        return items[^1];
    }
}
