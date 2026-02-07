using System.Collections.Generic;

namespace HardwoodHoops.Core.Domain.Teams;

public sealed class Team
{
    public Team(string teamId, string name, string level, string region)
    {
        TeamId = teamId;
        Name = name;
        Level = level;
        Region = region;
    }

    public string TeamId { get; }
    public string Name { get; }
    public string Level { get; }
    public string Region { get; }
    public int Prestige { get; set; }
    public string? CoachId { get; set; }
    public List<string> Roster { get; } = new();
    public int Scholarships { get; set; }
    public string? Playstyle { get; set; }

    public void AddPlayer(string playerId)
    {
        if (!Roster.Contains(playerId))
        {
            Roster.Add(playerId);
        }
    }
}
