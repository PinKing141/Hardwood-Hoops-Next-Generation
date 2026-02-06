namespace HardwoodHoops.Core;

public class GrowthProfile
{
    public float ShootingLearningRate { get; init; } = 1.0f;
    public float FinishingLearningRate { get; init; } = 1.0f;
    public float PlaymakingLearningRate { get; init; } = 1.0f;
    public float DefenseLearningRate { get; init; } = 1.0f;
    public float PhysicalLearningRate { get; init; } = 1.0f;
    public bool IsLateBloomer { get; init; }
}
