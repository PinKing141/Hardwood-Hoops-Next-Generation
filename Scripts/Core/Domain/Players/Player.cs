using System.Collections.Generic;

namespace HardwoodHoops.Core.Domain.Players;

public sealed class Player
{
    public Player(
        string playerId,
        string name,
        string classYear,
        PlayerAttributes attributes,
        PlayerTendencies tendencies,
        PlayerPersonality personality)
    {
        PlayerId = playerId;
        Name = name;
        ClassYear = classYear;
        Attributes = attributes;
        Tendencies = tendencies;
        Personality = personality;
    }

    public string PlayerId { get; }
    public string Name { get; }
    public string ClassYear { get; set; }
    public PlayerAttributes Attributes { get; set; }
    public PlayerTendencies Tendencies { get; }
    public PlayerPersonality Personality { get; }
    public double Fatigue { get; set; }
    public bool Injured { get; set; }
    public int InjuryDays { get; set; }
    public string? InjuryType { get; set; }
    public string? InjurySeverity { get; set; }
    public string? InjuryStatus { get; set; }
    public Dictionary<string, object> Stats { get; } = new();
    public double MinutesAllocation { get; set; } = 20.0;
    public List<string> Badges { get; } = new();
    public string? Archetype { get; set; }

    public void ResetFatigue()
    {
        Fatigue = 0.0;
    }
}
