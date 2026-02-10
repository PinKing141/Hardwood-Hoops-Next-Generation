using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Recruiting;

namespace HardwoodHoops.Core.App.Services.Recruiting;

public sealed class RecruitingOfferService
{
    public RecruitingOfferBoard BuildSampleOffers()
    {
        return new RecruitingOfferBoard(new List<RecruitingOffer>
        {
            new("Florida", OfferTier.Committable, 78, 2),
            new("Oregon", OfferTier.Soft, 65, 1),
            new("Auburn", OfferTier.Soft, 62, 1),
            new("Michigan St", OfferTier.Watchlist, 50, 0),
            new("Texas A&M", OfferTier.Watchlist, 48, 0)
        });
    }

    public RecruitingOfferBoard BuildFromInterest(IEnumerable<RecruitingInterest> interests)
    {
        var offers = new List<RecruitingOffer>();
        foreach (var interest in interests)
        {
            var tier = interest.OfferMade
                ? OfferTier.Committable
                : (interest.Interest >= 0.6 ? OfferTier.Soft : OfferTier.Watchlist);
            offers.Add(new RecruitingOffer(
                interest.TeamId,
                tier,
                (int)System.Math.Round(interest.Interest * 100),
                interest.Visits));
        }
        return new RecruitingOfferBoard(offers);
    }
}
