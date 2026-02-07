namespace HardwoodHoops.Core.Domain.Players;

public record PlayerPersonality(
    double WorkEthic,
    double Coachability,
    double Competitiveness
)
{
    public static PlayerPersonality Default() => new(0.5, 0.5, 0.5);
}
