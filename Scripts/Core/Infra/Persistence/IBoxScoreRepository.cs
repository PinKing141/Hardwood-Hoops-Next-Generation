namespace HardwoodHoops.Core.Infra.Persistence;

public interface IBoxScoreRepository<TBoxScore>
{
    void Save(TBoxScore boxScore);
    TBoxScore? GetByGameId(string gameId);
}
