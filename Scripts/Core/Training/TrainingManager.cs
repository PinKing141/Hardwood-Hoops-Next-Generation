using System;

namespace HardwoodHoops.Core;

public class TrainingManager
{
    public bool ApplyWeeklyTraining(PlayerProfile player, TrainingFocus focus, float intensity, Random rng)
    {
        var growth = player.GrowthProfile;
        var variance = (float)rng.NextDouble() * 4f - 2f;
        var progress = Math.Max(5f, (intensity * 20f) + variance);

        return focus switch
        {
            TrainingFocus.Finishing => player.Attributes.DrivingLayup.AddProgress(progress * growth.FinishingLearningRate),
            TrainingFocus.Shooting => player.Attributes.ThreePointShot.AddProgress(progress * growth.ShootingLearningRate),
            TrainingFocus.Playmaking => player.Attributes.PassAccuracy.AddProgress(progress * growth.PlaymakingLearningRate),
            TrainingFocus.Defense => player.Attributes.PerimeterDefense.AddProgress(progress * growth.DefenseLearningRate),
            TrainingFocus.Physical => player.Attributes.Speed.AddProgress(progress * growth.PhysicalLearningRate),
            TrainingFocus.FilmStudy => player.Attributes.OffensiveIq.AddProgress(progress),
            _ => false
        };
    }
}
