using Godot;

namespace HardwoodHoops;

public partial class MainMenu : Control
{
    [Signal] public delegate void StartNewGamePressedEventHandler();
    [Signal] public delegate void LoadGamePressedEventHandler();
    [Signal] public delegate void SettingsPressedEventHandler();
    [Signal] public delegate void RecruitingPressedEventHandler();
    [Signal] public delegate void ExitPressedEventHandler();

    public override void _Ready()
    {
        GetNode<Button>("Center/Options/NewGameButton").Pressed += () => EmitSignal(SignalName.StartNewGamePressed);
        GetNode<Button>("Center/Options/LoadGameButton").Pressed += () => EmitSignal(SignalName.LoadGamePressed);
        GetNode<Button>("Center/Options/SettingsButton").Pressed += () => EmitSignal(SignalName.SettingsPressed);
        GetNode<Button>("Center/Options/RecruitingButton").Pressed += () => EmitSignal(SignalName.RecruitingPressed);
        GetNode<Button>("Center/Options/ExitButton").Pressed += () => EmitSignal(SignalName.ExitPressed);
    }
}
