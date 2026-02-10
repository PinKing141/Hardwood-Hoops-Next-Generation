using Godot;
using HardwoodHoops.Core.App.Services;
using System;

namespace HardwoodHoops;

public partial class CareerHub : Control
{
    [Signal] public delegate void StartFeaturedGamePressedEventHandler();
    [Signal] public delegate void BackPressedEventHandler();

    private ItemList _boxScores = null!;
    private Label _detailText = null!;
    private Label _status = null!;
    private Button _playButton = null!;

    public override void _Ready()
    {
        _boxScores = GetNode<ItemList>("Root/Layout/Body/BoxScores");
        _detailText = GetNode<Label>("Root/Layout/Body/Detail/DetailContent/DetailText");
        _status = GetNode<Label>("Root/Layout/Status");
        _playButton = GetNode<Button>("Root/Layout/Actions/PlayButton");

        _playButton.Pressed += () => EmitSignal(SignalName.StartFeaturedGamePressed);
        GetNode<Button>("Root/Layout/Actions/BackButton").Pressed += () => EmitSignal(SignalName.BackPressed);
        _boxScores.ItemSelected += OnBoxScoreSelected;

        Refresh();
    }

    private void Refresh()
    {
        var remaining = FeaturedGameTracker.TotalFeaturedGames - FeaturedGameTracker.FeaturedGamesPlayed;
        _status.Text = $"Featured games remaining: {Math.Max(remaining, 0)}";
        _playButton.Disabled = !FeaturedGameTracker.HasUpcomingFeatured;

        _boxScores.Clear();
        var games = BoxScoreHistory.Games;
        if (games.Count == 0)
        {
            _detailText.Text = "No games played yet.";
            return;
        }

        for (var i = games.Count - 1; i >= 0; i--)
        {
            var game = games[i];
            var date = game.PlayedOn.ToString("MMM dd");
            var line = $"{date} vs {game.Opponent}  {game.HomeScore}-{game.AwayScore}";
            _boxScores.AddItem(line);
        }

        _boxScores.Select(0);
        OnBoxScoreSelected(0);
    }

    private void OnBoxScoreSelected(long index)
    {
        var games = BoxScoreHistory.Games;
        if (games.Count == 0)
        {
            _detailText.Text = "No games played yet.";
            return;
        }

        var reverseIndex = games.Count - 1 - (int)index;
        if (reverseIndex < 0 || reverseIndex >= games.Count)
        {
            return;
        }

        var game = games[reverseIndex];
        var featured = game.IsFeatured ? "Featured" : "Background";
        _detailText.Text = $"{game.PlayedOn:MMMM dd, yyyy}\nOpponent: {game.Opponent}\nScore: {game.HomeScore}-{game.AwayScore}\nType: {featured}\nLine: {game.PlayerLine}";
    }
}
