using System;
using System.IO;
using System.Linq;
using Godot;

namespace HardwoodHoops.Core.Infra.Persistence.Local;

internal static class SavePaths
{
    private static readonly string SaveRoot = Path.Combine(ProjectSettings.GlobalizePath("user://"), "saves");

    public static void EnsureRoot()
    {
        Directory.CreateDirectory(SaveRoot);
    }

    public static string GameStatePath(string gameId) => Path.Combine(SaveRoot, $"game_{Sanitize(gameId)}.json");
    public static string EventsPath(string gameId) => Path.Combine(SaveRoot, $"events_{Sanitize(gameId)}.json");
    public static string BoxScorePath(string gameId) => Path.Combine(SaveRoot, $"boxscore_{Sanitize(gameId)}.json");

    private static string Sanitize(string value)
    {
        var invalid = Path.GetInvalidFileNameChars();
        var cleaned = new string(value.Select(ch => invalid.Contains(ch) ? '_' : ch).ToArray());
        return string.IsNullOrWhiteSpace(cleaned) ? "unknown" : cleaned;
    }
}
