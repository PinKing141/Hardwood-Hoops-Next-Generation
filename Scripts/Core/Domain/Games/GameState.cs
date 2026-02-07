using System.Collections.Generic;

namespace HardwoodHoops.Core.Domain.Games;

public sealed class GameState
{
    public GameState(string gameId, string homeTeamId, string awayTeamId)
    {
        GameId = gameId;
        HomeTeamId = homeTeamId;
        AwayTeamId = awayTeamId;
    }

    public string GameId { get; }
    public string HomeTeamId { get; }
    public string AwayTeamId { get; }
    public int Period { get; set; } = 1;
    public int ClockSeconds { get; set; } = 20 * 60;
    public Dictionary<string, int> Score { get; } = new() { ["home"] = 0, ["away"] = 0 };
    public List<GameEvent> Events { get; } = new();
    public Dictionary<string, List<string>> Rosters { get; } = new();
    public Dictionary<string, List<string>> OnFloor { get; } = new();
    public Dictionary<string, List<string>> Bench { get; } = new();
    public Dictionary<string, double> FatigueByPlayer { get; } = new();
    public Dictionary<string, int> FoulsByPlayer { get; } = new();
    public Dictionary<string, int> TeamFouls { get; } = new();
    public Dictionary<string, bool> Injuries { get; } = new();
    public Dictionary<string, double> MinutesPlayed { get; } = new();
    public Dictionary<string, object> Metadata { get; } = new();

    public void RecordEvent(GameEvent gameEvent)
    {
        Events.Add(gameEvent);
    }
}
