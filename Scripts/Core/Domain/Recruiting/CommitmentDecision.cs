namespace HardwoodHoops.Core.Domain.Recruiting;

public sealed class CommitmentDecision
{
    public CommitmentDecision(string playerId, string teamId, bool committed, string rationale = "")
    {
        PlayerId = playerId;
        TeamId = teamId;
        Committed = committed;
        Rationale = rationale;
    }

    public string PlayerId { get; }
    public string TeamId { get; }
    public bool Committed { get; }
    public string Rationale { get; }
}
