using System.Collections.Generic;

namespace HardwoodHoops.Core.App.Services;

public sealed class AttributeSnapshot
{
    public AttributeSnapshot(string label, Dictionary<string, int> values)
    {
        Label = label;
        Values = values;
    }

    public string Label { get; }
    public Dictionary<string, int> Values { get; }
}

public static class ProgressionContext
{
    public static AttributeSnapshot? Previous { get; private set; }
    public static AttributeSnapshot? Current { get; private set; }

    public static void Update(AttributeSnapshot previous, AttributeSnapshot current)
    {
        Previous = previous;
        Current = current;
    }
}
