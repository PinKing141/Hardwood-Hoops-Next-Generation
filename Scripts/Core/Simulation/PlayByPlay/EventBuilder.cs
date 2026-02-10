using System;
using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Games;
using DomainGameEvent = HardwoodHoops.Core.Domain.Games.GameEvent;

namespace HardwoodHoops.Core.Simulation.PlayByPlay;

public sealed class EventBuilder
{
    public DomainGameEvent Build(string eventType, string description, Dictionary<string, object> payload)
    {
        var timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        return new DomainGameEvent(eventType, description, payload, timestamp);
    }
}
