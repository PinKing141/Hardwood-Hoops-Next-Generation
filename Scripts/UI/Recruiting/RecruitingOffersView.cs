using Godot;
using HardwoodHoops.Core.App.Services.Recruiting;
using HardwoodHoops.Core.Domain.Recruiting;
using System.Linq;

namespace HardwoodHoops;

public partial class RecruitingOffersView : Control
{
    [Signal] public delegate void BackPressedEventHandler();

    private readonly RecruitingOfferService _service = new();

    public override void _Ready()
    {
        var list = GetNode<VBoxContainer>("Root/Body/List/Rows");
        foreach (var child in list.GetChildren())
        {
            child.QueueFree();
        }

        var board = RecruitingOfferContext.Interests.Count > 0
            ? _service.BuildFromInterest(RecruitingOfferContext.Interests)
            : _service.BuildSampleOffers();

        foreach (var offer in board.Offers)
        {
            list.AddChild(BuildRow(offer));
        }

        var best = board.Offers.OrderByDescending(o => o.Interest).FirstOrDefault();
        if (best is not null)
        {
            GetNode<Label>("Root/Body/Detail/DetailSchool").Text = $"School: {best.School}";
            GetNode<Label>("Root/Body/Detail/DetailTier").Text = $"Tier: {best.Tier}";
            GetNode<Label>("Root/Body/Detail/DetailInterest").Text = $"Interest: {best.Interest}";
            GetNode<Label>("Root/Body/Detail/DetailVisits").Text = $"Visits: {best.Visits}";
        }
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event.IsActionPressed("ui_cancel"))
        {
            EmitSignal(SignalName.BackPressed);
        }
    }

    private static Control BuildRow(RecruitingOffer offer)
    {
        var row = new HBoxContainer();
        row.AddChild(MakeCell(offer.School, 200, true));
        row.AddChild(MakeCell(offer.Tier.ToString(), 120));
        row.AddChild(MakeCell(offer.Interest.ToString(), 80));
        row.AddChild(MakeCell(offer.Visits.ToString(), 60));
        return row;
    }

    private static Label MakeCell(string text, float width, bool expand = false)
    {
        return new Label
        {
            Text = text,
            CustomMinimumSize = width > 0 ? new Vector2(width, 0) : Vector2.Zero,
            SizeFlagsHorizontal = expand ? Control.SizeFlags.ExpandFill : 0
        };
    }
}
