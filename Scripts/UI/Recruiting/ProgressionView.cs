using Godot;
using HardwoodHoops.Core.App.Services;
using System.Linq;

namespace HardwoodHoops;

public partial class ProgressionView : Control
{
    [Signal] public delegate void BackPressedEventHandler();

    public override void _Ready()
    {
        var rows = GetNode<VBoxContainer>("Root/List/Rows");
        foreach (var child in rows.GetChildren())
        {
            child.QueueFree();
        }

        if (ProgressionContext.Previous is null || ProgressionContext.Current is null)
        {
            rows.AddChild(new Label { Text = "No progression data yet." });
            return;
        }

        rows.AddChild(new Label { Text = $"{ProgressionContext.Previous.Label} ? {ProgressionContext.Current.Label}" });

        foreach (var key in ProgressionContext.Current.Values.Keys.OrderBy(k => k))
        {
            var prev = ProgressionContext.Previous.Values.GetValueOrDefault(key, 0);
            var cur = ProgressionContext.Current.Values.GetValueOrDefault(key, 0);
            var delta = cur - prev;
            var sign = delta > 0 ? "+" : "";
            rows.AddChild(new Label { Text = $"{key}: {prev} ? {cur} ({sign}{delta})" });
        }
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event.IsActionPressed("ui_cancel"))
        {
            EmitSignal(SignalName.BackPressed);
        }
    }
}
