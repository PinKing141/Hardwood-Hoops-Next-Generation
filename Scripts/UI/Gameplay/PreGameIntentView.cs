using Godot;

namespace HardwoodHoops;

public partial class PreGameIntentView : Control
{
    [Signal] public delegate void BackPressedEventHandler();
    [Signal] public delegate void ConfirmPressedEventHandler(string usage, string shotBias, string defenseFocus, string minutes);

    private OptionButton _usageOption = null!;
    private OptionButton _shotBiasOption = null!;
    private OptionButton _defenseOption = null!;
    private OptionButton _minutesOption = null!;
    private Label _summaryLabel = null!;

    public override void _Ready()
    {
        _usageOption = GetNode<OptionButton>("Root/Fields/UsageRow/UsageOption");
        _shotBiasOption = GetNode<OptionButton>("Root/Fields/ShotRow/ShotOption");
        _defenseOption = GetNode<OptionButton>("Root/Fields/DefenseRow/DefenseOption");
        _minutesOption = GetNode<OptionButton>("Root/Fields/MinutesRow/MinutesOption");
        _summaryLabel = GetNode<Label>("Root/Summary/SummaryLabel");

        Populate(_usageOption, new[] { "Aggressive", "Balanced", "Low" }, 1);
        Populate(_shotBiasOption, new[] { "Rim", "Mid", "Three" }, 0);
        Populate(_defenseOption, new[] { "Contain", "Disrupt" }, 0);
        Populate(_minutesOption, new[] { "Light", "Normal", "Heavy" }, 1);

        _usageOption.ItemSelected += _ => UpdateSummary();
        _shotBiasOption.ItemSelected += _ => UpdateSummary();
        _defenseOption.ItemSelected += _ => UpdateSummary();
        _minutesOption.ItemSelected += _ => UpdateSummary();

        GetNode<Button>("Root/Actions/BackButton").Pressed += () => EmitSignal(SignalName.BackPressed);
        GetNode<Button>("Root/Actions/ConfirmButton").Pressed += OnConfirm;

        UpdateSummary();
    }

    private void OnConfirm()
    {
        EmitSignal(
            SignalName.ConfirmPressed,
            _usageOption.GetItemText(_usageOption.Selected),
            _shotBiasOption.GetItemText(_shotBiasOption.Selected),
            _defenseOption.GetItemText(_defenseOption.Selected),
            _minutesOption.GetItemText(_minutesOption.Selected));
    }

    private void UpdateSummary()
    {
        _summaryLabel.Text = $"Usage: {_usageOption.GetItemText(_usageOption.Selected)} | " +
                             $"Shot Bias: {_shotBiasOption.GetItemText(_shotBiasOption.Selected)} | " +
                             $"Defense: {_defenseOption.GetItemText(_defenseOption.Selected)} | " +
                             $"Minutes: {_minutesOption.GetItemText(_minutesOption.Selected)}";
    }

    private static void Populate(OptionButton button, string[] options, int selected)
    {
        button.Clear();
        for (var i = 0; i < options.Length; i++)
        {
            button.AddItem(options[i], i);
        }
        button.Selected = selected;
    }
}
