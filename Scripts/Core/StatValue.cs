using System;

namespace HardwoodHoops.Core;

public struct StatValue
{
    public int Value { get; private set; }
    public float Progress { get; private set; }
    public int Cap { get; }

    public StatValue(int value, int cap)
    {
        Value = value;
        Cap = cap;
        Progress = 0f;
    }

    public bool AddProgress(float amount)
    {
        if (Value >= Cap)
        {
            return false;
        }

        Progress += amount;

        if (Progress < 100f)
        {
            return false;
        }

        Progress -= 100f;
        Value = Math.Min(Value + 1, Cap);
        return true;
    }
}
