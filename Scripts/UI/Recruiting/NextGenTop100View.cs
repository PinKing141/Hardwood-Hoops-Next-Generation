using Godot;
using HardwoodHoops.Core.App.Services.Recruiting;
using HardwoodHoops.Core.Domain.Recruiting;
using System.Linq;

namespace HardwoodHoops;

public partial class NextGenTop100View : Control
{
    [Signal] public delegate void BackPressedEventHandler();

    private readonly RecruitingRankingDataService _data = new();

    public override void _Ready()
    {
        var rows = GetNode<VBoxContainer>("Root/Body/Table/Rows/RowList");
        foreach (var child in rows.GetChildren())
        {
            child.QueueFree();
        }

        var entries = _data.GetTop100(2027).Take(25).ToList();
        foreach (var entry in entries)
        {
            rows.AddChild(BuildRow(entry));
        }

        var highlight = _data.GetHighlighted(2027);
        GetNode<Label>("Root/Body/SidePanel/CardRank").Text = $"Rank: #{highlight.Rank}";
        GetNode<Label>("Root/Body/SidePanel/CardStars").Text = $"Stars: {FormatStars(highlight.Stars)}";
        GetNode<Label>("Root/Body/SidePanel/CardTrend").Text = $"Trend: {FormatTrend(highlight.Trend)}";
        GetNode<Label>("Root/Body/SidePanel/CardBuild").Text = $"Build: {highlight.Build}";
        GetNode<Label>("Root/Body/SidePanel/CardNotes").Text = $"Quick Notes\n- {string.Join("\n- ", highlight.Tags)}";
        GetNode<Label>("Root/Body/SidePanel/CardOffers").Text = $"Offers ({highlight.Offers.Length})\n- {string.Join("\n- ", highlight.Offers)}";
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event.IsActionPressed("ui_cancel"))
        {
            EmitSignal(SignalName.BackPressed);
        }
    }

    private static Control BuildRow(RecruitingRankingEntry entry)
    {
        var row = new HBoxContainer();
        row.AddChild(MakeCell(entry.Rank.ToString(), 40));
        row.AddChild(MakeCell(entry.PlayerName, 0, true));
        row.AddChild(MakeCell(entry.Position, 40));
        row.AddChild(MakeCell(FormatHeight(entry.HeightInches), 60));
        row.AddChild(MakeCell(entry.WeightLbs.ToString(), 50));
        row.AddChild(MakeCell(entry.Program, 240));
        row.AddChild(MakeCell(entry.Commitment, 120));
        return row;
    }

    private static Label MakeCell(string text, float width, bool expand = false)
    {
        return new Label
        {
            Text = text,
            CustomMinimumSize = width > 0 ? new Vector2(width, 0) : Vector2.Zero,
            SizeFlagsHorizontal = expand ? Control.SizeFlags.ExpandFill : 0
        };
    }

    private static string FormatHeight(int inches)
    {
        var feet = inches / 12;
        var rem = inches % 12;
        return $"{feet}'{rem}\"";
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
