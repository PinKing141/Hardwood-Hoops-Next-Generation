using Godot;
using HardwoodHoops.Core;

namespace HardwoodHoops;

public partial class Main : Control
{
    private readonly Random _rng = new(42);
    private readonly SimulationEngine _simulation = new();
    private readonly EventLog _eventLog = new();

    private PlayerProfile _player = null!;
    private PlayerProfile _defender = null!;
    private GameClock _clock = null!;
    private int _homeScore;
    private int _awayScore;

    private RichTextLabel _feed = null!;
    private Label _clockLabel = null!;
    private Label _scoreLabel = null!;

    public override void _Ready()
    {
        _feed = GetNode<RichTextLabel>("Margin/Root/Feed");
        _clockLabel = GetNode<Label>("Margin/Root/Header/Clock");
        _scoreLabel = GetNode<Label>("Margin/Root/Score");

        _player = PlayerProfile.CreateSample("Player One", Position.PointGuard, CareerPhase.HighSchool);
        _defender = PlayerProfile.CreateSample("Defender One", Position.ShootingGuard, CareerPhase.HighSchool);
        _clock = new GameClock(12 * 60, 4);

        var timer = GetNode<Timer>("PossessionTimer");
        timer.Timeout += OnPossessionTick;

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
}
