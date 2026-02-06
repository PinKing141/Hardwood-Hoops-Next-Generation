namespace HardwoodHoops.Core;

public readonly record struct GameEvent(
    GameEventType EventType,
    string Description,
    string PrimaryPlayer,
    string? SecondaryPlayer,
    int Points);
