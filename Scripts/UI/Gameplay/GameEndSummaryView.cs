using Godot;

namespace HardwoodHoops;

public partial class GameEndSummaryView : Control
{
    [Signal] public delegate void BackPressedEventHandler();
    [Signal] public delegate void ContinuePressedEventHandler();

    public override void _Ready()
    {
        GetNode<Button>("Root/Actions/BackButton").Pressed += () => EmitSignal(SignalName.BackPressed);
        GetNode<Button>("Root/Actions/ContinueButton").Pressed += () => EmitSignal(SignalName.ContinuePressed);
    }

    public void SetSummary(string boxScore, string scoutingNotes, string momentumImpact, string recruitingMessages)
    {
        GetNode<Label>("Root/BoxScore/BoxScoreLines").Text = boxScore;
        GetNode<Label>("Root/Scouting/ScoutingLines").Text = scoutingNotes;
        GetNode<Label>("Root/Momentum/MomentumLines").Text = momentumImpact;
        GetNode<Label>("Root/Recruiting/RecruitingLines").Text = recruitingMessages;
    }
}
