using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Players;
using HardwoodHoops.Core.Domain.Recruiting;

namespace HardwoodHoops.Core.App.Services;

public sealed class ScoutingService
{
    private readonly PlayerEvaluationService _evaluator;
    private readonly BuildNameService _buildNamer;
    private readonly RoleAffinityService _roleAffinity;

    public ScoutingService(
        PlayerEvaluationService? evaluator = null,
        BuildNameService? buildNamer = null,
        RoleAffinityService? roleAffinity = null)
    {
        _evaluator = evaluator ?? new PlayerEvaluationService();
        _buildNamer = buildNamer ?? new BuildNameService();
        _roleAffinity = roleAffinity ?? new RoleAffinityService();
    }

    public Dictionary<string, Dictionary<string, object?>> ScoutingReports(
        IEnumerable<Player> players,
        Dictionary<string, string>? roleMap = null,
        Dictionary<string, RecruitingInterest>? recruiting = null)
    {
        var ratings = _evaluator.Evaluate(players, roleMap);
        var reports = new Dictionary<string, Dictionary<string, object?>>();
        foreach (var player in players)
        {
            var (_, publicOvr) = ratings[player.PlayerId];
            var buildName = _buildNamer.GenerateName(player);
            var topRoles = new List<string>(_roleAffinity.TopRoles(player, 3).Keys);
            var status = player.Injured ? "injured" : "healthy";
            if (player.Injured && player.InjuryDays > 0)
            {
                status = $"injured ({player.InjuryDays}d)";
            }

            RecruitingInterest? rec = null;
            if (recruiting is not null)
            {
                recruiting.TryGetValue(player.PlayerId, out rec);
            }
            var report = new Dictionary<string, object?>
            {
                ["public_ovr"] = System.Math.Round(publicOvr, 1),
                ["build_name"] = buildName,
                ["role_descriptors"] = topRoles,
                ["status"] = status,
                ["class_rank"] = rec?.ClassRank,
                ["public_rating"] = rec?.PublicRating,
                ["visits"] = rec?.Visits,
                ["offers"] = rec?.OfferHistory.Count,
                ["visited_weeks"] = rec?.VisitHistory
            };

            reports[player.PlayerId] = report;
        }

        return reports;
    }
}
