using Godot;
using HardwoodHoops.Core.App.Services.Recruiting;

namespace HardwoodHoops;

public partial class ClassRankingsView : Control
{
    [Signal] public delegate void BackPressedEventHandler();

    private readonly RecruitingRankingDataService _data = new();

    public override void _Ready()
    {
        var bands = GetNode<VBoxContainer>("Root/List/Bands");
        foreach (var child in bands.GetChildren())
        {
            child.QueueFree();
        }

        AddBand(bands, "TOP 10", 10);
        AddBand(bands, "TOP 25", 25);
        AddBand(bands, "TOP 50", 50);
        AddBand(bands, "TOP 100", 100);
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event.IsActionPressed("ui_cancel"))
        {
            EmitSignal(SignalName.BackPressed);
        }
    }

    private void AddBand(VBoxContainer container, string title, int maxRank)
    {
        container.AddChild(new Label { Text = title });
        foreach (var entry in _data.GetBand(2027, maxRank))
        {
            var line = $"{entry.Rank,2}  {entry.PlayerName,-24} {entry.Position,2}  {FormatHeight(entry.HeightInches),5}  {entry.WeightLbs,3}  {entry.Program,-20} {entry.Commitment}";
            container.AddChild(new Label { Text = line });
        }
    }

    private static string FormatHeight(int inches)
    {
        var feet = inches / 12;
        var rem = inches % 12;
        return $"{feet}'{rem}\"";
    }
}
