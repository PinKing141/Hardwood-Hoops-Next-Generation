using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Players;

namespace HardwoodHoops.Core.App.Services;

public sealed class BuildNameService
{
    private readonly RoleAffinityService _roleAffinity;

    public BuildNameService(RoleAffinityService? roleAffinity = null)
    {
        _roleAffinity = roleAffinity ?? new RoleAffinityService();
    }

    public string GenerateName(Player player, Dictionary<string, string>? positionMap = null)
    {
        var affinities = _roleAffinity.TopRoles(player, 3);
        var primaryRole = affinities.Count > 0 ? new List<string>(affinities.Keys)[0] : "balanced";
        var group = PositionGroup(player, positionMap);

        var name = RuleAName(player, affinities, primaryRole, group);
        if (string.IsNullOrWhiteSpace(name))
        {
            name = RuleBName(primaryRole, group);
        }

        return TrimWords(name);
    }

    private string RuleAName(Player player, Dictionary<string, double> affinities, string primaryRole, string? group)
    {
        var defensivePrefix = DefensivePrefix(player, affinities);
        var offensiveCore = OffensiveCore(primaryRole, group);
        var specialization = Specialization(primaryRole, group);
        var parts = new List<string>();
        if (!string.IsNullOrWhiteSpace(defensivePrefix))
        {
            parts.Add(defensivePrefix);
        }
        if (!string.IsNullOrWhiteSpace(specialization))
        {
            parts.Add(specialization);
        }
        parts.Add(offensiveCore);
        return string.Join(' ', parts).Trim();
    }

    private string RuleBName(string primaryRole, string? group)
    {
        var descriptor = BestDescriptor(primaryRole, group);
        var noun = BestNoun(primaryRole, group);
        return $"{descriptor} {noun}".Trim();
    }

    private string DefensivePrefix(Player player, Dictionary<string, double> affinities)
    {
        var attrs = player.Attributes;
        var defenseScore = (attrs.PerimeterDefense + attrs.InteriorDefense + attrs.Steal + attrs.Block) / 4.0;
        var shootScore = (attrs.ThreePoint + attrs.FreeThrow) / 2.0;
        if (defenseScore >= 75 && shootScore >= 70)
        {
            return "3 & D";
        }
        if (defenseScore >= 80)
        {
            return "2 Way";
        }
        var topDef = affinities.GetValueOrDefault("defensive_stopper");
        return topDef >= 0.2 ? "2 Way" : string.Empty;
    }

    private string OffensiveCore(string primaryRole, string? group)
    {
        var mapping = new Dictionary<string, string>
        {
            ["rim_pressure_wing"] = "Slasher",
            ["spot_up_shooter"] = "Shooter",
            ["secondary_creator"] = "Shot Creator",
            ["primary_creator"] = "Playmaker",
            ["defensive_stopper"] = "Defender",
            ["glass_cleaner"] = "Glass Cleaner",
            ["stretch_big"] = "Stretch Four"
        };

        var core = mapping.GetValueOrDefault(primaryRole, "Shot Creator");
        return core;
    }

    private string Specialization(string primaryRole, string? group)
    {
        var mapping = new Dictionary<string, string>
        {
            ["rim_pressure_wing"] = "Slashing",
            ["spot_up_shooter"] = "3 PT",
            ["secondary_creator"] = "Inside Out",
            ["primary_creator"] = "3 Level",
            ["stretch_big"] = "Floor Spacing"
        };

        return mapping.GetValueOrDefault(primaryRole, string.Empty);
    }

    private static string BestDescriptor(string primaryRole, string? group)
    {
        var pref = new Dictionary<string, string>
        {
            ["rim_pressure_wing"] = "Slashing",
            ["spot_up_shooter"] = "Sharpshooting",
            ["secondary_creator"] = "Shot Creating",
            ["primary_creator"] = "Playmaking",
            ["glass_cleaner"] = "Rebounding",
            ["stretch_big"] = "Floor Spacing",
            ["defensive_stopper"] = "Lockdown"
        };
        return pref.GetValueOrDefault(primaryRole, "Shot Creating");
    }

    private static string BestNoun(string primaryRole, string? group)
    {
        var pref = new Dictionary<string, string>
        {
            ["rim_pressure_wing"] = "Wing",
            ["spot_up_shooter"] = "Wing",
            ["secondary_creator"] = "Guard",
            ["primary_creator"] = "Guard",
            ["glass_cleaner"] = "Big",
            ["stretch_big"] = "Four",
            ["defensive_stopper"] = "Defender"
        };
        return pref.GetValueOrDefault(primaryRole, "Guard");
    }

    private static string TrimWords(string name)
    {
        var parts = name.Split(' ');
        if (parts.Length <= 5)
        {
            return name.Trim();
        }
        return string.Join(' ', parts[..5]);
    }

    private static string? PositionGroup(Player player, Dictionary<string, string>? positionMap)
    {
        if (positionMap is not null && positionMap.TryGetValue(player.PlayerId, out var posCode))
        {
            return PositionGroupFromCode(posCode);
        }

        if (player.Stats.TryGetValue("position", out var posObj))
        {
            return PositionGroupFromCode(posObj.ToString() ?? string.Empty);
        }

        return null;
    }

    private static string? PositionGroupFromCode(string code)
    {
        var upper = code.ToUpperInvariant();
        return upper switch
        {
            "PG" => "guard",
            "SG" => "wing",
            "SF" => "forward",
            "PF" => "big",
            "C" => "center",
            _ => null
        };
    }
}
