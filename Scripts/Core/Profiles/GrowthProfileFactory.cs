namespace HardwoodHoops.Core;

public static class GrowthProfileFactory
{
    public static GrowthProfile CreateDefault(CareerPhase phase)
    {
        return phase switch
        {
            CareerPhase.HighSchool => new GrowthProfile
            {
                ShootingLearningRate = 1.1f,
                FinishingLearningRate = 1.1f,
                PlaymakingLearningRate = 1.0f,
                DefenseLearningRate = 1.0f,
                PhysicalLearningRate = 1.1f,
                IsLateBloomer = false
            },
            CareerPhase.College => new GrowthProfile
            {
                ShootingLearningRate = 1.0f,
                FinishingLearningRate = 1.0f,
                PlaymakingLearningRate = 1.0f,
                DefenseLearningRate = 1.0f,
                PhysicalLearningRate = 0.95f,
                IsLateBloomer = false
            },
            _ => new GrowthProfile
            {
                ShootingLearningRate = 0.9f,
                FinishingLearningRate = 0.9f,
                PlaymakingLearningRate = 0.9f,
                DefenseLearningRate = 0.9f,
                PhysicalLearningRate = 0.85f,
                IsLateBloomer = false
            }
        };
    }
}
