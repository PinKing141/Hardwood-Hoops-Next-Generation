using Godot;
using HardwoodHoops.Core.App.Services.Recruiting;

namespace HardwoodHoops;

public partial class RecruitingInboxView : Control
{
    [Signal] public delegate void BackPressedEventHandler();

    public override void _Ready()
    {
        var list = GetNode<VBoxContainer>("Root/List/Rows");
        foreach (var child in list.GetChildren())
        {
            child.QueueFree();
        }

        foreach (var message in RecruitingMessageContext.Messages)
        {
            list.AddChild(new Label { Text = message });
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
