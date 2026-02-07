using Godot;
using HardwoodHoops.Core;
using HardwoodHoops.Core.App.Services;
using DomainPlayer = HardwoodHoops.Core.Domain.Players.Player;
using DomainPlayerAttributes = HardwoodHoops.Core.Domain.Players.PlayerAttributes;
using DomainPlayerPersonality = HardwoodHoops.Core.Domain.Players.PlayerPersonality;
using DomainPlayerTendencies = HardwoodHoops.Core.Domain.Players.PlayerTendencies;
using System;
using System.Collections.Generic;
using PlayerPosition = HardwoodHoops.Core.Position;
using GodotTimer = Godot.Timer;

namespace HardwoodHoops;

public partial class Main : Control
{
    private readonly Random _rng = new(42);
    private readonly SimulationEngine _simulation = new();
    private readonly EventLog _eventLog = new();
    private readonly ScoutingReport _scoutingReport = new();
    private readonly List<AttributeRow> _attributeRows = new();
    private readonly ScoutingService _scoutingService = new();

    private PlayerProfile _player = null!;
    private PlayerProfile _defender = null!;
    private DomainPlayer _scoutingPlayer = null!;
    private GameClock _clock = null!;
    private int _homeScore;
    private int _awayScore;

    private RichTextLabel _feed = null!;
    private Label _clockLabel = null!;
    private Label _scoreLabel = null!;
    private Label _playerNameLabel = null!;
    private Label _positionLabel = null!;
    private Label _careerLabel = null!;
    private Label _hypeLabel = null!;
    private Label _publicOvrLabel = null!;
    private Label _privateOvrLabel = null!;
    private Label _archetypeLabel = null!;
    private VBoxContainer _attributeGrid = null!;
    private Label _scoutingDetail = null!;
    private Label _shotDietSummary = null!;
    private Label _shotDietDetail = null!;

    public override void _Ready()
    {
        _feed = GetNode<RichTextLabel>("Margin/Tabs/LiveFeed/Feed");
        _clockLabel = GetNode<Label>("Margin/Tabs/LiveFeed/Header/Clock");
        _scoreLabel = GetNode<Label>("Margin/Tabs/LiveFeed/Score");

        _playerNameLabel = GetNode<Label>("Margin/Tabs/LockerRoom/PlayerHeader/NameLabel");
        _positionLabel = GetNode<Label>("Margin/Tabs/LockerRoom/PlayerHeader/PositionLabel");
        _careerLabel = GetNode<Label>("Margin/Tabs/LockerRoom/PlayerHeader/CareerLabel");
        _hypeLabel = GetNode<Label>("Margin/Tabs/LockerRoom/PlayerHeader/HypeLabel");
        _publicOvrLabel = GetNode<Label>("Margin/Tabs/LockerRoom/OvrSection/OvrRow/PublicOvrBox/PublicOvrValue");
        _privateOvrLabel = GetNode<Label>("Margin/Tabs/LockerRoom/OvrSection/OvrRow/PrivateOvrBox/PrivateOvrValue");
        _archetypeLabel = GetNode<Label>("Margin/Tabs/LockerRoom/ArchetypeLabel");
        _attributeGrid = GetNode<VBoxContainer>("Margin/Tabs/LockerRoom/AttributeScroll/AttributeGrid");
        _scoutingDetail = GetNode<Label>("Margin/Tabs/Scouting/ScoutingDetail");
        _shotDietSummary = GetNode<Label>("Margin/Tabs/ShotDiet/ShotDietSummary");
        _shotDietDetail = GetNode<Label>("Margin/Tabs/ShotDiet/ShotDietDetail");

        _player = PlayerProfile.CreateSample("Player One", PlayerPosition.PointGuard, CareerPhase.HighSchool);
        _defender = PlayerProfile.CreateSample("Defender One", PlayerPosition.ShootingGuard, CareerPhase.HighSchool);
        _scoutingPlayer = CreateScoutingPlayer(_player.Name);
        _clock = new GameClock(12 * 60, 4);

        var timer = GetNode<GodotTimer>("PossessionTimer");
        timer.Timeout += OnPossessionTick;

        BuildAttributeGrid();
        UpdateLockerRoom();
        UpdateScoutingPanels();

        AppendFeed("[b]Tip-off![/b] The game is underway.");
        UpdateLabels();
    }

    private void OnPossessionTick()
    {
        if (_clock.IsFinalBuzzer)
        {
            return;
        }

        var gameEvent = _simulation.SimulatePossession(_player, _defender, _rng);
        _eventLog.Add(gameEvent);
        ApplyScore(gameEvent);
        AppendFeed(gameEvent.Description);

        _clock.AdvanceSeconds(24);
        UpdateLabels();
        UpdateLockerRoom();
    }

    private void ApplyScore(GameEvent gameEvent)
    {
        if (gameEvent.Points <= 0)
        {
            return;
        }

        _homeScore += gameEvent.Points;
    }

    private void AppendFeed(string message)
    {
        _feed.AppendText($"{_clock.FormatGameTime()} {message}\n");
        _feed.ScrollToLine(_feed.GetLineCount());
    }

    private void UpdateLabels()
    {
        _clockLabel.Text = _clock.FormatPeriodClock();
        _scoreLabel.Text = $"Home {_homeScore} - {_awayScore} Away";
    }

    private void BuildAttributeGrid()
    {
        foreach (var child in _attributeGrid.GetChildren())
        {
            child.QueueFree();
        }

        _attributeRows.Clear();
        var attributes = new (string Label, Func<PlayerAttributes, StatValue> Selector)[]
        {
            ("Close Shot", a => a.CloseShot),
            ("Driving Layup", a => a.DrivingLayup),
            ("Driving Dunk", a => a.DrivingDunk),
            ("Standing Dunk", a => a.StandingDunk),
            ("Post Control", a => a.PostControl),
            ("Mid-Range Shot", a => a.MidRangeShot),
            ("Three-Point Shot", a => a.ThreePointShot),
            ("Free Throw", a => a.FreeThrow),
            ("Pass Accuracy", a => a.PassAccuracy),
            ("Ball Handle", a => a.BallHandle),
            ("Speed With Ball", a => a.SpeedWithBall),
            ("Interior Defense", a => a.InteriorDefense),
            ("Perimeter Defense", a => a.PerimeterDefense),
            ("Steal", a => a.Steal),
            ("Block", a => a.Block),
            ("Offensive Rebound", a => a.OffensiveRebound),
            ("Defensive Rebound", a => a.DefensiveRebound),
            ("Speed", a => a.Speed),
            ("Acceleration", a => a.Acceleration),
            ("Strength", a => a.Strength),
            ("Vertical", a => a.Vertical),
            ("Stamina", a => a.Stamina),
            ("Hustle", a => a.Hustle),
            ("Pass Perception", a => a.PassPerception),
            ("Offensive Consistency", a => a.OffensiveConsistency),
            ("Defensive Consistency", a => a.DefensiveConsistency),
            ("Intangibles", a => a.Intangibles),
            ("Potential", a => a.Potential),
            ("Offensive IQ", a => a.OffensiveIq),
            ("Defensive IQ", a => a.DefensiveIq)
        };

        foreach (var attribute in attributes)
        {
            var stat = attribute.Selector(_player.Attributes);
            var row = new HBoxContainer
            {
                SizeFlagsHorizontal = Control.SizeFlags.ExpandFill
            };

            var nameLabel = new Label
            {
                Text = attribute.Label,
                SizeFlagsHorizontal = Control.SizeFlags.ExpandFill
            };

            var valueLabel = new Label
            {
                Text = stat.Value.ToString(),
                HorizontalAlignment = HorizontalAlignment.Right,
                CustomMinimumSize = new Vector2(48, 0)
            };

            var progressBar = new ProgressBar
            {
                MinValue = 0,
                MaxValue = 100,
                Value = stat.Progress,
                SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
                CustomMinimumSize = new Vector2(160, 18)
            };

            var capLabel = new Label
            {
                Text = $"Cap {stat.Cap}",
                HorizontalAlignment = HorizontalAlignment.Right,
                CustomMinimumSize = new Vector2(72, 0)
            };

            row.AddChild(nameLabel);
            row.AddChild(valueLabel);
            row.AddChild(progressBar);
            row.AddChild(capLabel);
            _attributeGrid.AddChild(row);

            _attributeRows.Add(new AttributeRow(attribute.Selector, valueLabel, progressBar, capLabel));
        }
    }

    private void UpdateLockerRoom()
    {
        _scoutingReport.UpdateFromEventLog(_eventLog, _player);
        _playerNameLabel.Text = _player.Name;
        _positionLabel.Text = _player.Position.ToString();
        _careerLabel.Text = _player.CareerPhase.ToString();
        _hypeLabel.Text = $"Hype {_scoutingReport.HypePoints}";
        _publicOvrLabel.Text = _scoutingReport.PublicOvr.ToString("F1");
        _privateOvrLabel.Text = _scoutingReport.PrivateOvr.ToString("F1");
        _archetypeLabel.Text = $"Archetype: {DetermineArchetype(_player.Attributes)}";

        foreach (var row in _attributeRows)
        {
            var stat = row.Selector(_player.Attributes);
            row.ValueLabel.Text = stat.Value.ToString();
            row.ProgressBar.Value = stat.Progress;
            row.CapLabel.Text = $"Cap {stat.Cap}";
        }

        UpdateScoutingPanels();
    }

    private void UpdateScoutingPanels()
    {
        var reports = _scoutingService.ScoutingReports(new[] { _scoutingPlayer });
        if (reports.TryGetValue(_scoutingPlayer.PlayerId, out var report))
        {
            var roles = report["role_descriptors"] as List<string> ?? new List<string>();
            _scoutingDetail.Text =
                $"OVR: {report["public_ovr"]} | Build: {report["build_name"]} | Roles: {string.Join(", ", roles)} | Status: {report["status"]}";
        }

        var tendencies = _scoutingPlayer.Tendencies;
        var close = FormatPercent(tendencies.ShotProfile[0]);
        var mid = FormatPercent(tendencies.ShotProfile[1]);
        var three = FormatPercent(tendencies.ShotProfile[2]);
        var layup = FormatPercent(tendencies.RimAggression[0]);
        var dunk = FormatPercent(tendencies.RimAggression[1]);
        var catchShoot = FormatPercent(tendencies.ShotCreation[0]);
        var pullUp = FormatPercent(tendencies.ShotCreation[1]);
        var drive = FormatPercent(tendencies.ShotCreation[2]);

        _shotDietSummary.Text = $"Close {close} | Mid {mid} | Three {three}";
        _shotDietDetail.Text = $"Rim: Layup {layup} / Dunk {dunk} | Creation: Catch {catchShoot} / Pull-Up {pullUp} / Drive {drive}";
    }

    private static string FormatPercent(double value)
    {
        return $"{Math.Round(value * 100)}%";
    }

    private static DomainPlayer CreateScoutingPlayer(string name)
    {
        var attrs = new DomainPlayerAttributes(
            70, 65, 68, 66, 72, 75, 55, 70, 68, 58, 65, 62, 60, 55, 78, 74, 80, 70, 85, 72, 70, 74, 82, 45, 68, 70, 66);
        return new DomainPlayer(
            playerId: "SCOUT-1",
            name: name,
            classYear: "HS FR",
            attributes: attrs,
            tendencies: DomainPlayerTendencies.Default(),
            personality: DomainPlayerPersonality.Default());
    }

    private static string DetermineArchetype(PlayerAttributes attributes)
    {
        var candidates = new List<(string Name, int Score)>
        {
            ("Slasher", attributes.DrivingLayup.Value + attributes.DrivingDunk.Value),
            ("Sharpshooter", attributes.ThreePointShot.Value + attributes.MidRangeShot.Value),
            ("Playmaker", attributes.BallHandle.Value + attributes.PassAccuracy.Value),
            ("Lockdown", attributes.PerimeterDefense.Value + attributes.Steal.Value),
            ("Rim Protector", attributes.InteriorDefense.Value + attributes.Block.Value),
            ("Glass Cleaner", attributes.DefensiveRebound.Value + attributes.OffensiveRebound.Value)
        };

        candidates.Sort((a, b) => b.Score.CompareTo(a.Score));
        return candidates[0].Score >= 120 ? candidates[0].Name : "Balanced";
    }

    private sealed class AttributeRow
    {
        public AttributeRow(Func<PlayerAttributes, StatValue> selector, Label valueLabel, ProgressBar progressBar, Label capLabel)
        {
            Selector = selector;
            ValueLabel = valueLabel;
            ProgressBar = progressBar;
            CapLabel = capLabel;
        }

        public Func<PlayerAttributes, StatValue> Selector { get; }
        public Label ValueLabel { get; }
        public ProgressBar ProgressBar { get; }
        public Label CapLabel { get; }
    }
}
