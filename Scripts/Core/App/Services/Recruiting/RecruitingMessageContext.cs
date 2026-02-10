using System.Collections.Generic;

namespace HardwoodHoops.Core.App.Services.Recruiting;

public static class RecruitingMessageContext
{
    public static IReadOnlyList<string> Messages { get; private set; } = new List<string>();

    public static void UpdateMessages(IReadOnlyList<string> messages)
    {
        Messages = messages;
    }
}
