using System.Collections.Generic;

namespace HardwoodHoops.Core.Infra.Persistence;

public interface IPlayByPlayRepository<TEvent>
{
    void SaveEvents(string gameId, IReadOnlyList<TEvent> events);
    IReadOnlyList<TEvent> LoadEvents(string gameId);
}
