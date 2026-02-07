using System;

namespace HardwoodHoops.Core;

public class SimulationEngine
{
    public GameEvent SimulatePossession(PlayerProfile offense, PlayerProfile defense, Random rng)
    {
        var metaOffense = MetaStats.FromAttributes(offense.Attributes);
        var metaDefense = MetaStats.FromAttributes(defense.Attributes);
        var actionRoll = rng.NextDouble();

        if (actionRoll < offense.Tendencies.Drive)
        {
            return ResolveDrive(offense, metaOffense, metaDefense, rng);
        }

        if (actionRoll < offense.Tendencies.Drive + offense.Tendencies.Shoot)
        {
            return ResolveShot(offense, metaOffense, metaDefense, rng);
        }

        return new GameEvent(
            GameEventType.Assist,
            $"{offense.Name} sets up a teammate for a clean look.",
            offense.Name,
            null,
            0);
    }

    private static GameEvent ResolveDrive(PlayerProfile offense, MetaStats offenseMeta, MetaStats defenseMeta, Random rng)
    {
        var roll = rng.Next(0, 100);
        var score = offenseMeta.RimPressure + (float)roll - defenseMeta.InteriorDefense;
        var made = score > 55f;

        return new GameEvent(
            made ? GameEventType.ShotMade : GameEventType.ShotMissed,
            made
                ? $"{offense.Name} powers to the rim and scores."
                : $"{offense.Name} drives but can’t finish.",
            offense.Name,
            null,
            made ? 2 : 0);
    }

    private static GameEvent ResolveShot(PlayerProfile offense, MetaStats offenseMeta, MetaStats defenseMeta, Random rng)
    {
        var roll = rng.Next(0, 100);
        var score = offenseMeta.ShotCreation + (float)roll - defenseMeta.PerimeterDefense;
        var made = score > 60f;

        return new GameEvent(
            made ? GameEventType.ShotMade : GameEventType.ShotMissed,
            made
                ? $"{offense.Name} rises and hits the jumper."
                : $"{offense.Name} comes up empty on the jumper.",
            offense.Name,
            null,
            made ? 2 : 0);
    }
}
