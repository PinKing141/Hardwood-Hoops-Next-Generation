using System;
using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Games;

namespace HardwoodHoops.Core.Simulation.PlayByPlay;

public sealed class EventBuilder
{
    public GameEvent Build(string eventType, string description, Dictionary<string, object> payload)
    {
        var timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        return new GameEvent(eventType, description, payload, timestamp);
    }
}
