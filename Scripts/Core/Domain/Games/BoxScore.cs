using System.Collections.Generic;

namespace HardwoodHoops.Core.Domain.Games;

public sealed class BoxScore
{
    public BoxScore(
        string gameId,
        string homeTeamId,
        string awayTeamId,
        int homeScore,
        int awayScore,
        Dictionary<string, object> payload)
    {
        GameId = gameId;
        HomeTeamId = homeTeamId;
        AwayTeamId = awayTeamId;
        HomeScore = homeScore;
        AwayScore = awayScore;
        Payload = payload;
    }

    public string GameId { get; }
    public string HomeTeamId { get; }
    public string AwayTeamId { get; }
    public int HomeScore { get; }
    public int AwayScore { get; }
    public Dictionary<string, object> Payload { get; }
}
