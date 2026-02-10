using Godot;
using HardwoodHoops.Core.App.Services.Recruiting;

namespace HardwoodHoops;

public partial class ShotDietView : Control
{
    [Signal] public delegate void BackPressedEventHandler();

    public override void _Ready()
    {
        if (RecruitingRankingContext.TryGet(2027, out var entry))
        {
            GetNode<Label>("Root/Header/Title").Text = $"Shot Diet — {entry.PlayerName} ({entry.Position})";
            GetNode<Label>("Root/Header/Meta").Text = $"NextGen Rank: #{entry.Rank}  •  {FormatStars(entry.Stars)}  •  Trend: {FormatTrend(entry.Trend)}";
            GetNode<Label>("Root/Overview/OverviewLines").Text =
                $"- Primary Role: {entry.Build}\n" +
                $"- Shot Profile: Close {Pct(entry.ShotClose)} | Mid {Pct(entry.ShotMid)} | Three {Pct(entry.ShotThree)}\n" +
                $"- Rim Attack: Layup {Pct(entry.RimLayup)} | Dunk {Pct(entry.RimDunk)}\n" +
                $"- Creation Type: Catch {Pct(entry.CreationCatch)} | Pull-Up {Pct(entry.CreationPull)} | Rim {Pct(entry.CreationDrive)}";

            GetNode<Label>("Root/Creation/CreationLines").Text =
                $"- Catch & Shoot: {Pct(entry.CreationCatch)}\n" +
                $"- Pull-Up: {Pct(entry.CreationPull)}\n" +
                $"- Off the Drive: {Pct(entry.CreationDrive)}";

            GetNode<Label>("Root/Quality/QualityLines").Text =
                $"- At Rim: {Pct(entry.RimLayup + entry.RimDunk)} (Layup {Pct(entry.RimLayup)} / Dunk {Pct(entry.RimDunk)})\n" +
                $"- Short Mid: {Pct(entry.ShotClose)}\n" +
                $"- Long Mid: {Pct(entry.ShotMid)}\n" +
                $"- Threes: {Pct(entry.ShotThree)}";
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
