# Integration Checklist (Follow Exactly)

> Purpose: A strict, step-by-step checklist to integrate and repurpose features from
> `Next-Up-Hardwood-Hoops-main` into this C# game without overstepping scope.
> Follow each step in order. Do not skip or add extra work without updating this list.

## 0) Pre-Work Guardrails
- [ ] Confirm the current working directory is the repo root.
- [ ] Do **not** modify files outside this repo.
- [ ] Only touch files required by the checklist.
- [ ] If a step cannot be completed, **stop** and record the blocker.

## 1) Inventory & Mapping
- [ ] List the **exact** modules to reuse from `Next-Up-Hardwood-Hoops-main`:
  - [ ] Domain entities (Player, Team, GameState, Event, RecruitingInterest, etc.)
  - [ ] Simulation engines (GameEngine, PossessionEngine, Shot/Foul/Rebound)
  - [ ] App services (Recruiting, Progression, Season, Injury, WorldPipeline)
  - [ ] UI helpers (Scouting, BuildName, RoleAffinity, Shot Diet views)
- [ ] Create a mapping table: Python source class → C# target class/interface.
- [ ] Mark any modules that will **not** be ported (with rationale).

## 2) C# Architecture Setup
- [ ] Define project folders: `Domain/`, `Simulation/`, `App/Services/`, `Infra/`, `UI/`.
- [ ] Define interfaces for:
  - [ ] RNG (deterministic, seedable)
  - [ ] Persistence (repositories)
  - [ ] Simulation engine factory
- [ ] Document dependency direction rules (Domain → Simulation → App → UI).

## 3) Port Core Domain Models
- [ ] Implement Player-related models:
  - [ ] PlayerAttributes
  - [ ] PlayerTendencies
  - [ ] PlayerPersonality
  - [ ] Player
- [ ] Implement Team model.
- [ ] Implement GameState + Event models.
- [ ] Implement Recruiting models.
- [ ] Add serialization tests for each model (JSON round-trip).

## 4) Port Simulation Engines
- [ ] GameEngine (clock, possessions, fatigue, lineups).
- [ ] PossessionEngine (play selection, shooter selection, event dispatch).
- [ ] ShotEngine (shot type + probability + FT logic).
- [ ] FoulEngine (foul checks + bonus logic).
- [ ] ReboundEngine (rebound resolution + fatigue/foul influence).
- [ ] Determinism test: same seed → same event stream.

## 5) Port Career/Franchise Services
- [ ] WorldPipelineService (aging, recruiting, roster updates).
- [ ] RecruitingService (interest ticks, visits/offers, signing windows).
- [ ] ProgressionService (soft caps, aging decline).
- [ ] InjuryService (injury + recovery).
- [ ] SeasonService (schedule sim, box scores, play-by-play output).

## 6) UI Integration
- [ ] ScoutingService (public OVR, build names, role descriptors).
- [ ] BuildNameService (2K-style naming rules).
- [ ] RoleAffinityService (tendency-based affinities).
- [ ] Shot Diet UI (preference view first; efficiency later).
- [ ] Class Rankings UI (Top 10/25/50/100 bands).

## 7) Persistence & Saves
- [ ] Decide storage format (SQLite/JSON/engine-native).
- [ ] Implement repositories for Player/Team/Game/Recruiting/BoxScore.
- [ ] Add versioning or migration strategy if needed.

## 8) Validation & Review
- [ ] Run unit tests for domain, sim, and services.
- [ ] Run end-to-end sim test (single game + mini-season).
- [ ] Verify UI data contracts (scouting reports + shot diet).
- [ ] Update this checklist with any new required steps.

## 9) Stop Conditions
- [ ] If a step is unclear, stop and ask for clarification.
- [ ] Do not implement extra features beyond this list.
- [ ] Only proceed when the current checklist item is complete.
