using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Recruiting;

namespace HardwoodHoops.Core.App.Services.Recruiting;

public sealed class RecruitingCommitmentService
{
    public IReadOnlyList<RecruitingInterest> BuildCommitments(IEnumerable<RecruitingInterest> interests)
    {
        var list = new List<RecruitingInterest>(interests);
        list.Sort((a, b) => b.Interest.CompareTo(a.Interest));
        return list;
    }
}
