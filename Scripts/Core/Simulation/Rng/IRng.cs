namespace HardwoodHoops.Core.Simulation.Rng;

public interface IRng
{
    int NextInt(int minInclusive, int maxInclusive);
    double NextDouble();
    T Choice<T>(IReadOnlyList<T> items);
    T ChoiceWeighted<T>(IReadOnlyList<T> items, IReadOnlyList<double> weights);
}
