using System.Collections.Generic;

namespace HardwoodHoops.Core.Domain.Recruiting;

public enum OfferTier
{
    Watchlist,
    Soft,
    Committable
}

public sealed class RecruitingOffer
{
    public RecruitingOffer(string school, OfferTier tier, int interest, int visits)
    {
        School = school;
        Tier = tier;
        Interest = interest;
        Visits = visits;
    }

    public string School { get; }
    public OfferTier Tier { get; }
    public int Interest { get; }
    public int Visits { get; }
}

public sealed class RecruitingOfferBoard
{
    public RecruitingOfferBoard(IReadOnlyList<RecruitingOffer> offers)
    {
        Offers = offers;
    }

    public IReadOnlyList<RecruitingOffer> Offers { get; }
}
