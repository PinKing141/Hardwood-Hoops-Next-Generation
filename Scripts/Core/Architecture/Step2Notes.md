# Step 2 Notes (Architecture Setup)

This file exists to confirm the Step 2 checklist items were implemented.

## Folder Layout Created
- `Scripts/Core/Domain`
- `Scripts/Core/Simulation`
- `Scripts/Core/App/Services`
- `Scripts/Core/Infra`
- `Scripts/Core/UI`

## Interfaces Added
- RNG: `IRng` + `SeededRng`
- Persistence: `IRepository`, `IGameRepository`, `IBoxScoreRepository`, `IPlayByPlayRepository`
- Simulation engine factory: `IGameEngine`, `IGameEngineFactory`, `GameEngineContext`

## Dependency Rules
See `Scripts/Core/Architecture/DependencyRules.md`.

