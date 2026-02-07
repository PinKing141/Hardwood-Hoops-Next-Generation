using System;
using System.Collections.Generic;

namespace HardwoodHoops.Core.Simulation.Rng;

public sealed class SeededRng : IRng
{
    private readonly Random _random;

    public SeededRng(int? seed = null)
    {
        _random = seed.HasValue ? new Random(seed.Value) : new Random();
    }

    public int NextInt(int minInclusive, int maxInclusive)
    {
        return _random.Next(minInclusive, maxInclusive + 1);
    }

    public double NextDouble()
    {
        return _random.NextDouble();
    }

    public T Choice<T>(IReadOnlyList<T> items)
    {
        if (items.Count == 0)
        {
            throw new ArgumentException("Cannot choose from an empty list.", nameof(items));
        }

        return items[_random.Next(0, items.Count)];
    }

    public T ChoiceWeighted<T>(IReadOnlyList<T> items, IReadOnlyList<double> weights)
    {
        if (items.Count == 0)
        {
            throw new ArgumentException("Cannot choose from an empty list.", nameof(items));
        }

        if (items.Count != weights.Count)
        {
            throw new ArgumentException("Items and weights must be the same length.");
        }

        double total = 0;
        foreach (var weight in weights)
        {
            total += Math.Max(0, weight);
        }

        if (total <= 0)
        {
            return Choice(items);
        }

        var roll = _random.NextDouble() * total;
        double cumulative = 0;
        for (var i = 0; i < items.Count; i++)
        {
            cumulative += Math.Max(0, weights[i]);
            if (roll <= cumulative)
            {
                return items[i];
            }
        }

        return items[^1];
    }
}
