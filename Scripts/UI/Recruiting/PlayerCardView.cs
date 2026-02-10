using Godot;
using HardwoodHoops.Core.App.Services.Recruiting;

namespace HardwoodHoops;

public partial class PlayerCardView : Control
{
    [Signal] public delegate void BackPressedEventHandler();

    public override void _Ready()
    {
        if (RecruitingRankingContext.TryGet(2027, out var entry))
        {
            GetNode<Label>("Root/Title").Text = $"Player Card — {entry.PlayerName}";
            GetNode<Label>("Root/Vitals").Text = $"{entry.Position}  {FormatHeight(entry.HeightInches)}  {entry.WeightLbs} lbs";
            GetNode<Label>("Root/Stars").Text = $"Stars: {FormatStars(entry.Stars)}";
            GetNode<Label>("Root/Rank").Text = entry.Rank <= 100 ? $"Rank: #{entry.Rank}" : "Rank: Unranked";
            GetNode<Label>("Root/Trend").Text = $"Trend: {FormatTrend(entry.Trend)}";
            GetNode<Label>("Root/Build").Text = $"Build: {entry.Build}";
            GetNode<Label>("Root/Tags").Text = $"Tags: {string.Join(", ", entry.Tags)}";
            GetNode<Label>("Root/ShotDiet").Text =
                $"Shot Diet: Close {Pct(entry.ShotClose)} | Mid {Pct(entry.ShotMid)} | Three {Pct(entry.ShotThree)}";
        }
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event.IsActionPressed("ui_cancel"))
        {
            EmitSignal(SignalName.BackPressed);
        }
    }

    private static string FormatStars(int stars) => new string('?', stars).PadRight(5, '?');

    private static string FormatTrend(Core.Domain.Recruiting.RecruitTrend trend)
    {
        return trend switch
        {
            Core.Domain.Recruiting.RecruitTrend.Rising => "? Rising",
            Core.Domain.Recruiting.RecruitTrend.Falling => "? Falling",
            _ => "— Stable"
        };
    }

    private static string FormatHeight(int inches)
    {
        var feet = inches / 12;
        var rem = inches % 12;
        return $"{feet}'{rem}\"";
    }

    private static string Pct(float value)
    {
        return $"{Mathf.RoundToInt(value * 100f)}%";
    }
}
