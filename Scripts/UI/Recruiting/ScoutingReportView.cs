using Godot;
using HardwoodHoops.Core.App.Services.Recruiting;

namespace HardwoodHoops;

public partial class ScoutingReportView : Control
{
    [Signal] public delegate void BackPressedEventHandler();

    public override void _Ready()
    {
        if (RecruitingRankingContext.TryGet(2027, out var entry))
        {
            GetNode<Label>("Root/Header/Title").Text = $"Scouting Report — {entry.PlayerName} ({entry.Position})";
            GetNode<Label>("Root/Header/Meta").Text = $"NextGen Top 100: #{entry.Rank}  •  {FormatStars(entry.Stars)}  •  Trend: {FormatTrend(entry.Trend)}";
            GetNode<Label>("Root/Build").Text = $"Build: {entry.Build}";
            GetNode<Label>("Root/Snapshot/SnapshotLines").Text =
                $"- Shot Profile: Close {Pct(entry.ShotClose)} | Mid {Pct(entry.ShotMid)} | Three {Pct(entry.ShotThree)}\n" +
                $"- Rim Attack: Layup {Pct(entry.RimLayup)} | Dunk {Pct(entry.RimDunk)}\n" +
                $"- Creation: Catch {Pct(entry.CreationCatch)} | Pull-Up {Pct(entry.CreationPull)} | Rim {Pct(entry.CreationDrive)}\n" +
                $"- Defence: Disciplined 55% | Gambler 45%";
        }
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event.IsActionPressed("ui_cancel"))
        {
            EmitSignal(SignalName.BackPressed);
        }
    }

    private static string FormatStars(int stars)
    {
        return new string('?', stars).PadRight(5, '?');
    }

    private static string FormatTrend(RecruitTrend trend)
    {
        return trend switch
        {
            RecruitTrend.Rising => "? Rising",
            RecruitTrend.Falling => "? Falling",
            _ => "— Stable"
        };
    }

    private static string Pct(float value)
    {
        return $"{Mathf.RoundToInt(value * 100f)}%";
    }
}
