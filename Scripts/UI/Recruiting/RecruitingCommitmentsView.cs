using Godot;
using HardwoodHoops.Core.App.Services.Recruiting;

namespace HardwoodHoops;

public partial class RecruitingCommitmentsView : Control
{
    [Signal] public delegate void BackPressedEventHandler();

    private readonly RecruitingCommitmentService _service = new();

    public override void _Ready()
    {
        var list = GetNode<VBoxContainer>("Root/List/Rows");
        foreach (var child in list.GetChildren())
        {
            child.QueueFree();
        }

        var entries = _service.BuildCommitments(RecruitingOfferContext.Interests);
        foreach (var entry in entries)
        {
            list.AddChild(BuildRow(entry));
        }
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event.IsActionPressed("ui_cancel"))
        {
            EmitSignal(SignalName.BackPressed);
        }
    }

    private static Control BuildRow(Core.Domain.Recruiting.RecruitingInterest entry)
    {
        var row = new HBoxContainer();
        row.AddChild(MakeCell(entry.TeamId, 200, true));
        row.AddChild(MakeCell(entry.Committed ? "Committed" : "Uncommitted", 120));
        row.AddChild(MakeCell($"{(int)(entry.Interest * 100)}", 80));
        row.AddChild(MakeCell(entry.Visits.ToString(), 60));
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
}
