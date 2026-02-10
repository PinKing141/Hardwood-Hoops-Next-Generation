using Godot;
using HardwoodHoops.Core.App.Services;

namespace HardwoodHoops;

public partial class FeaturedGameCalendarView : Control
{
    [Signal] public delegate void BackPressedEventHandler();

    private readonly FeaturedGameCalendarService _service = new();
    private readonly CareerScheduleService _scheduleService = new();

    public override void _Ready()
    {
        var list = GetNode<VBoxContainer>("Root/List/Rows");
        foreach (var child in list.GetChildren())
        {
            child.QueueFree();
        }

        var calendar = _service.BuildFromSchedule(_scheduleService.BuildDefaultSchedule());
        foreach (var game in calendar.Games)
        {
            list.AddChild(BuildRow(game));
        }
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event.IsActionPressed("ui_cancel"))
        {
            EmitSignal(SignalName.BackPressed);
        }
    }

    private static Control BuildRow(Core.Domain.Career.FeaturedGameEntry game)
    {
        var row = new HBoxContainer();
        row.AddChild(MakeCell($"W{game.Week}", 48));
        row.AddChild(MakeCell(game.Stage.ToString(), 140));
        row.AddChild(MakeCell(game.Opponent, 200, true));
        row.AddChild(MakeCell(game.IsFeatured ? "Featured" : "Background", 120));
        row.AddChild(MakeCell(game.IsTelevised ? "TV" : "-", 60));
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
