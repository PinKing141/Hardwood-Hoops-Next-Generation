using System.IO;
using System.Text.Json;
using HardwoodHoops.Core.Domain.Games;

namespace HardwoodHoops.Core.Infra.Persistence.Local;

public sealed class JsonGameRepository : IGameRepository<GameState>
{
    private readonly JsonSerializerOptions _options = new()
    {
        WriteIndented = true,
        PropertyNameCaseInsensitive = true
    };

    public void Save(GameState state)
    {
        SavePaths.EnsureRoot();
        var json = JsonSerializer.Serialize(state, _options);
        File.WriteAllText(SavePaths.GameStatePath(state.GameId), json);
    }

    public GameState? GetById(string gameId)
    {
        var path = SavePaths.GameStatePath(gameId);
        if (!File.Exists(path))
        {
            return null;
        }

        var json = File.ReadAllText(path);
        return JsonSerializer.Deserialize<GameState>(json, _options);
    }
}
