using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Players;

namespace HardwoodHoops.Core.App.Services;

public sealed class PlayerEvaluationService
{
    private readonly string _defaultRole;

    public PlayerEvaluationService(string defaultRole = "wing")
    {
        _defaultRole = defaultRole;
    }

    public Dictionary<string, (double trueOvr, double publicOvr)> Evaluate(
        IEnumerable<Player> players,
        Dictionary<string, string>? roleMap = null)
    {
        roleMap ??= new Dictionary<string, string>();
        var ratings = new Dictionary<string, (double, double)>();
        foreach (var player in players)
        {
            var role = roleMap.GetValueOrDefault(player.PlayerId, _defaultRole);
            var (trueOvr, publicOvr) = OverallCalculator.ComputePublicOverall(player, role);
            ratings[player.PlayerId] = (trueOvr, publicOvr);
        }

        return ratings;
    }

    public List<Player> BestPlayers(
        IEnumerable<Player> players,
        int topN = 10,
        Dictionary<string, string>? roleMap = null)
    {
        roleMap ??= new Dictionary<string, string>();
        var scored = new List<(double, Player)>();
        foreach (var player in players)
        {
            var role = roleMap.GetValueOrDefault(player.PlayerId, _defaultRole);
            var trueOvr = OverallCalculator.ComputeTrueOverall(player, role);
            scored.Add((trueOvr, player));
        }

        scored.Sort((a, b) => b.Item1.CompareTo(a.Item1));
        var results = new List<Player>();
        for (var i = 0; i < scored.Count && i < topN; i++)
        {
            results.Add(scored[i].Item2);
        }

        return results;
    }
}
