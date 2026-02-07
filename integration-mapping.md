# Integration Mapping (Step 1: Inventory & Mapping)

This document captures the **exact** modules to reuse from `Next-Up-Hardwood-Hoops-main`,
the target C# counterparts, and any items explicitly excluded from the porting scope.

## 1) Reuse Inventory (Exact Modules)

### Domain entities
- `courthoops/domain/player/entity.py` → Player models
- `courthoops/domain/player/overall.py` → Overall rating logic
- `courthoops/domain/team/entity.py` → Team model
- `courthoops/domain/game/state.py` → GameState model
- `courthoops/domain/game/events.py` → Event model
- `courthoops/domain/recruiting/models.py` → Recruiting interest/commitment models

### Simulation engines
- `courthoops/simulation/engine/game_engine.py` → Game loop and clock control
- `courthoops/simulation/engine/possession_engine.py` → Possession selection + event flow
- `courthoops/simulation/engine/shot_engine.py` → Shot resolution and FT logic
- `courthoops/simulation/engine/foul_engine.py` → Foul checks and bonus logic
- `courthoops/simulation/engine/rebound_engine.py` → Rebound resolution

### App services
- `courthoops/app/services/world_pipeline_service.py` → Offseason pipeline (aging/recruiting)
- `courthoops/app/services/recruiting_service.py` → Interest/visits/commitments
- `courthoops/app/services/progression_service.py` → Attribute growth + decline
- `courthoops/app/services/injury_service.py` → Injury and recovery logic
- `courthoops/app/services/season_service.py` → Schedule simulation + box scores
- `courthoops/app/services/role_affinity_service.py` → Role affinity weights
- `courthoops/app/services/build_name_service.py` → 2K-style build names
- `courthoops/app/services/scouting_service.py` → Scouting report aggregation
- `courthoops/app/services/player_evaluation_service.py` → True/public OVR evaluation

### UI helpers / mockups
- `NextToAdd.md` → Class Rankings + Shot Diet UI references

### Infra utilities (to mirror)
- `courthoops/infra/utils/rng.py` → Deterministic RNG abstraction

## 2) Python → C# Mapping Table

| Python Source | C# Target | Notes |
| --- | --- | --- |
| `PlayerAttributes` | `Domain/Players/PlayerAttributes.cs` | POCO/record with validation helpers. |
| `PlayerTendencies` | `Domain/Players/PlayerTendencies.cs` | Include normalized vectors. |
| `PlayerPersonality` | `Domain/Players/PlayerPersonality.cs` | Simple value object. |
| `Player` | `Domain/Players/Player.cs` | Root entity with stats + injury flags. |
| `Team` | `Domain/Teams/Team.cs` | Roster, prestige, region. |
| `GameState` | `Domain/Games/GameState.cs` | Event list + fatigue/fouls/injuries. |
| `Event` | `Domain/Games/Event.cs` | Typed event + payload data. |
| `RecruitingInterest` | `Domain/Recruiting/RecruitingInterest.cs` | Interest, visits, ratings. |
| `CommitmentDecision` | `Domain/Recruiting/CommitmentDecision.cs` | Recruit commitments. |
| `compute_true_overall` | `Domain/Players/OverallCalculator.cs` | Static/utility class. |
| `compute_public_overall` | `Domain/Players/OverallCalculator.cs` | Deterministic noise logic. |
| `IRNG` | `Simulation/Rng/IRng.cs` | Interface with seedable impl. |
| `PythonRNG` | `Simulation/Rng/SeededRng.cs` | Deterministic RNG implementation. |
| `GameEngine` | `Simulation/Engines/GameEngine.cs` | Main simulation loop. |
| `PossessionEngine` | `Simulation/Engines/PossessionEngine.cs` | Possession dispatcher. |
| `ShotEngine` | `Simulation/Engines/ShotEngine.cs` | Shot resolution. |
| `FoulEngine` | `Simulation/Engines/FoulEngine.cs` | Foul checks + bonus. |
| `ReboundEngine` | `Simulation/Engines/ReboundEngine.cs` | Rebound logic. |
| `WorldPipelineService` | `App/Services/WorldPipelineService.cs` | Offseason pipeline. |
| `RecruitingService` | `App/Services/RecruitingService.cs` | Interest/commitments. |
| `ProgressionService` | `App/Services/ProgressionService.cs` | Growth/decline. |
| `InjuryService` | `App/Services/InjuryService.cs` | Injury/recovery. |
| `SeasonService` | `App/Services/SeasonService.cs` | Schedule sim + box scores. |
| `RoleAffinityService` | `App/Services/RoleAffinityService.cs` | Role weights. |
| `BuildNameService` | `App/Services/BuildNameService.cs` | Build naming rules. |
| `ScoutingService` | `App/Services/ScoutingService.cs` | UI scouting data. |
| `PlayerEvaluationService` | `App/Services/PlayerEvaluationService.cs` | OVR evaluation. |
| `NextToAdd.md` mockups | `UI/Recruiting/ClassRankingsView.*` | UI layout/behavior only. |
| `NextToAdd.md` mockups | `UI/Scouting/ShotDietView.*` | UI layout/behavior only. |

## 3) Explicitly Not Porting (For Now)

These are out of scope for the initial C# port and **should not be implemented** unless
the checklist is updated:

- `courthoops/infra/persistence/*` (SQLAlchemy/Alembic specifics) → Use C#-native storage later.
- `courthoops/cli/*` and Textual UI → Not needed for game client.
- `courthoops/tests/*` → Will be replaced with C# test suite.
- `courthoops/data/*` large name pools → Optional, defer until name generation is finalized.

