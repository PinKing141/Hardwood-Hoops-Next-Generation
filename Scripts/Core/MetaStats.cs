namespace HardwoodHoops.Core;

public readonly struct MetaStats
{
    public float ShotCreation { get; init; }
    public float RimPressure { get; init; }
    public float PerimeterDefense { get; init; }
    public float InteriorDefense { get; init; }
    public float PlaymakingImpact { get; init; }
    public float ReboundingImpact { get; init; }
    public float OffensiveIqImpact { get; init; }
    public float DefensiveIqImpact { get; init; }

    public static MetaStats FromAttributes(PlayerAttributes attributes)
    {
        return new MetaStats
        {
            ShotCreation = (attributes.MidRangeShot.Value + attributes.ThreePointShot.Value + attributes.BallHandle.Value) / 3f,
            RimPressure = (attributes.DrivingLayup.Value + attributes.DrivingDunk.Value + attributes.SpeedWithBall.Value) / 3f,
            PerimeterDefense = (attributes.PerimeterDefense.Value + attributes.Steal.Value + attributes.DefensiveIq.Value) / 3f,
            InteriorDefense = (attributes.InteriorDefense.Value + attributes.Block.Value + attributes.DefensiveIq.Value) / 3f,
            PlaymakingImpact = (attributes.PassAccuracy.Value + attributes.BallHandle.Value + attributes.OffensiveIq.Value) / 3f,
            ReboundingImpact = (attributes.OffensiveRebound.Value + attributes.DefensiveRebound.Value + attributes.Vertical.Value) / 3f,
            OffensiveIqImpact = attributes.OffensiveIq.Value,
            DefensiveIqImpact = attributes.DefensiveIq.Value
        };
    }
}
