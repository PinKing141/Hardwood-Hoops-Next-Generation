using Godot;
using HardwoodHoops.Core;

namespace HardwoodHoops;

public partial class Main : Node
{
    public override void _Ready()
    {
        var rng = new Random(42);
        var player = PlayerProfile.CreateSample("Player One", Position.PointGuard, CareerPhase.HighSchool);
        var defender = PlayerProfile.CreateSample("Defender One", Position.ShootingGuard, CareerPhase.HighSchool);

        var simulation = new SimulationEngine();
        var eventLog = new EventLog();

        for (var i = 0; i < 3; i++)
        {
            var gameEvent = simulation.SimulatePossession(player, defender, rng);
            eventLog.Add(gameEvent);
        }

        var scouting = new ScoutingReport();
        scouting.UpdateFromEventLog(eventLog, player);

        GD.Print($"Events logged: {eventLog.Count}");
        GD.Print($"Public OVR: {scouting.PublicOvr:F1}, Private OVR: {scouting.PrivateOvr:F1}");
    }
}
