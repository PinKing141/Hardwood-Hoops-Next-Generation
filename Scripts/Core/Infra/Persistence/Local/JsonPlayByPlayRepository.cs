using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using HardwoodHoops.Core.Domain.Games;

namespace HardwoodHoops.Core.Infra.Persistence.Local;

public sealed class JsonPlayByPlayRepository : IPlayByPlayRepository<GameEvent>
{
    private readonly JsonSerializerOptions _options = new()
    {
        WriteIndented = true,
        PropertyNameCaseInsensitive = true
    };

    public void SaveEvents(string gameId, IReadOnlyList<GameEvent> events)
    {
        SavePaths.EnsureRoot();
        var json = JsonSerializer.Serialize(events, _options);
        File.WriteAllText(SavePaths.EventsPath(gameId), json);
    }

    public IReadOnlyList<GameEvent> LoadEvents(string gameId)
    {
        var path = SavePaths.EventsPath(gameId);
        if (!File.Exists(path))
        {
            return new List<GameEvent>();
        }

        var json = File.ReadAllText(path);
        return JsonSerializer.Deserialize<List<GameEvent>>(json, _options) ?? new List<GameEvent>();
    }
}
