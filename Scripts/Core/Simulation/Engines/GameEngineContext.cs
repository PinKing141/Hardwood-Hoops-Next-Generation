using System.Collections.Generic;

namespace HardwoodHoops.Core.Simulation.Engines;

public sealed class GameEngineContext<TGameState>
{
    public GameEngineContext(TGameState gameState, IReadOnlyDictionary<string, object> metadata)
    {
        GameState = gameState;
        Metadata = metadata;
    }

    public TGameState GameState { get; }
    public IReadOnlyDictionary<string, object> Metadata { get; }
}
