# SDLC Plan — Hardwood Hoops (Godot C#)

## 1. Vision & Scope
- **Goal:** Build a text-based, simulation-first basketball career mode (HS → College → NBA).
- **Non-Goals:** Fully authored narrative, physics-based gameplay, real-time 3D.

## 2. Requirements
### Functional
- Career progression with scaling difficulty.
- Live feed simulation with event log.
- Training and progression system.
- Scouting with public/private OVR.
- Archetype generation from stats.

### Non-Functional
- Deterministic + probabilistic simulation.
- Fast UI updates with large text logs.
- Extensible data model for stats/teams.

## 3. Architecture
### Core Modules
1. **Player Model**
2. **Meta-Stats + Archetypes**
3. **Simulation Engine**
4. **Event Log**
5. **Training Manager**
6. **Scouting Manager**
7. **UI / Live Feed**

### Data Flow
```
Weekly Loop -> Training -> Game Sim -> Event Log -> Scouting Updates
```

## 4. Development Phases
1. **Foundation**
   - Core models, enums, config, and minimal scene.
2. **Simulation MVP**
   - Possession loop, event generation, basic feed output.
3. **Progression MVP**
   - Training tick, growth profile, stat caps.
4. **Scouting MVP**
   - Public/Private OVR calculations, recruitment triggers.
5. **UX Polish**
   - Log filtering, speed controls, performance optimizations.

## 5. Testing & Validation
- Unit tests for stat calculations.
- Integration checks for simulation loop.
- Seeded random for reproducibility.

## 6. Release Milestones
- **M1:** Simulated single game with event log.
- **M2:** Weekly loop + training.
- **M3:** Recruitment + draft mock.
- **M4:** UI polish + performance tuning.
