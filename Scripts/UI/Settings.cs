using Godot;

namespace HardwoodHoops;

public partial class Settings : Control
{
    [Signal] public delegate void BackPressedEventHandler();

    public override void _Ready()
    {
        GetNode<Button>("Root/Actions/BackButton").Pressed += () => EmitSignal(SignalName.BackPressed);
    }
}
