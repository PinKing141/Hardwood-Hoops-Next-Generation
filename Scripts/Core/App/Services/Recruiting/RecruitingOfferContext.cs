using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Recruiting;

namespace HardwoodHoops.Core.App.Services.Recruiting;

public static class RecruitingOfferContext
{
    public static IReadOnlyList<RecruitingInterest> Interests { get; private set; } = new List<RecruitingInterest>();

    public static void UpdateInterests(IReadOnlyList<RecruitingInterest> interests)
    {
        Interests = interests;
    }
}
