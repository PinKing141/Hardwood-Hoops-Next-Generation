namespace HardwoodHoops.Core;

public static class AttributeFactory
{
    public static PlayerAttributeDefaults CreateDefaults(Position position, CareerPhase phase)
    {
        var cap = phase switch
        {
            CareerPhase.HighSchool => 75,
            CareerPhase.College => 85,
            _ => 95
        };

        return position switch
        {
            Position.PointGuard => new PlayerAttributeDefaults
            {
                Cap = cap,
                BallHandle = 70,
                PassAccuracy = 68,
                Speed = 72,
                Acceleration = 70,
                ThreePointShot = 62,
                InteriorDefense = 35,
                PerimeterDefense = 55,
                Strength = 40,
                Stamina = 70,
                SpeedWithBall = 70,
                MidRangeShot = 60,
                CloseShot = 55,
                DrivingLayup = 62,
                DrivingDunk = 45,
                StandingDunk = 20,
                PostControl = 30,
                FreeThrow = 65,
                Steal = 55,
                Block = 25,
                OffensiveRebound = 30,
                DefensiveRebound = 35,
                Vertical = 55,
                Hustle = 60,
                PassPerception = 55,
                OffensiveConsistency = 60,
                DefensiveConsistency = 55,
                Intangibles = 50,
                Potential = 70,
                OffensiveIq = 55,
                DefensiveIq = 50
            },
            Position.Center => new PlayerAttributeDefaults
            {
                Cap = cap,
                BallHandle = 35,
                PassAccuracy = 45,
                Speed = 50,
                Acceleration = 48,
                ThreePointShot = 40,
                InteriorDefense = 70,
                PerimeterDefense = 35,
                Strength = 80,
                Stamina = 65,
                SpeedWithBall = 40,
                MidRangeShot = 45,
                CloseShot = 70,
                DrivingLayup = 55,
                DrivingDunk = 65,
                StandingDunk = 75,
                PostControl = 65,
                FreeThrow = 55,
                Steal = 30,
                Block = 70,
                OffensiveRebound = 70,
                DefensiveRebound = 75,
                Vertical = 60,
                Hustle = 65,
                PassPerception = 40,
                OffensiveConsistency = 55,
                DefensiveConsistency = 65,
                Intangibles = 50,
                Potential = 70,
                OffensiveIq = 50,
                DefensiveIq = 60
            },
            _ => new PlayerAttributeDefaults
            {
                Cap = cap,
                BallHandle = 55,
                PassAccuracy = 55,
                Speed = 60,
                Acceleration = 58,
                ThreePointShot = 55,
                InteriorDefense = 50,
                PerimeterDefense = 50,
                Strength = 55,
                Stamina = 65,
                SpeedWithBall = 55,
                MidRangeShot = 55,
                CloseShot = 55,
                DrivingLayup = 55,
                DrivingDunk = 50,
                StandingDunk = 45,
                PostControl = 50,
                FreeThrow = 60,
                Steal = 45,
                Block = 45,
                OffensiveRebound = 50,
                DefensiveRebound = 55,
                Vertical = 55,
                Hustle = 55,
                PassPerception = 50,
                OffensiveConsistency = 55,
                DefensiveConsistency = 55,
                Intangibles = 50,
                Potential = 70,
                OffensiveIq = 52,
                DefensiveIq = 52
            }
        };
    }
}
