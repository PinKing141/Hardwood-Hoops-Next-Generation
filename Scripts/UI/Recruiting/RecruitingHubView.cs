using Godot;
using HardwoodHoops.Core.App.Services.Recruiting;
using HardwoodHoops.Core.Domain.Recruiting;

namespace HardwoodHoops;

public partial class RecruitingHubView : Control
{
    [Signal] public delegate void OpenTop100EventHandler();
    [Signal] public delegate void OpenClassRankingsEventHandler();
    [Signal] public delegate void OpenShotDietEventHandler();
    [Signal] public delegate void OpenScoutingReportEventHandler();
    [Signal] public delegate void OpenCalendarEventHandler();
    [Signal] public delegate void OpenOffersEventHandler();
    [Signal] public delegate void OpenCommitmentsEventHandler();
    [Signal] public delegate void OpenInboxEventHandler();
    [Signal] public delegate void OpenPlayerCardEventHandler();
    [Signal] public delegate void OpenProgressionEventHandler();
    [Signal] public delegate void BackPressedEventHandler();

    private readonly RecruitingRankingDataService _data = new();

    public override void _Ready()
    {
        GetNode<Button>("Root/Cards/Top100Card/OpenButton").Pressed += () => EmitSignal(SignalName.OpenTop100);
        GetNode<Button>("Root/Cards/ClassCard/OpenButton").Pressed += () => EmitSignal(SignalName.OpenClassRankings);
        GetNode<Button>("Root/Cards/ShotDietCard/OpenButton").Pressed += () => EmitSignal(SignalName.OpenShotDiet);
        GetNode<Button>("Root/Cards/ScoutingCard/OpenButton").Pressed += () => EmitSignal(SignalName.OpenScoutingReport);
        GetNode<Button>("Root/Cards/CalendarCard/OpenButton").Pressed += () => EmitSignal(SignalName.OpenCalendar);
        GetNode<Button>("Root/Cards/OffersCard/OpenButton").Pressed += () => EmitSignal(SignalName.OpenOffers);
        GetNode<Button>("Root/Cards/CommitmentsCard/OpenButton").Pressed += () => EmitSignal(SignalName.OpenCommitments);
        GetNode<Button>("Root/Cards/InboxCard/OpenButton").Pressed += () => EmitSignal(SignalName.OpenInbox);
        GetNode<Button>("Root/Cards/PlayerCard/OpenButton").Pressed += () => EmitSignal(SignalName.OpenPlayerCard);
        GetNode<Button>("Root/Cards/ProgressionCard/OpenButton").Pressed += () => EmitSignal(SignalName.OpenProgression);

        var highlight = _data.GetHighlighted(2027);
        GetNode<Label>("Root/QuickStats/Stars").Text = $"Stars: {FormatStars(highlight.Stars)}";
        GetNode<Label>("Root/QuickStats/Rank").Text = highlight.Rank <= 100 ? $"Rank: #{highlight.Rank}" : "Rank: Unranked";
        GetNode<Label>("Root/QuickStats/Trend").Text = $"Trend: {FormatTrend(highlight.Trend)}";
        GetNode<Label>("Root/QuickStats/Offers").Text = $"Offers: {highlight.Offers.Length}";
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
}
