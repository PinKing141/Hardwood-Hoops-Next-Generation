# Courthoops Foundation

Clean architecture scaffolding for the HS → College hoops simulation with real-time play-by-play, SQL persistence, and GUI-ready boundaries.

## Layout
- `courthoops/domain` — pure entities and value objects; **no imports from other layers**.
- `courthoops/simulation` — engines, play-by-play rendering, and rule helpers. Depends only on `domain`.
- `courthoops/app` — services and use cases that orchestrate workflows. Depends on `domain`, `simulation`, and repositories.
- `courthoops/infra` — persistence adapters, world generators, and shared utilities (RNG, logger, config). Depends inward only.
- `courthoops/cli` — minimal CLI entrypoint for now; GUI adapters will live in `courthoops/gui`.
- `courthoops/tests` — lightweight tests.

## Dependency Rules
- Domain imports → domain only.
- Simulation imports → domain.
- App imports → domain, simulation, repositories/services.
- Infra imports → nothing above it.
- UI (CLI/GUI) imports → app/use_cases only.

## Status
- SQLAlchemy models/session and repositories are wired in `infra/persistence/orm` and `infra/persistence/repositories` with domain mapping (players/teams/games/PBP/recruiting/pipeline/box scores).
- World pipeline (`app/services/world_pipeline_service.py`) ages players, frees scholarships, generates recruits, and commits via prestige-weighted RNG; pipeline snapshots persist.
- Simulation engines (`courthoops/simulation/engine`) handle shot/foul/rebound with RNG + team/player strengths; fatigue-aware lineups/subs are active via game state.
- Season service (`app/services/season_service.py`) runs schedules, saving game state, play-by-play, and box scores. Box scores persist through `BoxScoreRow`/`BoxScoreRepository`.
- Scouting/UI surface (`app/services/scouting_service.py`) exposes public OVR + 2K-style build names + top role descriptors; AI (`app/services/ai_decision_service.py`) returns true OVR + role affinities for roster/lineup logic.
- CLI demo (`python -m courthoops.cli.main --demo`) seeds a world, runs a demo game through the season service, and saves play-by-play, game state, and box scores.
- Tests: `python -m pytest` passes.
- Injuries: `InjuryService` assigns day-to-day/short-term/multi-week injuries with status text and days remaining; recovery ticks season-to-season and injured players are auto-skipped in lineups. Injury type/severity are persisted for querying and UI reports.
- Box scores: per-player lines include points, rebounds, assists, steals, blocks, turnovers, fouls, 3PM/3PA, minutes, plus advanced proxies (TS%, usage, AST%). CLI flags can print box scores and injury reports with these details.
- Fouls/FTs: Team foul tracking drives bonus free throws; shooting fouls create real FT attempts using player FT%, with occasional and-ones. ORtg/DRtg/TS/usage account for FTA in possession estimates.
- Recruiting: Weekly decay, region bias, visit caps, early/late signing windows, and competition resolution are implemented. Public vs. true ratings with class-rank noise are available for boards; visit/offer histories are persisted. CLI flags `--show-prospects` (public) and `--show-prospects-ai` (true) dump boards.
- Scheduling/standings: Regular-season generator supports rivalries and per-level schedules; postseason brackets seeded from standings; standings are persisted and printable from CLI. Progression knobs are configurable via `AppConfig` and used in CLI wiring.

## Ratings and overall
- Attribute ranges are stored 25–99, but generation targets realistic 35–95 bands per category. Hidden attributes (potential, clutch, consistency, decision discipline, injury proneness) exist for realism.
- Behaviour vectors (shot profile, rim aggression, creation, playmaking/pass profiles, defensive style/help, rebound bias, athletic usage) live in `PlayerTendencies` to drive emergent roles; role affinity (`app/services/role_affinity_service.py`) computes continuous affinities; build names (`app/services/build_name_service.py`) generate 2K-style labels for UI.
- True OVR (hidden, AI-facing) and public OVR (perceived, noisy) helpers live in `courthoops/domain/player/overall.py`. Gameplay still uses individual attributes; OVR is for sorting/UI/AI valuation.
- Scouting/UI: use `app/services/scouting_service.py` to surface public OVR, build names, and top role descriptors from continuous affinities. AI: use `app/services/ai_decision_service.py` to consume true OVR + role affinities for roster/lineup decisions.

## CLI/GUI surfacing
- CLI demo flags: `--show-boxes` prints box scores with per-player lines; `--show-injuries` lists active injuries with remaining days; `--show-scouting` prints public OVR/build/roles; `--show-standings` prints standings.
- Injury state (injured, injury_days, injury_status) is persisted on players for direct querying; surface in GUI by reading from the player repository or box score payloads.

## Name pool curation (one-off)
Large `first_names.pkl` / `last_names.pkl` datasets live in `courthoops/data`. Use the builder to create lightweight US-flavored pools:
```
python -m courthoops.infra.generators.name_pool_builder ^
  --first-pickle courthoops/data/first_names.pkl ^
  --last-pickle courthoops/data/last_names.pkl ^
  --out-first courthoops/data/us_male_first_names.json ^
  --out-last courthoops/data/us_last_names.json
```
Add `--ascii-display` if you need ASCII display names while preserving originals.

## Persistence (Universes and Saves)
- All tables are tagged with `universe_id` so multiple worlds can live in one SQLite file.
- Save slots link a `save_id` to a `universe_id` + `world_id` (see `save_slots` table).
- CLI flags:
  - `--db-path ./my_universe.db` to pick a DB file.
  - `--universe-id U1` to scope repos to a universe.
  - `--save-id SAVE1` / `--save-name "My Career"` to load or create a save slot (auto-sets universe on load).
  - `--migrate-db` to add `universe_id` columns and `save_slots` to an existing SQLite DB (run once).
  - `--list-saves` to list saves and exit.
- Example: `python -m courthoops.cli.main --demo --db-path ./courthoops.db --save-id SAVE1 --universe-id U1 --skip-bootstrap-if-data`.
- Migrations: Alembic is configured; run `alembic upgrade head` (set `ALEMBIC_DATABASE_URL` to point at your DB) to apply schema changes instead of manual edits.

## Libraries in Use
- Core: SQLAlchemy, Alembic, SQLAlchemy-Utils (ORM, migrations, convenience types).
- CLI/UI: Typer (CLI), Textual (terminal UI).
- Validation/IO: Pydantic (schemas/serialization).
- Data/Analytics: pandas, polars (ad-hoc DB analysis).
- Generation: Faker (seed data), factory_boy + pytest-factoryboy (test factories).
- Testing: pytest, pytest-cov, pytest-timeout, ruff, mypy.
