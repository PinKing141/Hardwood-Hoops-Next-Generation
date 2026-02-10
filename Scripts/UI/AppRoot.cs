using Godot;
using HardwoodHoops.Core;
using HardwoodHoops.Diagnostics;
using System;
using System.Collections.Generic;

namespace HardwoodHoops;

public partial class AppRoot : Control
{
    [Export] public PackedScene MainMenuScene { get; set; } = null!;
    [Export] public PackedScene CharacterCreationScene { get; set; } = null!;
    [Export] public PackedScene LoadGameScene { get; set; } = null!;
    [Export] public PackedScene SettingsScene { get; set; } = null!;
    [Export] public PackedScene CareerHubScene { get; set; } = null!;
    [Export] public PackedScene GameplayScene { get; set; } = null!;
    [Export] public PackedScene RecruitingHubScene { get; set; } = null!;
    [Export] public PackedScene Top100Scene { get; set; } = null!;
    [Export] public PackedScene ClassRankingsScene { get; set; } = null!;
    [Export] public PackedScene ShotDietScene { get; set; } = null!;
    [Export] public PackedScene ScoutingReportScene { get; set; } = null!;
    [Export] public PackedScene FeaturedCalendarScene { get; set; } = null!;
    [Export] public PackedScene RecruitingOffersScene { get; set; } = null!;
    [Export] public PackedScene RecruitingCommitmentsScene { get; set; } = null!;
    [Export] public PackedScene RecruitingInboxScene { get; set; } = null!;
    [Export] public PackedScene PlayerCardScene { get; set; } = null!;
    [Export] public PackedScene ProgressionScene { get; set; } = null!;

    private Control _screenHost = null!;
    private Node? _currentScreen;
    private string? _pendingPlayerName;
    private Position _pendingPlayerPosition;
    private Godot.Collections.Dictionary? _pendingAttributes;
    private Godot.Collections.Dictionary? _pendingTendencies;
    private int _pendingHeightInches;
    private int _pendingWeightLbs;
    private int _pendingWingspanInches;
    private int _pendingStartingPath;

    public override void _Ready()
    {
        _screenHost = GetNode<Control>("ScreenHost");
        RunValidation();
        ShowMainMenu();
    }

    private static void RunValidation()
    {
        var report = ValidationRunner.RunAll();
        if (report.IsOk)
        {
            GD.Print("[Validation] All checks passed.");
            return;
        }

        foreach (var warning in report.Warnings)
        {
            GD.PushWarning($"[Validation] {warning}");
        }

        foreach (var error in report.Errors)
        {
            GD.PushError($"[Validation] {error}");
        }
    }

    private void ShowMainMenu()
    {
        var menu = MainMenuScene.Instantiate<MainMenu>();
        menu.StartNewGamePressed += OnStartNewGame;
        menu.LoadGamePressed += OnLoadGame;
        menu.SettingsPressed += OnSettings;
        menu.RecruitingPressed += OnRecruiting;
        menu.ExitPressed += OnExit;
        SwitchTo(menu);
    }

    private void OnStartNewGame()
    {
        var creator = CharacterCreationScene.Instantiate<CharacterCreation>();
        creator.BackPressed += ShowMainMenu;
        creator.StartGamePressed += StartNewGame;
        SwitchTo(creator);
    }

    private void OnLoadGame()
    {
        var load = LoadGameScene.Instantiate<LoadGame>();
        load.BackPressed += ShowMainMenu;
        SwitchTo(load);
    }

    private void OnSettings()
    {
        var settings = SettingsScene.Instantiate<Settings>();
        settings.BackPressed += ShowMainMenu;
        SwitchTo(settings);
    }

    private void OnRecruiting()
    {
        var hub = RecruitingHubScene.Instantiate<RecruitingHubView>();
        hub.OpenTop100 += OnOpenTop100;
        hub.OpenClassRankings += OnOpenClassRankings;
        hub.OpenShotDiet += OnOpenShotDiet;
        hub.OpenScoutingReport += OnOpenScoutingReport;
        hub.OpenCalendar += OnOpenCalendar;
        hub.OpenOffers += OnOpenOffers;
        hub.OpenCommitments += OnOpenCommitments;
        hub.OpenInbox += OnOpenInbox;
        hub.OpenPlayerCard += OnOpenPlayerCard;
        hub.OpenProgression += OnOpenProgression;
        hub.BackPressed += ShowMainMenu;
        SwitchTo(hub);
    }

    private void OnOpenTop100()
    {
        var view = Top100Scene.Instantiate<NextGenTop100View>();
        view.BackPressed += OnRecruiting;
        SwitchTo(view);
    }

    private void OnOpenClassRankings()
    {
        var view = ClassRankingsScene.Instantiate<ClassRankingsView>();
        view.BackPressed += OnRecruiting;
        SwitchTo(view);
    }

    private void OnOpenShotDiet()
    {
        var view = ShotDietScene.Instantiate<ShotDietView>();
        view.BackPressed += OnRecruiting;
        SwitchTo(view);
    }

    private void OnOpenScoutingReport()
    {
        var view = ScoutingReportScene.Instantiate<ScoutingReportView>();
        view.BackPressed += OnRecruiting;
        SwitchTo(view);
    }

    private void OnOpenCalendar()
    {
        var view = FeaturedCalendarScene.Instantiate<FeaturedGameCalendarView>();
        view.BackPressed += OnRecruiting;
        SwitchTo(view);
    }

    private void OnOpenOffers()
    {
        var view = RecruitingOffersScene.Instantiate<RecruitingOffersView>();
        view.BackPressed += OnRecruiting;
        SwitchTo(view);
    }

    private void OnOpenCommitments()
    {
        var view = RecruitingCommitmentsScene.Instantiate<RecruitingCommitmentsView>();
        view.BackPressed += OnRecruiting;
        SwitchTo(view);
    }

    private void OnOpenInbox()
    {
        var view = RecruitingInboxScene.Instantiate<RecruitingInboxView>();
        view.BackPressed += OnRecruiting;
        SwitchTo(view);
    }

    private void OnOpenPlayerCard()
    {
        var view = PlayerCardScene.Instantiate<PlayerCardView>();
        view.BackPressed += OnRecruiting;
        SwitchTo(view);
    }

    private void OnOpenProgression()
    {
        var view = ProgressionScene.Instantiate<ProgressionView>();
        view.BackPressed += OnRecruiting;
        SwitchTo(view);
    }

    private void StartNewGame(
        string playerName,
        int playerPosition,
        Godot.Collections.Dictionary attributes,
        Godot.Collections.Dictionary tendencies,
        int heightInches,
        int weightLbs,
        int wingspanInches,
        int startingPath)
    {
        _pendingPlayerName = playerName;
        _pendingPlayerPosition = (Position)playerPosition;
        _pendingAttributes = attributes;
        _pendingTendencies = tendencies;
        _pendingHeightInches = heightInches;
        _pendingWeightLbs = weightLbs;
        _pendingWingspanInches = wingspanInches;
        _pendingStartingPath = startingPath;

        BoxScoreHistory.Reset();
        FeaturedGameTracker.Reset();
        ShowCareerHub();
    }

    private void ShowCareerHub()
    {
        var hub = CareerHubScene.Instantiate<CareerHub>();
        hub.StartFeaturedGamePressed += OnStartFeaturedGame;
        hub.BackPressed += ShowMainMenu;
        SwitchTo(hub);
    }

    private void OnStartFeaturedGame()
    {
        if (_pendingPlayerName is null || _pendingAttributes is null || _pendingTendencies is null)
        {
            ShowMainMenu();
            return;
        }

        var game = GameplayScene.Instantiate<Main>();
        game.ExitToMenu += ShowMainMenu;
        game.ExitToHub += ShowCareerHub;
        game.ConfigureNewGame(
            _pendingPlayerName,
            _pendingPlayerPosition,
            ToIntDictionary(_pendingAttributes),
            ToFloatDictionary(_pendingTendencies),
            _pendingHeightInches,
            _pendingWeightLbs,
            _pendingWingspanInches,
            _pendingStartingPath);
        SwitchTo(game);
    }

    private static Dictionary<string, int> ToIntDictionary(Godot.Collections.Dictionary input)
    {
        var output = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        foreach (var key in input.Keys)
        {
            if (key is not string textKey)
            {
                continue;
            }

            if (input[key] is int intValue)
            {
                output[textKey] = intValue;
            }
            else if (input[key] is long longValue)
            {
                output[textKey] = (int)longValue;
            }
            else if (input[key] is double doubleValue)
            {
                output[textKey] = (int)Math.Round(doubleValue);
            }
        }

        return output;
    }

    private static Dictionary<string, float> ToFloatDictionary(Godot.Collections.Dictionary input)
    {
        var output = new Dictionary<string, float>(StringComparer.OrdinalIgnoreCase);
        foreach (var key in input.Keys)
        {
            if (key is not string textKey)
            {
                continue;
            }

            if (input[key] is float floatValue)
            {
                output[textKey] = floatValue;
            }
            else if (input[key] is double doubleValue)
            {
                output[textKey] = (float)doubleValue;
            }
            else if (input[key] is int intValue)
            {
                output[textKey] = intValue / 100f;
            }
        }

        return output;
    }

    private void OnExit()
    {
        GetTree().Quit();
    }

    private void SwitchTo(Node screen)
    {
        if (_currentScreen is not null)
        {
            _currentScreen.QueueFree();
        }

        _currentScreen = screen;
        _screenHost.AddChild(screen);
    }

}
