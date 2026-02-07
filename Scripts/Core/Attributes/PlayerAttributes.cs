namespace HardwoodHoops.Core;

public class PlayerAttributes
{
    public StatValue CloseShot { get; private set; }
    public StatValue DrivingLayup { get; private set; }
    public StatValue DrivingDunk { get; private set; }
    public StatValue StandingDunk { get; private set; }
    public StatValue PostControl { get; private set; }

    public StatValue MidRangeShot { get; private set; }
    public StatValue ThreePointShot { get; private set; }
    public StatValue FreeThrow { get; private set; }

    public StatValue PassAccuracy { get; private set; }
    public StatValue BallHandle { get; private set; }
    public StatValue SpeedWithBall { get; private set; }

    public StatValue InteriorDefense { get; private set; }
    public StatValue PerimeterDefense { get; private set; }
    public StatValue Steal { get; private set; }
    public StatValue Block { get; private set; }
    public StatValue OffensiveRebound { get; private set; }
    public StatValue DefensiveRebound { get; private set; }

    public StatValue Speed { get; private set; }
    public StatValue Acceleration { get; private set; }
    public StatValue Strength { get; private set; }
    public StatValue Vertical { get; private set; }
    public StatValue Stamina { get; private set; }

    public StatValue Hustle { get; private set; }
    public StatValue PassPerception { get; private set; }
    public StatValue OffensiveConsistency { get; private set; }
    public StatValue DefensiveConsistency { get; private set; }
    public StatValue Intangibles { get; private set; }
    public StatValue Potential { get; private set; }
    public StatValue OffensiveIq { get; private set; }
    public StatValue DefensiveIq { get; private set; }

    public PlayerAttributes(PlayerAttributeDefaults defaults)
    {
        CloseShot = new StatValue(defaults.CloseShot, defaults.Cap);
        DrivingLayup = new StatValue(defaults.DrivingLayup, defaults.Cap);
        DrivingDunk = new StatValue(defaults.DrivingDunk, defaults.Cap);
        StandingDunk = new StatValue(defaults.StandingDunk, defaults.Cap);
        PostControl = new StatValue(defaults.PostControl, defaults.Cap);

        MidRangeShot = new StatValue(defaults.MidRangeShot, defaults.Cap);
        ThreePointShot = new StatValue(defaults.ThreePointShot, defaults.Cap);
        FreeThrow = new StatValue(defaults.FreeThrow, defaults.Cap);

        PassAccuracy = new StatValue(defaults.PassAccuracy, defaults.Cap);
        BallHandle = new StatValue(defaults.BallHandle, defaults.Cap);
        SpeedWithBall = new StatValue(defaults.SpeedWithBall, defaults.Cap);

        InteriorDefense = new StatValue(defaults.InteriorDefense, defaults.Cap);
        PerimeterDefense = new StatValue(defaults.PerimeterDefense, defaults.Cap);
        Steal = new StatValue(defaults.Steal, defaults.Cap);
        Block = new StatValue(defaults.Block, defaults.Cap);
        OffensiveRebound = new StatValue(defaults.OffensiveRebound, defaults.Cap);
        DefensiveRebound = new StatValue(defaults.DefensiveRebound, defaults.Cap);

        Speed = new StatValue(defaults.Speed, defaults.Cap);
        Acceleration = new StatValue(defaults.Acceleration, defaults.Cap);
        Strength = new StatValue(defaults.Strength, defaults.Cap);
        Vertical = new StatValue(defaults.Vertical, defaults.Cap);
        Stamina = new StatValue(defaults.Stamina, defaults.Cap);

        Hustle = new StatValue(defaults.Hustle, defaults.Cap);
        PassPerception = new StatValue(defaults.PassPerception, defaults.Cap);
        OffensiveConsistency = new StatValue(defaults.OffensiveConsistency, defaults.Cap);
        DefensiveConsistency = new StatValue(defaults.DefensiveConsistency, defaults.Cap);
        Intangibles = new StatValue(defaults.Intangibles, defaults.Cap);
        Potential = new StatValue(defaults.Potential, defaults.Cap);
        OffensiveIq = new StatValue(defaults.OffensiveIq, defaults.Cap);
        DefensiveIq = new StatValue(defaults.DefensiveIq, defaults.Cap);
    }
}
