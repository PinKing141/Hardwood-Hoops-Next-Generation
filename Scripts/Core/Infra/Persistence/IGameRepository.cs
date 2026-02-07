namespace HardwoodHoops.Core.Infra.Persistence;

public interface IGameRepository<TGameState>
{
    void Save(TGameState state);
    TGameState? GetById(string gameId);
}
