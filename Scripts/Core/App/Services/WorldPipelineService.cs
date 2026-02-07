using System;
using System.Collections.Generic;
using HardwoodHoops.Core.Domain.Players;
using HardwoodHoops.Core.Domain.Recruiting;
using HardwoodHoops.Core.Domain.Teams;
using HardwoodHoops.Core.Infra.Persistence;
using HardwoodHoops.Core.Simulation.Rng;

namespace HardwoodHoops.Core.App.Services;

public sealed class WorldPipelineService
{
    private readonly IRepository<Player> _playerRepo;
    private readonly IRepository<Team> _teamRepo;
    private readonly IRepository<RecruitingInterest> _recruitingRepo;
    private readonly IRng _rng;
    private readonly ProgressionService _progressionService;
    private readonly Action<string> _logger;

    public WorldPipelineService(
        IRepository<Player> playerRepo,
        IRepository<Team> teamRepo,
        IRepository<RecruitingInterest> recruitingRepo,
        IRng rng,
        ProgressionService? progressionService = null,
        Action<string>? logger = null)
    {
        _playerRepo = playerRepo;
        _teamRepo = teamRepo;
        _recruitingRepo = recruitingRepo;
        _rng = rng;
        _progressionService = progressionService ?? new ProgressionService();
        _logger = logger ?? (_ => { });
    }

    public void AdvanceYear()
    {
        _logger("Starting world pipeline");
        var players = _playerRepo.ListAll();
        var teams = _teamRepo.ListAll();
        var positionMap = DerivePositionMap(teams);

        var agedPlayers = AgePlayers(players);
        HandleGraduations(agedPlayers, teams);
        var vacancies = OpenScholarships(teams);
        var recruits = GenerateRecruitPool(vacancies);
        AssignRecruitsToTeams(recruits, teams, vacancies);
        ApplyDevelopment(agedPlayers);
        _progressionService.ApplyGrowth(agedPlayers, positionMap);
        SaveEntities(agedPlayers, recruits, teams);

        _logger("World pipeline completed");
    }

    private List<Player> AgePlayers(IEnumerable<Player> players)
    {
        var updated = new List<Player>();
        foreach (var player in players)
        {
            var classYear = player.ClassYear;
            if (classYear.Contains("HS") && classYear.Contains("SR"))
            {
                player.ClassYear = "Recruit";
            }
            else if (classYear.Contains("HS"))
            {
                player.ClassYear = IncrementClass(classYear);
            }
            else if (classYear.Contains("College"))
            {
                player.ClassYear = IncrementClass(classYear);
            }
            updated.Add(player);
        }
        return updated;
    }

    private static void HandleGraduations(IEnumerable<Player> players, IEnumerable<Team> teams)
    {
        var graduated = new HashSet<string>();
        foreach (var player in players)
        {
            if (player.ClassYear.Contains("Graduate"))
            {
                graduated.Add(player.PlayerId);
            }
        }

        foreach (var team in teams)
        {
            team.Roster.RemoveAll(pid => graduated.Contains(pid));
        }
    }

    private static Dictionary<string, int> OpenScholarships(IEnumerable<Team> teams)
    {
        var vacancies = new Dictionary<string, int>();
        foreach (var team in teams)
        {
            var openSlots = Math.Max(team.Scholarships - team.Roster.Count, 0);
            vacancies[team.TeamId] = openSlots;
        }
        return vacancies;
    }

    private Dictionary<string, string> DerivePositionMap(IEnumerable<Team> teams)
    {
        var mapping = new Dictionary<string, string>();
        var positions = new[] { "guard", "guard", "wing", "wing", "center" };
        foreach (var team in teams)
        {
            for (var i = 0; i < team.Roster.Count; i++)
            {
                mapping[team.Roster[i]] = positions[i % positions.Length];
            }
        }
        return mapping;
    }

    private List<Player> GenerateRecruitPool(Dictionary<string, int> vacancies)
    {
        var totalNeeded = Math.Max(0, Sum(vacancies.Values)) + 4;
        var recruits = new List<Player>();
        var positions = new[] { "PG", "SG", "SF", "PF", "C" };
        for (var i = 0; i < totalNeeded; i++)
        {
            var pid = $"REC-{Guid.NewGuid():N}".Substring(0, 12);
            var pos = positions[_rng.NextInt(0, positions.Length - 1)];
            var attrs = new PlayerAttributes(
                _rng.NextInt(40, 95),
                _rng.NextInt(25, 95),
                _rng.NextInt(35, 95),
                _rng.NextInt(30, 90),
                _rng.NextInt(25, 95),
                _rng.NextInt(40, 95),
                _rng.NextInt(30, 90),
                _rng.NextInt(35, 90),
                _rng.NextInt(40, 90),
                _rng.NextInt(30, 90),
                _rng.NextInt(35, 90),
                _rng.NextInt(30, 90),
                _rng.NextInt(30, 90),
                _rng.NextInt(25, 95),
                _rng.NextInt(35, 95),
                _rng.NextInt(35, 95),
                _rng.NextInt(25, 95),
                _rng.NextInt(30, 90),
                _rng.NextInt(40, 95),
                _rng.NextInt(40, 90),
                _rng.NextInt(40, 90),
                _rng.NextInt(35, 95),
                _rng.NextInt(40, 95),
                _rng.NextInt(25, 80),
                _rng.NextInt(30, 95),
                _rng.NextInt(30, 90),
                _rng.NextInt(35, 90));

            var recruit = new Player(
                playerId: pid,
                name: $"Recruit {pid}",
                classYear: "Recruit",
                attributes: attrs,
                tendencies: PlayerTendencies.Default(),
                personality: PlayerPersonality.Default());
            recruit.Stats["position"] = pos;
            recruits.Add(recruit);
        }

        return recruits;
    }

    private void AssignRecruitsToTeams(List<Player> recruits, List<Team> teams, Dictionary<string, int> vacancies)
    {
        foreach (var recruit in recruits)
        {
            var eligible = new List<Team>();
            foreach (var team in teams)
            {
                if (vacancies.GetValueOrDefault(team.TeamId) > 0)
                {
                    eligible.Add(team);
                }
            }
            if (eligible.Count == 0)
            {
                break;
            }

            var weights = new List<double>();
            foreach (var team in eligible)
            {
                weights.Add(Math.Max(team.Prestige, 1));
            }
            var teamPicked = _rng.ChoiceWeighted(eligible, weights);
            teamPicked.AddPlayer(recruit.PlayerId);
            vacancies[teamPicked.TeamId] -= 1;
            recruit.ClassYear = "College FR";
            _recruitingRepo.Save(new RecruitingInterest(recruit.PlayerId, teamPicked.TeamId, 1.0, teamPicked.Prestige / 100.0)
            {
                OfferMade = true,
                Committed = true
            });
        }
    }

    private static void ApplyDevelopment(IEnumerable<Player> players)
    {
        foreach (var player in players)
        {
            var growthFactor = 1 + (player.Attributes.Potential - 50) / 100.0;
            var consistencyPenalty = Math.Max(0.5, player.Attributes.Consistency / 100.0);
            var disciplinePenalty = Math.Max(0.6, player.Attributes.DecisionDiscipline / 100.0);
            var delta = 1 * growthFactor * consistencyPenalty * disciplinePenalty;
            var attrs = player.Attributes with
            {
                Layup = Math.Min(99, player.Attributes.Layup + (int)delta),
                Dunk = Math.Min(99, player.Attributes.Dunk + (int)delta),
                Inside = Math.Min(99, player.Attributes.Inside + (int)delta),
                MidRange = Math.Min(99, player.Attributes.MidRange + (int)delta),
                ThreePoint = Math.Min(99, player.Attributes.ThreePoint + (int)delta),
                FreeThrow = Math.Min(99, player.Attributes.FreeThrow + (int)delta),
                OffensiveRebound = Math.Min(99, player.Attributes.OffensiveRebound + (int)delta),
                BallControl = Math.Min(99, player.Attributes.BallControl + (int)delta),
                Passing = Math.Min(99, player.Attributes.Passing + (int)delta),
                DefensiveRebound = Math.Min(99, player.Attributes.DefensiveRebound + (int)delta),
                PerimeterDefense = Math.Min(99, player.Attributes.PerimeterDefense + (int)delta),
                InteriorDefense = Math.Min(99, player.Attributes.InteriorDefense + (int)delta),
                Steal = Math.Min(99, player.Attributes.Steal + (int)delta),
                Block = Math.Min(99, player.Attributes.Block + (int)delta),
                Speed = Math.Min(99, player.Attributes.Speed + (int)delta),
                Agility = Math.Min(99, player.Attributes.Agility + (int)delta),
                Vertical = Math.Min(99, player.Attributes.Vertical + (int)delta),
                Strength = Math.Min(99, player.Attributes.Strength + (int)delta),
                Stamina = Math.Min(99, player.Attributes.Stamina + (int)delta),
                OffensiveIq = Math.Min(99, player.Attributes.OffensiveIq + (int)delta),
                DefensiveIq = Math.Min(99, player.Attributes.DefensiveIq + (int)delta),
                Hustle = Math.Min(99, player.Attributes.Hustle + (int)delta),
                Clutch = Math.Min(99, player.Attributes.Clutch + (int)delta),
                Consistency = Math.Min(99, player.Attributes.Consistency + (int)delta),
                DecisionDiscipline = Math.Min(99, player.Attributes.DecisionDiscipline + (int)delta)
            };
            player.Attributes = attrs;
        }
    }

    private void SaveEntities(IEnumerable<Player> players, IEnumerable<Player> recruits, IEnumerable<Team> teams)
    {
        foreach (var player in players)
        {
            _playerRepo.Save(player);
        }
        foreach (var recruit in recruits)
        {
            _playerRepo.Save(recruit);
        }
        foreach (var team in teams)
        {
            _teamRepo.Save(team);
        }
    }

    private static int Sum(IEnumerable<int> values)
    {
        var total = 0;
        foreach (var value in values)
        {
            total += value;
        }
        return total;
    }

    private static string IncrementClass(string classYear)
    {
        var steps = new[] { "FR", "SO", "JR", "SR" };
        for (var i = 0; i < steps.Length; i++)
        {
            if (classYear.Contains(steps[i]) && i + 1 < steps.Length)
            {
                return classYear.Replace(steps[i], steps[i + 1]);
            }
        }
        return classYear.Contains("SR") ? "Graduate" : classYear;
    }
}
