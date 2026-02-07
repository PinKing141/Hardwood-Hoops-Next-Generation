using System.Collections.Generic;

namespace HardwoodHoops.Core;

public class EventLog
{
    private readonly List<GameEvent> _events = new();

    public int Count => _events.Count;
    public IReadOnlyList<GameEvent> Events => _events;

    public void Add(GameEvent gameEvent)
    {
        _events.Add(gameEvent);
    }
}
