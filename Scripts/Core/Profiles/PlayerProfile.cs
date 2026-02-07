using System;

namespace HardwoodHoops.Core;

public class PlayerProfile
{
    public string Name { get; }
    public Position Position { get; }
    public CareerPhase CareerPhase { get; private set; }
    public PlayerAttributes Attributes { get; }
    public GrowthProfile GrowthProfile { get; }
    public Tendencies Tendencies { get; }
    public float Fatigue { get; private set; } = 0.1f;
    public float Health { get; private set; } = 1.0f;

    public PlayerProfile(
        string name,
        Position position,
        CareerPhase careerPhase,
        PlayerAttributes attributes,
        GrowthProfile growthProfile,
        Tendencies tendencies)
    {
        Name = name;
        Position = position;
        CareerPhase = careerPhase;
        Attributes = attributes;
        GrowthProfile = growthProfile;
        Tendencies = tendencies;
    }

    public void ApplyFatigue(float amount)
    {
        Fatigue = Math.Clamp(Fatigue + amount, 0f, 1f);
    }

    public void Recover(float amount)
    {
        Fatigue = Math.Clamp(Fatigue - amount, 0f, 1f);
    }

    public static PlayerProfile CreateSample(string name, Position position, CareerPhase phase)
    {
        var defaults = AttributeFactory.CreateDefaults(position, phase);
        return new PlayerProfile(
            name,
            position,
            phase,
            new PlayerAttributes(defaults),
            GrowthProfileFactory.CreateDefault(phase),
            Tendencies.Default());
    }
}
