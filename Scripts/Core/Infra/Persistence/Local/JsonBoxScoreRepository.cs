using System.IO;
using System.Text.Json;
using HardwoodHoops.Core.Domain.Games;

namespace HardwoodHoops.Core.Infra.Persistence.Local;

public sealed class JsonBoxScoreRepository : IBoxScoreRepository<BoxScore>
{
    private readonly JsonSerializerOptions _options = new()
    {
        WriteIndented = true,
        PropertyNameCaseInsensitive = true
    };

    public void Save(BoxScore boxScore)
    {
        SavePaths.EnsureRoot();
        var json = JsonSerializer.Serialize(boxScore, _options);
        File.WriteAllText(SavePaths.BoxScorePath(boxScore.GameId), json);
    }

    public BoxScore? GetByGameId(string gameId)
    {
        var path = SavePaths.BoxScorePath(gameId);
        if (!File.Exists(path))
        {
            return null;
        }

        var json = File.ReadAllText(path);
        return JsonSerializer.Deserialize<BoxScore>(json, _options);
    }
}
