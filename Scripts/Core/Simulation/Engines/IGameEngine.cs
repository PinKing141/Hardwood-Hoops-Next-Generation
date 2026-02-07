using System.Collections.Generic;

namespace HardwoodHoops.Core.Simulation.Engines;

public interface IGameEngine<TGameState, TEvent>
{
    IReadOnlyList<TEvent> Simulate(TGameState gameState);
}
