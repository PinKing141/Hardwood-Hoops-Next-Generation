using System.Collections.Generic;

namespace HardwoodHoops.Core.Domain.Games;

public sealed class GameEvent
{
    public GameEvent(string eventType, string description, Dictionary<string, object> payload, double timestamp)
    {
        EventType = eventType;
        Description = description;
        Payload = payload;
        Timestamp = timestamp;
    }

    public string EventType { get; }
    public string Description { get; }
    public Dictionary<string, object> Payload { get; }
    public double Timestamp { get; }
}
