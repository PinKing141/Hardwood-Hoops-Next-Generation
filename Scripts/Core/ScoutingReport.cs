using System.Linq;

namespace HardwoodHoops.Core;

public class ScoutingReport
{
    public float PublicOvr { get; private set; }
    public float PrivateOvr { get; private set; }
    public int HypePoints { get; private set; }

    public void UpdateFromEventLog(EventLog log, PlayerProfile player)
    {
        var highlights = log.Events.Count(e => e.PrimaryPlayer == player.Name && e.EventType == GameEventType.ShotMade);
        var turnovers = log.Events.Count(e => e.PrimaryPlayer == player.Name && e.EventType == GameEventType.Turnover);
        var points = log.Events.Where(e => e.PrimaryPlayer == player.Name).Sum(e => e.Points);

        var meta = MetaStats.FromAttributes(player.Attributes);
        PublicOvr = (points * 1.5f) + (highlights * 4f);
        PrivateOvr = (meta.PlaymakingImpact + meta.ShotCreation + meta.DefensiveIqImpact) / 3f - (turnovers * 2f);
        HypePoints = (int)(PublicOvr * 0.5f);
    }
}
