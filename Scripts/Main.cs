using Godot;
using HardwoodHoops.Core;
using HardwoodHoops.Core.App.Services;
using HardwoodHoops.Core.App.Services.Recruiting;
using HardwoodHoops.Core.Domain.Career;
using HardwoodHoops.Core.Domain.Recruiting;
using DomainPlayer = HardwoodHoops.Core.Domain.Players.Player;
using DomainPlayerAttributes = HardwoodHoops.Core.Domain.Players.PlayerAttributes;
using DomainPlayerPersonality = HardwoodHoops.Core.Domain.Players.PlayerPersonality;
using DomainPlayerTendencies = HardwoodHoops.Core.Domain.Players.PlayerTendencies;
using System;
using System.Collections.Generic;
using System.Linq;
using PlayerPosition = HardwoodHoops.Core.Position;
using GodotTimer = Godot.Timer;

namespace HardwoodHoops;

public partial class Main : Control
{
    [Signal] public delegate void ExitToMenuEventHandler();
    private readonly Random _rng = new(42);
    private readonly SimulationEngine _simulation = new();
    private readonly EventLog _eventLog = new();
    private readonly ScoutingReport _scoutingReport = new();
    private readonly List<AttributeRow> _attributeRows = new();
    private readonly ScoutingService _scoutingService = new();
    private readonly RecruitingRankingService _recruitingService = new();

    private PlayerProfile _player = null!;
    private PlayerProfile _defender = null!;
    private DomainPlayer _scoutingPlayer = null!;
    private GameClock _clock = null!;
    private int _homeScore;
    private int _awayScore;
    private int _checkpointTicker;
    private int _checkpointIndex;
    private readonly List<RecruitingCheckpointInput> _checkpointSchedule = new();

    private ProspectProfile _prospectProfile = null!;
    private List<string> _buildTags = new();
    private readonly RecruitingService _recruitingInterestService = new(new HardwoodHoops.Core.Simulation.Rng.SeededRng(17));
    private List<RecruitingInterest> _recruitingInterests = new();
    private int _recruitingWeek = 1;
    private AttributeSnapshot? _seasonStartSnapshot;

    private GodotTimer _possessionTimer = null!;
    private bool _preGameReady;
    private bool _gameEnded;
    private PreGameIntentView? _preGameView;
    private GameEndSummaryView? _summaryView;

    private RichTextLabel _feed = null!;
    private Label _clockLabel = null!;
    private Label _scoreLabel = null!;
    private Label _playerNameLabel = null!;
    private Label _positionLabel = null!;
    private Label _careerLabel = null!;
    private Label _hypeLabel = null!;
    private Label _starsLabel = null!;
    private Label _rankLabel = null!;
    private Label _trendLabel = null!;
    private Label _publicOvrLabel = null!;
    private Label _privateOvrLabel = null!;
    private Label _archetypeLabel = null!;
    private VBoxContainer _attributeGrid = null!;
    private Label _scoutingDetail = null!;
    private Label _shotDietSummary = null!;
    private Label _shotDietDetail = null!;

    private string? _initialPlayerName;
    private PlayerPosition _initialPlayerPosition = PlayerPosition.PointGuard;
    private Dictionary<string, int>? _creationAttributes;
    private Dictionary<string, float>? _creationTendencies;
    private int? _creationHeightInches;
    private int? _creationWeightLbs;
    private int? _creationWingspanInches;
    private int _startingPath;

    private static readonly Dictionary<PlayerPosition, Dictionary<string, int>> PositionCaps = new()
    {
        [PlayerPosition.PointGuard] = new Dictionary<string, int>
        {
            ["Layup"] = 95, ["Dunk"] = 92, ["Inside"] = 88,
            ["Mid-Range"] = 95, ["Three-Point"] = 95, ["Free Throw"] = 95,
            ["Ball Control"] = 95, ["Passing"] = 95,
            ["Perimeter Defence"] = 95, ["Interior Defence"] = 88, ["Steal"] = 95, ["Block"] = 80,
            ["Offensive Rebound"] = 75, ["Defensive Rebound"] = 80,
            ["Speed"] = 95, ["Agility"] = 95, ["Vertical"] = 90, ["Strength"] = 80, ["Stamina"] = 95,
            ["Offensive IQ"] = 95, ["Defensive IQ"] = 95, ["Hustle"] = 95
        },
        [PlayerPosition.ShootingGuard] = new Dictionary<string, int>
        {
            ["Layup"] = 95, ["Dunk"] = 95, ["Inside"] = 90,
            ["Mid-Range"] = 95, ["Three-Point"] = 93, ["Free Throw"] = 95,
            ["Ball Control"] = 93, ["Passing"] = 95,
            ["Perimeter Defence"] = 96, ["Interior Defence"] = 92, ["Steal"] = 95, ["Block"] = 88,
            ["Offensive Rebound"] = 80, ["Defensive Rebound"] = 85,
            ["Speed"] = 95, ["Agility"] = 95, ["Vertical"] = 95, ["Strength"] = 88, ["Stamina"] = 95,
            ["Offensive IQ"] = 95, ["Defensive IQ"] = 95, ["Hustle"] = 95
        },
        [PlayerPosition.SmallForward] = new Dictionary<string, int>
        {
            ["Layup"] = 92, ["Dunk"] = 95, ["Inside"] = 95,
            ["Mid-Range"] = 92, ["Three-Point"] = 90, ["Free Throw"] = 90,
            ["Ball Control"] = 88, ["Passing"] = 90,
            ["Perimeter Defence"] = 92, ["Interior Defence"] = 95, ["Steal"] = 90, ["Block"] = 92,
            ["Offensive Rebound"] = 88, ["Defensive Rebound"] = 92,
            ["Speed"] = 90, ["Agility"] = 90, ["Vertical"] = 92, ["Strength"] = 92, ["Stamina"] = 92,
            ["Offensive IQ"] = 92, ["Defensive IQ"] = 92, ["Hustle"] = 95
        },
        [PlayerPosition.PowerForward] = new Dictionary<string, int>
        {
            ["Layup"] = 88, ["Dunk"] = 95, ["Inside"] = 95,
            ["Mid-Range"] = 88, ["Three-Point"] = 85, ["Free Throw"] = 85,
            ["Ball Control"] = 80, ["Passing"] = 85,
            ["Perimeter Defence"] = 88, ["Interior Defence"] = 96, ["Steal"] = 85, ["Block"] = 95,
            ["Offensive Rebound"] = 95, ["Defensive Rebound"] = 96,
            ["Speed"] = 85, ["Agility"] = 85, ["Vertical"] = 90, ["Strength"] = 96, ["Stamina"] = 90,
            ["Offensive IQ"] = 90, ["Defensive IQ"] = 92, ["Hustle"] = 95
        },
        [PlayerPosition.Center] = new Dictionary<string, int>
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

    public void ConfigureNewGame(
        string playerName,
        PlayerPosition playerPosition,
        Dictionary<string, int> attributes,
        Dictionary<string, float> tendencies,
        int heightInches,
        int weightLbs,
        int wingspanInches,
        int startingPath)
    {
        _initialPlayerName = playerName;
        _initialPlayerPosition = playerPosition;
        _creationAttributes = attributes;
        _creationTendencies = tendencies;
        _creationHeightInches = heightInches;
        _creationWeightLbs = weightLbs;
        _creationWingspanInches = wingspanInches;
        _startingPath = startingPath;
    }

    public override void _Ready()
    {
        _feed = GetNode<RichTextLabel>("Margin/Tabs/LiveFeed/Feed");
        _clockLabel = GetNode<Label>("Margin/Tabs/LiveFeed/Header/Clock");
        _scoreLabel = GetNode<Label>("Margin/Tabs/LiveFeed/Score");

        _playerNameLabel = GetNode<Label>("Margin/Tabs/LockerRoom/PlayerHeader/NameLabel");
        _positionLabel = GetNode<Label>("Margin/Tabs/LockerRoom/PlayerHeader/PositionLabel");
        _careerLabel = GetNode<Label>("Margin/Tabs/LockerRoom/PlayerHeader/CareerLabel");
        _hypeLabel = GetNode<Label>("Margin/Tabs/LockerRoom/PlayerHeader/HypeLabel");
        _starsLabel = GetNode<Label>("Margin/Tabs/LockerRoom/PlayerHeader/StarsLabel");
        _rankLabel = GetNode<Label>("Margin/Tabs/LockerRoom/PlayerHeader/RankLabel");
        _trendLabel = GetNode<Label>("Margin/Tabs/LockerRoom/PlayerHeader/TrendLabel");
        _publicOvrLabel = GetNode<Label>("Margin/Tabs/LockerRoom/OvrSection/OvrRow/PublicOvrBox/PublicOvrValue");
        _privateOvrLabel = GetNode<Label>("Margin/Tabs/LockerRoom/OvrSection/OvrRow/PrivateOvrBox/PrivateOvrValue");
        _archetypeLabel = GetNode<Label>("Margin/Tabs/LockerRoom/ArchetypeLabel");
        _attributeGrid = GetNode<VBoxContainer>("Margin/Tabs/LockerRoom/AttributeScroll/AttributeGrid");
        _scoutingDetail = GetNode<Label>("Margin/Tabs/Scouting/ScoutingDetail");
        _shotDietSummary = GetNode<Label>("Margin/Tabs/ShotDiet/ShotDietSummary");
        _shotDietDetail = GetNode<Label>("Margin/Tabs/ShotDiet/ShotDietDetail");

        var playerName = string.IsNullOrWhiteSpace(_initialPlayerName) ? "Player One" : _initialPlayerName;
        _player = CreatePlayerFromCreation(playerName, _initialPlayerPosition);
        _defender = PlayerProfile.CreateSample("Defender One", PlayerPosition.ShootingGuard, CareerPhase.HighSchool);
        _scoutingPlayer = CreateScoutingPlayer(_player.Name);
        _clock = new GameClock(12 * 60, 4);
        _prospectProfile = new ProspectProfile(_player.Name, 2027);
        _seasonStartSnapshot = CaptureSnapshot("HS Junior (Start)");
        BuildCheckpointSchedule();

        _possessionTimer = GetNode<GodotTimer>("PossessionTimer");
        _possessionTimer.Timeout += OnPossessionTick;

        BuildAttributeGrid();
        UpdateLockerRoom();
        UpdateScoutingPanels();

        AppendFeed("[b]Tip-off![/b] The game is underway.");
        UpdateLabels();

        ShowPreGameIntentIfFeatured();
    }

    private void OnPossessionTick()
    {
        if (_gameEnded || !_preGameReady)
        {
            return;
        }

        if (_clock.IsFinalBuzzer)
        {
            ShowGameEndSummary();
            return;
        }

        var gameEvent = _simulation.SimulatePossession(_player, _defender, _rng);
        _eventLog.Add(gameEvent);
        ApplyScore(gameEvent);
        AppendFeed(gameEvent.Description);

        _clock.AdvanceSeconds(24);
        if (_clock.IsFinalBuzzer && !_gameEnded)
        {
            ShowGameEndSummary();
            return;
        }
        MaybeUpdateRecruitingCheckpoint();
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
        _hypeLabel.Text = $"Hype {_prospectProfile.HypePoints}";
        _starsLabel.Text = $"Stars {FormatStars(_prospectProfile.VisibleStars)}";
        _rankLabel.Text = _prospectProfile.NationalRank.HasValue
            ? $"Rank #{_prospectProfile.NationalRank.Value}"
            : "Rank Unranked";
        _trendLabel.Text = $"Trend {FormatTrend(_prospectProfile.Trend)}";
        UpdateRecruitingContext();
        _publicOvrLabel.Text = Math.Round(_scoutingReport.PublicOvr).ToString("F0");
        _privateOvrLabel.Text = Math.Round(_scoutingReport.PrivateOvr).ToString("F0");
        _archetypeLabel.Text = $"Archetype: {DetermineArchetype(_player.Attributes)}";

        foreach (var row in _attributeRows)
        {
            var stat = row.Selector(_player.Attributes);
            row.ValueLabel.Text = stat.Value.ToString();
            row.ProgressBar.Value = stat.Progress;
            row.CapLabel.Text = $"Cap {stat.Cap}";
        }

        UpdateScoutingPanels();
        UpdateProgressionContext();
    }

    private void UpdateScoutingPanels()
    {
        var reports = _scoutingService.ScoutingReports(new[] { _scoutingPlayer });
        if (reports.TryGetValue(_scoutingPlayer.PlayerId, out var report))
        {
            var roles = report["role_descriptors"] as List<string> ?? new List<string>();
            var publicOvr = Convert.ToDouble(report["public_ovr"]);
            var tags = _buildTags.Count == 0 ? "None" : string.Join(", ", _buildTags);
            _scoutingDetail.Text =
                $"OVR: {Math.Round(publicOvr)} | Build: {report["build_name"]} | Roles: {string.Join(", ", roles)} | Tags: {tags} | Status: {report["status"]}";
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

    private void MaybeUpdateRecruitingCheckpoint()
    {
        _checkpointTicker++;
        if (_checkpointTicker % 12 != 0)
        {
            return;
        }

        if (_checkpointIndex >= _checkpointSchedule.Count)
        {
            _prospectProfile.ApplyInactivityDecay();
            return;
        }

        var performance = EvaluatePerformanceDelta(12);
        var baseInput = _checkpointSchedule[_checkpointIndex];
        var input = new RecruitingCheckpointInput(
            baseInput.Stage,
            baseInput.Importance,
            baseInput.ScoutPresence,
            performance,
            baseInput.OpponentQuality,
            baseInput.IsRankingUpdate,
            baseInput.IsStarUpdate,
            baseInput.HighVisibility);

        _recruitingService.ApplyCheckpoint(_prospectProfile, input);
        if (!string.IsNullOrWhiteSpace(_prospectProfile.LastUpdateMessage))
        {
            AppendFeed($"[i]{_prospectProfile.LastUpdateMessage}[/i]");
        }
        _checkpointIndex++;
    }

    private PerformanceDelta EvaluatePerformanceDelta(int windowSize)
    {
        var events = _eventLog.Events;
        var start = Math.Max(0, events.Count - windowSize);
        var points = 0;
        var turnovers = 0;
        var highlights = 0;

        for (var i = start; i < events.Count; i++)
        {
            var entry = events[i];
            if (entry.PrimaryPlayer != _player.Name)
            {
                continue;
            }

            points += entry.Points;
            if (entry.EventType == GameEventType.Turnover)
            {
                turnovers++;
            }
            if (entry.EventType == GameEventType.ShotMade)
            {
                highlights++;
            }
        }

        var performance = PerformanceDelta.Neutral;
        if (points >= 10 && turnovers <= 1)
        {
            performance = PerformanceDelta.MajorPositive;
        }
        else if (points >= 6)
        {
            performance = PerformanceDelta.Positive;
        }
        else if (turnovers >= 3)
        {
            performance = PerformanceDelta.MajorNegative;
        }
        else if (points <= 2)
        {
            performance = PerformanceDelta.Negative;
        }

        if (highlights >= 3 && performance == PerformanceDelta.Positive)
        {
            performance = PerformanceDelta.MajorPositive;
        }

        return performance;
    }

    private static string FormatStars(int stars)
    {
        return new string('★', stars).PadRight(5, '☆');
    }

    private static string FormatTrend(RecruitTrend trend)
    {
        return trend switch
        {
            RecruitTrend.Rising => "▲ Rising",
            RecruitTrend.Falling => "▼ Falling",
            _ => "— Stable"
        };
    }

    private void UpdateRecruitingContext()
    {
        UpdateRecruitingPipeline();
        var (shotClose, shotMid, shotThree) = GetShotProfile();
        var (creationCatch, creationPull, creationDrive) = GetCreationSplit();
        var (rimLayup, rimDunk) = GetRimAttack();
        var entry = new RecruitingRankingEntry(
            _prospectProfile.NationalRank ?? 101,
            _player.Name,
            _player.Position.ToString(),
            _creationHeightInches ?? 75,
            _creationWeightLbs ?? 200,
            "Your High School",
            "Uncomm",
            _prospectProfile.VisibleStars,
            _prospectProfile.Trend,
            DetermineArchetype(_player.Attributes),
            _buildTags.ToArray(),
            Array.Empty<string>(),
            2027,
            shotClose,
            shotMid,
            shotThree,
            creationCatch,
            creationPull,
            creationDrive,
            rimLayup,
            rimDunk);

        RecruitingRankingContext.UpdateCurrent(entry);
        RecruitingOfferContext.UpdateInterests(_recruitingInterests);
        RecruitingMessageContext.UpdateMessages(BuildRecruitingMessages());
    }

    private void UpdateRecruitingPipeline()
    {
        if (_recruitingInterests.Count == 0)
        {
            _recruitingInterests = BuildRecruitingInterests();
        }

        var updated = new List<RecruitingInterest>();
        for (var i = 0; i < _recruitingInterests.Count; i++)
        {
            var inter = _recruitingInterests[i];
            var offerNow = inter.Interest >= 0.6 || (_prospectProfile.VisibleStars >= 4 && inter.Interest >= 0.55);
            var visitNow = _prospectProfile.Trend == RecruitTrend.Rising && inter.Visits < 2;
            updated.Add(_recruitingInterestService.TickInterest(inter, offerNow, visitNow, week: _recruitingWeek, recruitRegion: "East", teamRegion: "East"));
        }

        _recruitingInterests = _recruitingInterestService.DecayInterest(updated);
        ApplyCommitments();
        _recruitingWeek++;
    }

    private List<RecruitingInterest> BuildRecruitingInterests()
    {
        var list = new List<RecruitingInterest>();
        var classRank = _prospectProfile.NationalRank ?? 150;
        var schools = new[]
        {
            "Florida", "Oregon", "Auburn", "Michigan St", "Texas A&M",
            "Duke", "Kansas", "Kentucky"
        };

        for (var i = 0; i < schools.Length; i++)
        {
            var fit = 0.55 + (i % 3) * 0.05;
            var interest = _recruitingInterestService.EvaluateProspect(_player.Name, schools[i], fit, classRank, "East");
            list.Add(interest);
        }

        return list;
    }

    private IReadOnlyList<string> BuildRecruitingMessages()
    {
        var messages = new List<string>();
        if (!string.IsNullOrWhiteSpace(_prospectProfile.LastUpdateMessage))
        {
            messages.Add(_prospectProfile.LastUpdateMessage);
        }

        foreach (var offer in _recruitingInterests)
        {
            if (offer.OfferMade)
            {
                messages.Add($"{offer.TeamId} staff extended a committable offer.");
            }
            else if (offer.Interest >= 0.6)
            {
                messages.Add($"{offer.TeamId} moved you to their soft offer tier.");
            }
        }

        if (messages.Count == 0)
        {
            messages.Add("No new recruiting updates this week.");
        }

        return messages;
    }

    private void ApplyCommitments()
    {
        var signingOpen = _recruitingWeek is >= 3 and <= 4 || _recruitingWeek >= 8;
        foreach (var interest in _recruitingInterests)
        {
            if (interest.Committed)
            {
                continue;
            }

            var decision = _recruitingInterestService.CommitIfReady(interest, signingOpen);
            if (decision is not null)
            {
                interest.Committed = true;
            }
        }
    }

    private (float close, float mid, float three) GetShotProfile()
    {
        if (_creationTendencies is null)
        {
            return (0.34f, 0.33f, 0.33f);
        }

        var close = GetTendency("shot_close", 0.34f);
        var mid = GetTendency("shot_mid", 0.33f);
        var three = GetTendency("shot_three", 0.33f);
        return NormalizeTriplet(close, mid, three);
    }

    private (float catchShoot, float pullUp, float drive) GetCreationSplit()
    {
        if (_creationTendencies is null)
        {
            return (0.34f, 0.33f, 0.33f);
        }

        var catchShoot = GetTendency("creation_catch", 0.34f);
        var pullUp = GetTendency("creation_pull", 0.33f);
        var drive = GetTendency("creation_drive", 0.33f);
        return NormalizeTriplet(catchShoot, pullUp, drive);
    }

    private (float layup, float dunk) GetRimAttack()
    {
        var layup = GetAttribute("Layup", 60);
        var dunk = GetAttribute("Dunk", 40);
        var total = Math.Max(1f, layup + dunk);
        return (layup / total, dunk / total);
    }

    private float GetTendency(string key, float fallback)
    {
        return _creationTendencies != null && _creationTendencies.TryGetValue(key, out var value) ? value : fallback;
    }

    private float GetAttribute(string key, float fallback)
    {
        return _creationAttributes != null && _creationAttributes.TryGetValue(key, out var value) ? value : fallback;
    }

    private static (float a, float b, float c) NormalizeTriplet(float a, float b, float c)
    {
        var total = Math.Max(0.0001f, a + b + c);
        return (a / total, b / total, c / total);
    }

    private List<RecruitingInterest> BuildOfferInterests(int stars)
    {
        var list = new List<RecruitingInterest>();
        var schools = stars switch
        {
            >= 5 => new[] { "Duke", "Kentucky", "Kansas", "UConn", "Arizona" },
            4 => new[] { "Florida", "Oregon", "Auburn", "Michigan St", "Texas A&M" },
            _ => new[] { "VCU", "Memphis", "Dayton", "St. John's", "Seton Hall" }
        };

        for (var i = 0; i < schools.Length; i++)
        {
            var baseInterest = stars switch
            {
                >= 5 => 0.75 - i * 0.05,
                4 => 0.6 - i * 0.04,
                _ => 0.5 - i * 0.03
            };

            var interest = Math.Max(0.35, baseInterest);
            var entry = new RecruitingInterest(_player.Name, schools[i], interest, 0.7)
            {
                OfferMade = i < (stars >= 5 ? 3 : stars == 4 ? 2 : 1),
                Visits = i < 2 ? 1 : 0
            };
            list.Add(entry);
        }

        return list;
    }

    private void ShowPreGameIntentIfFeatured()
    {
        if (_preGameReady)
        {
            return;
        }

        var isFeatured = _checkpointIndex < _checkpointSchedule.Count;
        if (!isFeatured)
        {
            _preGameReady = true;
            return;
        }

        _possessionTimer.Stop();
        var scene = ResourceLoader.Load<PackedScene>("res://Scenes/Gameplay/PreGameIntent.tscn");
        _preGameView = scene.Instantiate<PreGameIntentView>();
        _preGameView.ConfirmPressed += OnPreGameConfirmed;
        _preGameView.BackPressed += OnPreGameCancelled;
        AddChild(_preGameView);
    }

    private void OnPreGameConfirmed(string usage, string shotBias, string defenseFocus, string minutes)
    {
        AppendFeed($"[i]Intent locked: {usage} usage, {shotBias} bias, {defenseFocus} defense, {minutes} minutes.[/i]");
        _preGameReady = true;
        if (_preGameView is not null)
        {
            _preGameView.QueueFree();
            _preGameView = null;
        }
        _possessionTimer.Start();
    }

    private void OnPreGameCancelled()
    {
        _preGameReady = false;
        if (_preGameView is not null)
        {
            _preGameView.QueueFree();
            _preGameView = null;
        }
        _possessionTimer.Stop();
        EmitSignal(SignalName.ExitToMenu);
    }

    private void ShowGameEndSummary()
    {
        if (_gameEnded)
        {
            return;
        }

        _gameEnded = true;
        _possessionTimer.Stop();

        var (points, turnovers, highlights) = GetPlayerLine();
        var boxScore = $"PTS {points} | REB 0 | AST 0 | STL {highlights} | BLK 0 | TOV {turnovers}";
        var scoutingNotes = highlights >= 3
            ? "- Efficient downhill pressure\n- Stayed active off-ball"
            : "- Inconsistent shot quality\n- Needs stronger decisions";
        var momentum = $"Trend: {FormatTrend(_prospectProfile.Trend)} | Exposure {(_prospectProfile.HypePoints / 2)}";
        var recruiting = _prospectProfile.LastUpdateMessage is not null
            ? $"- {_prospectProfile.LastUpdateMessage}"
            : "- No major recruiting updates.";

        var scene = ResourceLoader.Load<PackedScene>("res://Scenes/Gameplay/GameEndSummary.tscn");
        _summaryView = scene.Instantiate<GameEndSummaryView>();
        _summaryView.SetSummary(boxScore, scoutingNotes, momentum, recruiting);
        _summaryView.BackPressed += CloseSummary;
        _summaryView.ContinuePressed += CloseSummary;
        AddChild(_summaryView);
    }

    private (int points, int turnovers, int highlights) GetPlayerLine()
    {
        var points = 0;
        var turnovers = 0;
        var highlights = 0;
        foreach (var entry in _eventLog.Events)
        {
            if (entry.PrimaryPlayer != _player.Name)
            {
                continue;
            }

            points += entry.Points;
            if (entry.EventType == GameEventType.Turnover)
            {
                turnovers++;
            }
            if (entry.EventType == GameEventType.ShotMade)
            {
                highlights++;
            }
        }

        return (points, turnovers, highlights);
    }

    private void CloseSummary()
    {
        if (_summaryView is not null)
        {
            _summaryView.QueueFree();
            _summaryView = null;
        }
    }

    private void UpdateProgressionContext()
    {
        if (_seasonStartSnapshot is null)
        {
            return;
        }

        var current = CaptureSnapshot("HS Senior (Current)");
        ProgressionContext.Update(_seasonStartSnapshot, current);
    }

    private AttributeSnapshot CaptureSnapshot(string label)
    {
        var values = new Dictionary<string, int>
        {
            ["Close Shot"] = _player.Attributes.CloseShot.Value,
            ["Driving Layup"] = _player.Attributes.DrivingLayup.Value,
            ["Driving Dunk"] = _player.Attributes.DrivingDunk.Value,
            ["Mid-Range Shot"] = _player.Attributes.MidRangeShot.Value,
            ["Three-Point Shot"] = _player.Attributes.ThreePointShot.Value,
            ["Free Throw"] = _player.Attributes.FreeThrow.Value,
            ["Pass Accuracy"] = _player.Attributes.PassAccuracy.Value,
            ["Ball Handle"] = _player.Attributes.BallHandle.Value,
            ["Perimeter Defense"] = _player.Attributes.PerimeterDefense.Value,
            ["Interior Defense"] = _player.Attributes.InteriorDefense.Value,
            ["Steal"] = _player.Attributes.Steal.Value,
            ["Block"] = _player.Attributes.Block.Value,
            ["Offensive Rebound"] = _player.Attributes.OffensiveRebound.Value,
            ["Defensive Rebound"] = _player.Attributes.DefensiveRebound.Value,
            ["Speed"] = _player.Attributes.Speed.Value,
            ["Acceleration"] = _player.Attributes.Acceleration.Value,
            ["Strength"] = _player.Attributes.Strength.Value,
            ["Vertical"] = _player.Attributes.Vertical.Value,
            ["Stamina"] = _player.Attributes.Stamina.Value,
            ["Hustle"] = _player.Attributes.Hustle.Value,
            ["Offensive IQ"] = _player.Attributes.OffensiveIq.Value,
            ["Defensive IQ"] = _player.Attributes.DefensiveIq.Value
        };

        return new AttributeSnapshot(label, values);
    }

    private void BuildCheckpointSchedule()
    {
        _checkpointSchedule.Clear();
        var schedule = new CareerScheduleService().BuildDefaultSchedule();
        foreach (var checkpoint in schedule)
        {
            var stage = checkpoint.Stage switch
            {
                CareerStage.JuniorHighSchool => RecruitingStage.JuniorHighSchool,
                CareerStage.AauCircuit => RecruitingStage.AauCircuit,
                _ => RecruitingStage.SeniorHighSchool
            };

            _checkpointSchedule.Add(new RecruitingCheckpointInput(
                stage,
                checkpoint.Importance,
                checkpoint.ScoutPresence,
                PerformanceDelta.Neutral,
                opponentQuality: checkpoint.HighVisibility ? 4 : 3,
                isRankingUpdate: checkpoint.IsRankingUpdate,
                isStarUpdate: checkpoint.IsStarUpdate,
                highVisibility: checkpoint.HighVisibility));
        }
    }

    private PlayerProfile CreatePlayerFromCreation(string name, PlayerPosition position)
    {
        var phase = CareerPhase.HighSchool;
        if (_creationAttributes is null || _creationTendencies is null)
        {
            _buildTags = new List<string>();
            return PlayerProfile.CreateSample(name, position, phase);
        }

        var defaults = AttributeFactory.CreateDefaults(position, phase);
        var attributes = BuildAttributesFromCreation(
            defaults,
            _creationAttributes,
            position,
            _startingPath,
            _creationHeightInches,
            _creationWeightLbs,
            _creationWingspanInches);
        var tendencies = BuildTendenciesFromCreation(_creationTendencies);
        _buildTags = ComputeBuildTags(_creationAttributes, _creationTendencies);

        return new PlayerProfile(
            name,
            position,
            phase,
            attributes,
            GrowthProfileFactory.CreateDefault(phase),
            tendencies);
    }

    private static PlayerAttributes BuildAttributesFromCreation(
        PlayerAttributeDefaults defaults,
        Dictionary<string, int> values,
        PlayerPosition position,
        int startingPath,
        int? heightInches,
        int? weightLbs,
        int? wingspanInches)
    {
        int Get(string key, int fallback)
        {
            return values.TryGetValue(key, out var value) ? value : fallback;
        }

        var positionCaps = PositionCaps.TryGetValue(position, out var caps)
            ? caps
            : new Dictionary<string, int>();

        int CapFor(string key, int fallbackCap)
        {
            return positionCaps.TryGetValue(key, out var cap) ? cap : fallbackCap;
        }

        var cap = 99;
        var (potentialBonus, hustleBonus, intangibleBonus) = startingPath switch
        {
            0 => (0, 0, 0),   // Blue Chip: more points, less upside
            2 => (8, 4, 4),   // Underdog: fewer points, higher upside
            _ => (4, 2, 2)    // Starter: balanced
        };
        var iqCap = Math.Min(CapFor("Offensive IQ", cap), CapFor("Defensive IQ", cap));
        var custom = new PlayerAttributeDefaults
        {
            Cap = cap,
            CloseShot = Clamp(Get("Inside", defaults.CloseShot), 25, CapFor("Inside", cap)),
            DrivingLayup = Clamp(Get("Layup", defaults.DrivingLayup), 25, CapFor("Layup", cap)),
            DrivingDunk = Clamp(Get("Dunk", defaults.DrivingDunk), 25, CapFor("Dunk", cap)),
            StandingDunk = Clamp(Get("Dunk", defaults.StandingDunk), 25, CapFor("Dunk", cap)),
            PostControl = Clamp(Get("Inside", defaults.PostControl), 25, CapFor("Inside", cap)),
            MidRangeShot = Clamp(Get("Mid-Range", defaults.MidRangeShot), 25, CapFor("Mid-Range", cap)),
            ThreePointShot = Clamp(Get("Three-Point", defaults.ThreePointShot), 25, CapFor("Three-Point", cap)),
            FreeThrow = Clamp(Get("Free Throw", defaults.FreeThrow), 25, CapFor("Free Throw", cap)),
            PassAccuracy = Clamp(Get("Passing", defaults.PassAccuracy), 25, CapFor("Passing", cap)),
            BallHandle = Clamp(Get("Ball Control", defaults.BallHandle), 25, CapFor("Ball Control", cap)),
            SpeedWithBall = Clamp(Get("Speed", defaults.SpeedWithBall), 25, CapFor("Speed", cap)),
            InteriorDefense = Clamp(Get("Interior Defence", defaults.InteriorDefense), 25, CapFor("Interior Defence", cap)),
            PerimeterDefense = Clamp(Get("Perimeter Defence", defaults.PerimeterDefense), 25, CapFor("Perimeter Defence", cap)),
            Steal = Clamp(Get("Steal", defaults.Steal), 25, CapFor("Steal", cap)),
            Block = Clamp(Get("Block", defaults.Block), 25, CapFor("Block", cap)),
            OffensiveRebound = Clamp(Get("Offensive Rebound", defaults.OffensiveRebound), 25, CapFor("Offensive Rebound", cap)),
            DefensiveRebound = Clamp(Get("Defensive Rebound", defaults.DefensiveRebound), 25, CapFor("Defensive Rebound", cap)),
            Speed = Clamp(Get("Speed", defaults.Speed), 25, CapFor("Speed", cap)),
            Acceleration = Clamp(Get("Agility", defaults.Acceleration), 25, CapFor("Agility", cap)),
            Strength = Clamp(Get("Strength", defaults.Strength), 25, CapFor("Strength", cap)),
            Vertical = Clamp(Get("Vertical", defaults.Vertical), 25, CapFor("Vertical", cap)),
            Stamina = Clamp(Get("Stamina", defaults.Stamina), 25, CapFor("Stamina", cap)),
            Hustle = Clamp(Get("Hustle", defaults.Hustle) + hustleBonus, 25, CapFor("Hustle", cap)),
            PassPerception = Clamp(Get("Passing", defaults.PassPerception), 25, CapFor("Passing", cap)),
            OffensiveConsistency = Clamp(Get("Offensive IQ", defaults.OffensiveConsistency), 25, CapFor("Offensive IQ", cap)),
            DefensiveConsistency = Clamp(Get("Defensive IQ", defaults.DefensiveConsistency), 25, CapFor("Defensive IQ", cap)),
            Intangibles = Clamp(
                ((Get("Offensive IQ", defaults.Intangibles) + Get("Defensive IQ", defaults.Intangibles)) / 2) + intangibleBonus,
                25,
                iqCap),
            Potential = Clamp(defaults.Potential + potentialBonus, 25, cap),
            OffensiveIq = Clamp(Get("Offensive IQ", defaults.OffensiveIq), 25, CapFor("Offensive IQ", cap)),
            DefensiveIq = Clamp(Get("Defensive IQ", defaults.DefensiveIq), 25, CapFor("Defensive IQ", cap))
        };

        if (heightInches.HasValue && weightLbs.HasValue && wingspanInches.HasValue)
        {
            custom = ApplyPhysicalModifiers(
                custom,
                positionCaps,
                heightInches.Value,
                weightLbs.Value,
                wingspanInches.Value);
        }

        return new PlayerAttributes(custom);
    }

    private static Tendencies BuildTendenciesFromCreation(Dictionary<string, float> values)
    {
        float Get(string key, float fallback)
        {
            return values.TryGetValue(key, out var value) ? value : fallback;
        }

        var close = Get("shot_close", 0.34f);
        var mid = Get("shot_mid", 0.33f);
        var three = Get("shot_three", 0.33f);
        var catchShoot = Get("creation_catch", 0.34f);
        var pullUp = Get("creation_pull", 0.33f);
        var drive = Get("creation_drive", 0.33f);

        var driveBias = (close + drive) * 0.5f;
        var shootBias = (mid + three + catchShoot + pullUp) * 0.25f;
        var passBias = MathF.Max(0.05f, 1f - (driveBias + shootBias));
        var total = driveBias + shootBias + passBias;

        return new Tendencies
        {
            Drive = driveBias / total,
            Shoot = shootBias / total,
            Pass = passBias / total
        };
    }

    private static int Clamp(int value, int min, int max)
    {
        return Math.Clamp(value, min, max);
    }

    private static List<string> ComputeBuildTags(
        Dictionary<string, int> attributes,
        Dictionary<string, float> tendencies)
    {
        var tags = new List<string>();

        int GetAttr(string key, int fallback = 50)
        {
            return attributes.TryGetValue(key, out var value) ? value : fallback;
        }

        float GetTen(string key, float fallback = 0.33f)
        {
            return tendencies.TryGetValue(key, out var value) ? value : fallback;
        }

        var layup = GetAttr("Layup");
        var dunk = GetAttr("Dunk");
        var mid = GetAttr("Mid-Range");
        var three = GetAttr("Three-Point");
        var passing = GetAttr("Passing");
        var handle = GetAttr("Ball Control");
        var perimeter = GetAttr("Perimeter Defence");
        var interior = GetAttr("Interior Defence");
        var steal = GetAttr("Steal");
        var block = GetAttr("Block");
        var offReb = GetAttr("Offensive Rebound");
        var defReb = GetAttr("Defensive Rebound");

        var shotThree = GetTen("shot_three");
        var creationDrive = GetTen("creation_drive");
        var creationPull = GetTen("creation_pull");
        var creationCatch = GetTen("creation_catch");

        if (three >= 80 || shotThree >= 0.38f) tags.Add("Floor Spacer");
        if (layup + dunk >= 165 || creationDrive >= 0.4f) tags.Add("Rim Pressure");
        if (passing + handle >= 165) tags.Add("Playmaker");
        if (perimeter + steal >= 165) tags.Add("Lockdown");
        if (interior + block >= 165) tags.Add("Rim Protector");
        if (offReb + defReb >= 170) tags.Add("Glass Cleaner");
        if (mid + three + handle >= 230 || creationPull >= 0.34f) tags.Add("Shot Creator");
        if (creationCatch >= 0.36f) tags.Add("Catch & Shoot");

        if (tags.Count == 0)
        {
            tags.Add("Balanced");
        }

        return tags;
    }

    private static PlayerAttributeDefaults ApplyPhysicalModifiers(
        PlayerAttributeDefaults baseStats,
        Dictionary<string, int> positionCaps,
        int heightInches,
        int weightLbs,
        int wingspanInches)
    {
        var heightDelta = heightInches - 75; // 6'3 baseline
        var weightDelta = weightLbs - 200;
        var wingspanDelta = wingspanInches - 78; // 6'6 baseline

        // 2K-style lean: taller/heavier reduces speed, boosts strength/inside; wingspan boosts defense/rebound/vertical.
        var speedMod = (int)Math.Round(-0.35f * heightDelta - 0.35f * (weightDelta / 5f));
        var strengthMod = (int)Math.Round(0.25f * heightDelta + 0.45f * (weightDelta / 5f));
        var verticalMod = (int)Math.Round(-0.2f * (weightDelta / 5f) + 0.35f * (wingspanDelta / 2f));
        var interiorMod = (int)Math.Round(0.3f * heightDelta + 0.4f * (wingspanDelta / 2f));
        var blockMod = (int)Math.Round(0.25f * heightDelta + 0.55f * (wingspanDelta / 2f));
        var reboundMod = (int)Math.Round(0.25f * heightDelta + 0.35f * (wingspanDelta / 2f) + 0.2f * (weightDelta / 5f));

        int CapOf(string key, int fallback) => positionCaps.TryGetValue(key, out var cap) ? cap : fallback;

        var maxSpeed = heightInches switch
        {
            <= 74 => 98,
            <= 78 => 93,
            <= 82 => 88,
            <= 85 => 83,
            _ => 78
        };

        var maxAccel = heightInches switch
        {
            <= 74 => 97,
            <= 78 => 92,
            <= 82 => 87,
            <= 85 => 82,
            _ => 77
        };

        var maxVertical = heightInches switch
        {
            <= 74 => 96,
            <= 78 => 92,
            <= 82 => 88,
            <= 85 => 84,
            _ => 80
        };

        var maxStrength = heightInches switch
        {
            >= 84 => 96,
            >= 81 => 92,
            >= 78 => 88,
            _ => 84
        };

        var maxInterior = heightInches switch
        {
            >= 84 => 97,
            >= 81 => 92,
            >= 78 => 88,
            _ => 82
        };

        var maxBlock = heightInches switch
        {
            >= 84 => 96,
            >= 81 => 92,
            >= 78 => 88,
            _ => 82
        };

        var maxRebound = heightInches switch
        {
            >= 84 => 97,
            >= 81 => 93,
            >= 78 => 88,
            _ => 82
        };

        var weightPenalty = (int)Math.Round(weightDelta / 12f);
        var wingspanBonus = (int)Math.Round(wingspanDelta / 2f);

        maxSpeed = Clamp(Math.Min(maxSpeed, CapOf("Speed", baseStats.Cap)) - weightPenalty, 60, baseStats.Cap);
        maxAccel = Clamp(Math.Min(maxAccel, CapOf("Agility", baseStats.Cap)) - weightPenalty, 60, baseStats.Cap);
        maxVertical = Clamp(Math.Min(maxVertical, CapOf("Vertical", baseStats.Cap)) - weightPenalty + wingspanBonus, 60, baseStats.Cap);
        maxStrength = Clamp(Math.Min(maxStrength, CapOf("Strength", baseStats.Cap)) + weightPenalty, 60, baseStats.Cap);
        maxInterior = Clamp(Math.Min(maxInterior, CapOf("Interior Defence", baseStats.Cap)) + wingspanBonus, 60, baseStats.Cap);
        maxBlock = Clamp(Math.Min(maxBlock, CapOf("Block", baseStats.Cap)) + wingspanBonus, 60, baseStats.Cap);
        maxRebound = Clamp(Math.Min(maxRebound, CapOf("Defensive Rebound", baseStats.Cap)) + wingspanBonus, 60, baseStats.Cap);

        int Adjust(int value, int mod, int max) => Clamp(value + mod, 25, Math.Min(baseStats.Cap, max));

        return baseStats with
        {
            Speed = Adjust(baseStats.Speed, speedMod, maxSpeed),
            Acceleration = Adjust(baseStats.Acceleration, speedMod, maxAccel),
            Strength = Adjust(baseStats.Strength, strengthMod, maxStrength),
            Vertical = Adjust(baseStats.Vertical, verticalMod, maxVertical),
            InteriorDefense = Adjust(baseStats.InteriorDefense, interiorMod, maxInterior),
            Block = Adjust(baseStats.Block, blockMod, maxBlock),
            OffensiveRebound = Adjust(baseStats.OffensiveRebound, reboundMod, maxRebound),
            DefensiveRebound = Adjust(baseStats.DefensiveRebound, reboundMod, maxRebound)
        };
    }
}
