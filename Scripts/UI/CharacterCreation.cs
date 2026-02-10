using Godot;
using HardwoodHoops.Core;
using System;
using System.Collections.Generic;
using System.Linq;

namespace HardwoodHoops;

public partial class CharacterCreation : Control
{
    [Signal] public delegate void BackPressedEventHandler();
    [Signal] public delegate void StartGamePressedEventHandler(
        string playerName,
        int playerPosition,
        Godot.Collections.Dictionary attributes,
        Godot.Collections.Dictionary tendencies,
        int heightInches,
        int weightLbs,
        int wingspanInches,
        int startingPath);

    private LineEdit _nameInput = null!;
    private OptionButton _positionOption = null!;
    private OptionButton _pathOption = null!;
    private VBoxContainer _attributeGroupsContainer = null!;
    private Label _previewLabel = null!;
    private Label _pointsLabel = null!;
    private Label _routeInfoLabel = null!;
    private Label _bodyLabel = null!;
    private Label _buildNameLabel = null!;
    private Label _rolesLabel = null!;
    private HSlider _heightSlider = null!;
    private Label _heightValue = null!;
    private HSlider _weightSlider = null!;
    private Label _weightValue = null!;
    private HSlider _wingspanSlider = null!;
    private Label _wingspanValue = null!;
    private HSlider _shotClose = null!;
    private Label _shotCloseValue = null!;
    private HSlider _shotMid = null!;
    private Label _shotMidValue = null!;
    private HSlider _shotThree = null!;
    private Label _shotThreeValue = null!;
    private HSlider _creationCatch = null!;
    private Label _creationCatchValue = null!;
    private HSlider _creationPull = null!;
    private Label _creationPullValue = null!;
    private HSlider _creationDrive = null!;
    private Label _creationDriveValue = null!;

    private readonly List<AttributeRow> _attributeRows = new();
    private bool _normalizingTendencies;
    private bool _suppressAttributeChange;

    private const int BudgetBlueChip = 720;
    private const int BudgetStarter = 660;
    private const int BudgetUnderdog = 600;

    private static readonly (string Group, string[] Attributes)[] AttributeGroups =
    {
        ("Finishing", new[] { "Layup", "Dunk", "Inside" }),
        ("Shooting", new[] { "Mid-Range", "Three-Point", "Free Throw" }),
        ("Playmaking", new[] { "Ball Control", "Passing" }),
        ("Defense", new[] { "Perimeter Defence", "Interior Defence", "Steal", "Block" }),
        ("Rebounding", new[] { "Offensive Rebound", "Defensive Rebound" }),
        ("Athleticism", new[] { "Speed", "Agility", "Vertical", "Strength", "Stamina" }),
        ("Mental & IQ", new[] { "Offensive IQ", "Defensive IQ", "Hustle" })
    };

    private static readonly Dictionary<Position, Dictionary<string, int>> BaseCapsByPosition = new()
    {
        [Position.PointGuard] = new Dictionary<string, int>
        {
            ["Layup"] = 95, ["Dunk"] = 92, ["Inside"] = 88,
            ["Mid-Range"] = 95, ["Three-Point"] = 95, ["Free Throw"] = 95,
            ["Ball Control"] = 95, ["Passing"] = 95,
            ["Perimeter Defence"] = 95, ["Interior Defence"] = 88, ["Steal"] = 95, ["Block"] = 80,
            ["Offensive Rebound"] = 75, ["Defensive Rebound"] = 80,
            ["Speed"] = 95, ["Agility"] = 95, ["Vertical"] = 90, ["Strength"] = 80, ["Stamina"] = 95,
            ["Offensive IQ"] = 95, ["Defensive IQ"] = 95, ["Hustle"] = 95
        },
        [Position.ShootingGuard] = new Dictionary<string, int>
        {
            ["Layup"] = 95, ["Dunk"] = 95, ["Inside"] = 90,
            ["Mid-Range"] = 95, ["Three-Point"] = 93, ["Free Throw"] = 95,
            ["Ball Control"] = 93, ["Passing"] = 95,
            ["Perimeter Defence"] = 96, ["Interior Defence"] = 92, ["Steal"] = 95, ["Block"] = 88,
            ["Offensive Rebound"] = 80, ["Defensive Rebound"] = 85,
            ["Speed"] = 95, ["Agility"] = 95, ["Vertical"] = 95, ["Strength"] = 88, ["Stamina"] = 95,
            ["Offensive IQ"] = 95, ["Defensive IQ"] = 95, ["Hustle"] = 95
        },
        [Position.SmallForward] = new Dictionary<string, int>
        {
            ["Layup"] = 92, ["Dunk"] = 95, ["Inside"] = 95,
            ["Mid-Range"] = 92, ["Three-Point"] = 90, ["Free Throw"] = 90,
            ["Ball Control"] = 88, ["Passing"] = 90,
            ["Perimeter Defence"] = 92, ["Interior Defence"] = 95, ["Steal"] = 90, ["Block"] = 92,
            ["Offensive Rebound"] = 88, ["Defensive Rebound"] = 92,
            ["Speed"] = 90, ["Agility"] = 90, ["Vertical"] = 92, ["Strength"] = 92, ["Stamina"] = 92,
            ["Offensive IQ"] = 92, ["Defensive IQ"] = 92, ["Hustle"] = 95
        },
        [Position.PowerForward] = new Dictionary<string, int>
        {
            ["Layup"] = 88, ["Dunk"] = 95, ["Inside"] = 95,
            ["Mid-Range"] = 88, ["Three-Point"] = 85, ["Free Throw"] = 85,
            ["Ball Control"] = 80, ["Passing"] = 85,
            ["Perimeter Defence"] = 88, ["Interior Defence"] = 96, ["Steal"] = 85, ["Block"] = 95,
            ["Offensive Rebound"] = 95, ["Defensive Rebound"] = 96,
            ["Speed"] = 85, ["Agility"] = 85, ["Vertical"] = 90, ["Strength"] = 96, ["Stamina"] = 90,
            ["Offensive IQ"] = 90, ["Defensive IQ"] = 92, ["Hustle"] = 95
        },
        [Position.Center] = new Dictionary<string, int>
        {
            ["Layup"] = 85, ["Dunk"] = 95, ["Inside"] = 95,
            ["Mid-Range"] = 82, ["Three-Point"] = 78, ["Free Throw"] = 80,
            ["Ball Control"] = 72, ["Passing"] = 85,
            ["Perimeter Defence"] = 82, ["Interior Defence"] = 98, ["Steal"] = 80, ["Block"] = 98,
            ["Offensive Rebound"] = 98, ["Defensive Rebound"] = 98,
            ["Speed"] = 78, ["Agility"] = 78, ["Vertical"] = 88, ["Strength"] = 98, ["Stamina"] = 88,
            ["Offensive IQ"] = 88, ["Defensive IQ"] = 92, ["Hustle"] = 95
        }
    };

    public override void _Ready()
    {
        _nameInput = GetNode<LineEdit>("Root/Scroll/Content/Fields/NameRow/NameInput");
        _positionOption = GetNode<OptionButton>("Root/Scroll/Content/Fields/PositionRow/PositionOption");
        _pathOption = GetNode<OptionButton>("Root/Scroll/Content/Fields/PathRow/PathOption");
        _attributeGroupsContainer = GetNode<VBoxContainer>("Root/Scroll/Content/Attributes/AttributeScroll/AttributeGroups");
        _previewLabel = GetNode<Label>("Root/Scroll/Content/Summary/PreviewLabel");
        _pointsLabel = GetNode<Label>("Root/Scroll/Content/Attributes/PointsLabel");
        _routeInfoLabel = GetNode<Label>("Root/Scroll/Content/Attributes/RouteInfoLabel");
        _bodyLabel = GetNode<Label>("Root/Scroll/Content/Summary/BodyLabel");
        _buildNameLabel = GetNode<Label>("Root/Scroll/Content/Summary/BuildNameLabel");
        _rolesLabel = GetNode<Label>("Root/Scroll/Content/Summary/RolesLabel");
        _heightSlider = GetNode<HSlider>("Root/Scroll/Content/Physical/HeightRow/HeightSlider");
        _heightValue = GetNode<Label>("Root/Scroll/Content/Physical/HeightRow/HeightValue");
        _weightSlider = GetNode<HSlider>("Root/Scroll/Content/Physical/WeightRow/WeightSlider");
        _weightValue = GetNode<Label>("Root/Scroll/Content/Physical/WeightRow/WeightValue");
        _wingspanSlider = GetNode<HSlider>("Root/Scroll/Content/Physical/WingspanRow/WingspanSlider");
        _wingspanValue = GetNode<Label>("Root/Scroll/Content/Physical/WingspanRow/WingspanValue");

        _shotClose = GetNode<HSlider>("Root/Scroll/Content/Tendencies/ShotProfileRow/ShotClose");
        _shotCloseValue = GetNode<Label>("Root/Scroll/Content/Tendencies/ShotProfileRow/ShotCloseValue");
        _shotMid = GetNode<HSlider>("Root/Scroll/Content/Tendencies/ShotProfileRow/ShotMid");
        _shotMidValue = GetNode<Label>("Root/Scroll/Content/Tendencies/ShotProfileRow/ShotMidValue");
        _shotThree = GetNode<HSlider>("Root/Scroll/Content/Tendencies/ShotProfileRow/ShotThree");
        _shotThreeValue = GetNode<Label>("Root/Scroll/Content/Tendencies/ShotProfileRow/ShotThreeValue");
        _creationCatch = GetNode<HSlider>("Root/Scroll/Content/Tendencies/CreationRow/CreationCatch");
        _creationCatchValue = GetNode<Label>("Root/Scroll/Content/Tendencies/CreationRow/CreationCatchValue");
        _creationPull = GetNode<HSlider>("Root/Scroll/Content/Tendencies/CreationRow/CreationPull");
        _creationPullValue = GetNode<Label>("Root/Scroll/Content/Tendencies/CreationRow/CreationPullValue");
        _creationDrive = GetNode<HSlider>("Root/Scroll/Content/Tendencies/CreationRow/CreationDrive");
        _creationDriveValue = GetNode<Label>("Root/Scroll/Content/Tendencies/CreationRow/CreationDriveValue");

        _positionOption.Clear();
        foreach (var position in Enum.GetValues<Position>())
        {
            _positionOption.AddItem(position.ToString(), (int)position);
        }
        _positionOption.Selected = 0;
        _positionOption.ItemSelected += _ => ApplyCapsForSelectedPosition();

        _pathOption.Clear();
        _pathOption.AddItem("Blue Chip (Easy)", 0);
        _pathOption.AddItem("Starter (Balanced)", 1);
        _pathOption.AddItem("Underdog (Hard)", 2);
        _pathOption.Selected = 1;
        _pathOption.ItemSelected += _ => UpdatePoints();

        GetNode<Button>("Root/Actions/BackButton").Pressed += () => EmitSignal(SignalName.BackPressed);
        GetNode<Button>("Root/Actions/StartButton").Pressed += OnStartPressed;

        _heightSlider.ValueChanged += _ => UpdatePhysicalLabels();
        _weightSlider.ValueChanged += _ => UpdatePhysicalLabels();
        _wingspanSlider.ValueChanged += _ => UpdatePhysicalLabels();
        _shotClose.ValueChanged += _ => NormalizeShotProfile();
        _shotMid.ValueChanged += _ => NormalizeShotProfile();
        _shotThree.ValueChanged += _ => NormalizeShotProfile();
        _creationCatch.ValueChanged += _ => NormalizeCreation();
        _creationPull.ValueChanged += _ => NormalizeCreation();
        _creationDrive.ValueChanged += _ => NormalizeCreation();

        BuildAttributeGroups();
        ApplyCapsForSelectedPosition();
        UpdatePhysicalLabels();
        NormalizeShotProfile();
        NormalizeCreation();
        UpdatePreview();
        UpdatePoints();
    }

    private void OnStartPressed()
    {
        var name = string.IsNullOrWhiteSpace(_nameInput.Text) ? "New Prospect" : _nameInput.Text.Trim();
        var position = _positionOption.GetItemId(_positionOption.Selected);
        var attributes = new Godot.Collections.Dictionary();
        foreach (var row in _attributeRows)
        {
            attributes[row.Name] = (int)row.Slider.Value;
        }

        var tendencies = new Godot.Collections.Dictionary
        {
            ["shot_close"] = (float)_shotClose.Value / 100f,
            ["shot_mid"] = (float)_shotMid.Value / 100f,
            ["shot_three"] = (float)_shotThree.Value / 100f,
            ["creation_catch"] = (float)_creationCatch.Value / 100f,
            ["creation_pull"] = (float)_creationPull.Value / 100f,
            ["creation_drive"] = (float)_creationDrive.Value / 100f
        };

        EmitSignal(
            SignalName.StartGamePressed,
            name,
            position,
            attributes,
            tendencies,
            (int)_heightSlider.Value,
            (int)_weightSlider.Value,
            (int)_wingspanSlider.Value,
            _pathOption.GetItemId(_pathOption.Selected));
    }

    private void BuildAttributeGroups()
    {
        foreach (var child in _attributeGroupsContainer.GetChildren())
        {
            child.QueueFree();
        }
        _attributeRows.Clear();

        foreach (var (groupName, attributes) in AttributeGroups)
        {
            var groupBox = new VBoxContainer();
            var groupLabel = new Label { Text = groupName };
            groupBox.AddChild(groupLabel);

            foreach (var attribute in attributes)
            {
                var row = new HBoxContainer();
                var nameLabel = new Label
                {
                    Text = attribute,
                    CustomMinimumSize = new Vector2(160, 0)
                };

                var slider = new HSlider
                {
                    MinValue = 25,
                    MaxValue = 99,
                    Step = 1,
                    Value = 36,
                    SizeFlagsHorizontal = Control.SizeFlags.ExpandFill
                };

                var valueLabel = new Label
                {
                    Text = "36",
                    CustomMinimumSize = new Vector2(48, 0)
                };

                var capLabel = new Label
                {
                    Text = "Cap 99",
                    CustomMinimumSize = new Vector2(72, 0)
                };

                slider.ValueChanged += _ => OnAttributeChanged(row);

                row.AddChild(nameLabel);
                row.AddChild(slider);
                row.AddChild(valueLabel);
                row.AddChild(capLabel);
                groupBox.AddChild(row);

                _attributeRows.Add(new AttributeRow(attribute, groupName, slider, valueLabel, capLabel));
            }

            _attributeGroupsContainer.AddChild(groupBox);
        }
    }

    private void ApplyCapsForSelectedPosition()
    {
        var position = (Position)_positionOption.GetItemId(_positionOption.Selected);
        if (!BaseCapsByPosition.TryGetValue(position, out var caps))
        {
            return;
        }

        foreach (var row in _attributeRows)
        {
            var cap = caps.TryGetValue(row.Name, out var value) ? value : 95;
            row.Slider.MaxValue = cap;
            if (row.Slider.Value > cap)
            {
                row.Slider.Value = cap;
            }
            row.CapLabel.Text = $"Cap {cap}";
            row.ValueLabel.Text = ((int)row.Slider.Value).ToString();
            row.PreviousValue = row.Slider.Value;
        }
        UpdatePoints();
        UpdatePreview();
    }

    private void UpdatePhysicalLabels()
    {
        _heightValue.Text = FormatHeight((int)_heightSlider.Value);
        _weightValue.Text = $"{(int)_weightSlider.Value} lb";
        _wingspanValue.Text = FormatHeight((int)_wingspanSlider.Value);
    }

    private void NormalizeShotProfile()
    {
        if (_normalizingTendencies)
        {
            return;
        }

        _normalizingTendencies = true;
        NormalizeTrio(_shotClose, _shotMid, _shotThree, _shotCloseValue, _shotMidValue, _shotThreeValue);
        _normalizingTendencies = false;
    }

    private void NormalizeCreation()
    {
        if (_normalizingTendencies)
        {
            return;
        }

        _normalizingTendencies = true;
        NormalizeTrio(_creationCatch, _creationPull, _creationDrive, _creationCatchValue, _creationPullValue, _creationDriveValue);
        _normalizingTendencies = false;
    }

    private void NormalizeTrio(HSlider a, HSlider b, HSlider c, Label aLabel, Label bLabel, Label cLabel)
    {
        var total = a.Value + b.Value + c.Value;
        if (total <= 0.1)
        {
            a.Value = 34;
            b.Value = 33;
            c.Value = 33;
        }
        else
        {
            a.Value = Math.Round(a.Value * 100.0 / total);
            b.Value = Math.Round(b.Value * 100.0 / total);
            c.Value = 100 - a.Value - b.Value;
        }

        aLabel.Text = $"{(int)a.Value}%";
        bLabel.Text = $"{(int)b.Value}%";
        cLabel.Text = $"{(int)c.Value}%";
    }

    private void UpdatePreview()
    {
        if (_attributeRows.Count == 0)
        {
            _previewLabel.Text = "Average: 0 | Focus: Balanced";
            _bodyLabel.Text = "Body: Balanced Wing";
            _buildNameLabel.Text = "Build: Prospect";
            _rolesLabel.Text = "Roles: -";
            return;
        }

        var average = _attributeRows.Average(r => r.Slider.Value);
        var topGroup = _attributeRows
            .GroupBy(r => r.Group)
            .Select(g => (Group: g.Key, Score: g.Sum(r => r.Slider.Value)))
            .OrderByDescending(g => g.Score)
            .First().Group;

        _previewLabel.Text = $"Average: {Math.Round(average)} | Focus: {topGroup}";

        var wingspanDelta = _wingspanSlider.Value - _heightSlider.Value;
        var bodyLabel = wingspanDelta >= 4 ? "Long-Arm Defender" :
            wingspanDelta <= 1 ? "Compact Scorer" : "Balanced Wing";
        _bodyLabel.Text = $"Body: {bodyLabel}";

        var off = AverageOf("Layup", "Dunk", "Mid-Range", "Three-Point");
        var def = AverageOf("Perimeter Defence", "Interior Defence", "Steal", "Block");
        var play = AverageOf("Ball Control", "Passing");
        var isTwoWay = def >= 80;
        var isThreeLevel = AverageOf("Layup", "Mid-Range", "Three-Point") >= 78;

        var core = off >= 82 && play >= 75 ? "Shot Creator"
            : (AverageOf("Layup", "Dunk") >= 82 ? "Slasher"
                : (play >= 80 ? "Playmaker" : "Scorer"));

        var buildName = $"{(isTwoWay ? "2-Way " : string.Empty)}{(isThreeLevel ? "3-Level " : string.Empty)}{core}".Trim();
        _buildNameLabel.Text = $"Build: {(string.IsNullOrWhiteSpace(buildName) ? "Prospect" : buildName)}";

        var roles = new List<string>();
        if (_shotThree.Value >= 38) roles.Add("Floor Spacer");
        if (_creationDrive.Value >= 40) roles.Add("Rim Pressure");
        if (def >= 80) roles.Add("Defensive Stopper");
        _rolesLabel.Text = roles.Count == 0 ? "Roles: -" : $"Roles: {string.Join(", ", roles)}";
    }

    private static string FormatHeight(int inches)
    {
        var feet = inches / 12;
        var remainder = inches % 12;
        return $"{feet}'{remainder}\"";
    }

    private sealed class AttributeRow
    {
        public AttributeRow(string name, string group, HSlider slider, Label valueLabel, Label capLabel)
        {
            Name = name;
            Group = group;
            Slider = slider;
            ValueLabel = valueLabel;
            CapLabel = capLabel;
            PreviousValue = slider.Value;
        }

        public string Name { get; }
        public string Group { get; }
        public HSlider Slider { get; }
        public Label ValueLabel { get; }
        public Label CapLabel { get; }
        public double PreviousValue { get; set; }
    }

    private void OnAttributeChanged(AttributeRow row)
    {
        if (_suppressAttributeChange)
        {
            return;
        }

        _suppressAttributeChange = true;

        var newValue = row.Slider.Value;
        var proposed = GetBudgetUsed(newValue, row);
        if (proposed > GetBudgetTotal())
        {
            row.Slider.Value = row.PreviousValue;
            row.ValueLabel.Text = ((int)row.PreviousValue).ToString();
            _suppressAttributeChange = false;
            UpdatePoints();
            UpdatePreview();
            return;
        }

        row.ValueLabel.Text = ((int)row.Slider.Value).ToString();
        row.PreviousValue = row.Slider.Value;
        _suppressAttributeChange = false;
        UpdatePoints();
        UpdatePreview();
    }

    private int GetBudgetUsed(double? overrideValue, AttributeRow? overrideRow)
    {
        var total = 0;
        foreach (var row in _attributeRows)
        {
            var value = row == overrideRow && overrideValue.HasValue ? overrideValue.Value : row.Slider.Value;
            total += (int)Math.Round(value);
        }
        return total;
    }

    private void UpdatePoints()
    {
        var used = GetBudgetUsed(null, null);
        var total = GetBudgetTotal();
        var remaining = total - used;
        _pointsLabel.Text = $"Points Remaining: {Math.Max(0, remaining)}";
        _routeInfoLabel.Text = GetRouteInfo();
    }

    private int GetBudgetTotal()
    {
        return _pathOption.GetItemId(_pathOption.Selected) switch
        {
            0 => BudgetBlueChip,
            2 => BudgetUnderdog,
            _ => BudgetStarter
        };
    }

    private string GetRouteInfo()
    {
        return _pathOption.GetItemId(_pathOption.Selected) switch
        {
            0 => "Route: Blue Chip | More points, lower upside.",
            2 => "Route: Underdog | Fewer points, higher upside.",
            _ => "Route: Starter | Balanced budget, balanced upside."
        };
    }

    private double AverageOf(params string[] names)
    {
        var values = _attributeRows
            .Where(r => names.Contains(r.Name))
            .Select(r => r.Slider.Value)
            .ToArray();
        if (values.Length == 0)
        {
            return 0;
        }

        return values.Average();
    }
}
