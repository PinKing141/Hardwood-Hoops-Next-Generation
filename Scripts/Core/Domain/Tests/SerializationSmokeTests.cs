using System.Text.Json;
using HardwoodHoops.Core.Domain.Games;
using HardwoodHoops.Core.Domain.Players;
using HardwoodHoops.Core.Domain.Recruiting;
using HardwoodHoops.Core.Domain.Teams;

namespace HardwoodHoops.Core.Domain.Tests;

public static class SerializationSmokeTests
{
    public static bool CanRoundTripPlayer()
    {
        var player = new Player(
            playerId: "P1",
            name: "Test Player",
            classYear: "HS FR",
            attributes: new PlayerAttributes(60, 55, 62, 58, 57, 65, 50, 55, 60, 52, 54, 50, 48, 45, 70, 68, 72, 60, 75, 64, 62, 66, 80, 40, 55, 58, 52),
            tendencies: PlayerTendencies.Default(),
            personality: PlayerPersonality.Default());

        var json = JsonSerializer.Serialize(player);
        var restored = JsonSerializer.Deserialize<Player>(json);
        return restored is not null && restored.PlayerId == player.PlayerId;
    }

    public static bool CanRoundTripTeam()
    {
        var team = new Team("T1", "Test Team", "D1", "West") { Prestige = 60, Scholarships = 12 };
        team.AddPlayer("P1");
        var json = JsonSerializer.Serialize(team);
        var restored = JsonSerializer.Deserialize<Team>(json);
        return restored is not null && restored.TeamId == team.TeamId;
    }

    public static bool CanRoundTripGameState()
    {
        var state = new GameState("G1", "HOME", "AWAY");
        state.RecordEvent(new GameEvent("tip", "Tip off", new(), 0));
        var json = JsonSerializer.Serialize(state);
        var restored = JsonSerializer.Deserialize<GameState>(json);
        return restored is not null && restored.GameId == state.GameId;
    }

    public static bool CanRoundTripRecruiting()
    {
        var interest = new RecruitingInterest("P1", "T1", 0.5, 0.7) { OfferMade = true, Visits = 2 };
        var json = JsonSerializer.Serialize(interest);
        var restored = JsonSerializer.Deserialize<RecruitingInterest>(json);
        return restored is not null && restored.PlayerId == interest.PlayerId;
    }
}
