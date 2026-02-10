using Godot;

namespace HardwoodHoops;

public partial class LoadGame : Control
{
    [Signal] public delegate void BackPressedEventHandler();
    [Signal] public delegate void LoadSlotPressedEventHandler(int slotIndex);

    public override void _Ready()
    {
        GetNode<Button>("Root/Actions/BackButton").Pressed += () => EmitSignal(SignalName.BackPressed);
        GetNode<Button>("Root/Slots/Slot1/Slot1Button").Pressed += () => EmitSignal(SignalName.LoadSlotPressed, 1);
        GetNode<Button>("Root/Slots/Slot2/Slot2Button").Pressed += () => EmitSignal(SignalName.LoadSlotPressed, 2);
        GetNode<Button>("Root/Slots/Slot3/Slot3Button").Pressed += () => EmitSignal(SignalName.LoadSlotPressed, 3);
    }
}
