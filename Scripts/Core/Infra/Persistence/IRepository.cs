using System.Collections.Generic;

namespace HardwoodHoops.Core.Infra.Persistence;

public interface IRepository<T>
{
    void Save(T entity);
    T? GetById(string id);
    IReadOnlyList<T> ListAll();
}
