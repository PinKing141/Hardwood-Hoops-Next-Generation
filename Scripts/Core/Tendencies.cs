namespace HardwoodHoops.Core;

public readonly struct Tendencies
{
    public float Drive { get; init; }
    public float Shoot { get; init; }
    public float Pass { get; init; }

    public static Tendencies Default()
    {
        return new Tendencies
        {
            Drive = 0.35f,
            Shoot = 0.35f,
            Pass = 0.30f
        };
    }
}
