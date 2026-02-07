namespace HardwoodHoops.Core.Simulation.Engines;

public interface IGameEngineFactory<TGameState, TEvent>
{
    IGameEngine<TGameState, TEvent> Create(GameEngineContext<TGameState> context);
}
