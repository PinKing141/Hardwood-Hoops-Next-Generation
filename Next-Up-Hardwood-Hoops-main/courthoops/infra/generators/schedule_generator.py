import random
from typing import Iterable, List, Tuple, Dict, Set

from courthoops.domain.schedule.game import ScheduleGame

class ScheduleGenerator:
    """Generates regular season schedules and simple brackets."""

    def round_robin(self, team_ids: List[str]) -> List[Tuple[str, str, str]]:
        """
        Returns a list of (game_id, home_team_id, away_team_id).
        Each pair plays once with the first listed as home.
        """
        games: List[Tuple[str, str, str]] = []
        for i, home in enumerate(team_ids):
            for j, away in enumerate(team_ids):
                if i >= j:
                    continue
                game_id = f"{home}_vs_{away}"
                games.append((game_id, home, away))
        return games

    def generate_regular_season(
        self,
        teams_by_level: Dict[str, List[str]],
        rivalries: Set[frozenset[str]] | None = None,
        games_per_pair: int = 2,
        start_week: int = 1,
    ) -> List[ScheduleGame]:
        """
        Produces a multi-week schedule separated by level (D1/D2/D3).
        Home/away balanced by alternating who hosts in repeated matchups.
        Rivalries are flagged when the pair is in the rivalry set.
        """
        rivalries = rivalries or set()
        schedule: List[ScheduleGame] = []
        week = start_week
        for level, teams in teams_by_level.items():
            for idx, home in enumerate(teams):
                for jdx, away in enumerate(teams):
                    if idx >= jdx:
                        continue
                    for k in range(games_per_pair):
                        host, visitor = (home, away) if k % 2 == 0 else (away, home)
                        game_id = f"{level}_{host}_vs_{visitor}_g{k}"
                        schedule.append(
                            ScheduleGame(
                                game_id=game_id,
                                home_team_id=host,
                                away_team_id=visitor,
                                week=week,
                                level=level,
                                rivalry=frozenset({home, away}) in rivalries,
                            )
                        )
                        week += 1
        return schedule

    def generate_bracket(self, seeds: List[str], bracket_name: str, start_week: int = 1) -> List[ScheduleGame]:
        """
        Single-elimination bracket generator. Seeds is ordered list (1 is seeds[0]).
        """
        games: List[ScheduleGame] = []
        round_names = ["Quarterfinal", "Semifinal", "Final"]
        current_round = seeds
        week = start_week
        round_idx = 0
        while len(current_round) > 1 and round_idx < len(round_names):
            next_round = []
            for i in range(0, len(current_round), 2):
                if i + 1 >= len(current_round):
                    next_round.append(current_round[i])
                    continue
                home = current_round[i]
                away = current_round[i + 1]
                game_id = f"{bracket_name}_{round_names[round_idx]}_{home}_vs_{away}"
                games.append(
                    ScheduleGame(
                        game_id=game_id,
                        home_team_id=home,
                        away_team_id=away,
                        week=week,
                        level=bracket_name,
                        rivalry=False,
                        postseason_round=round_names[round_idx],
                    )
                )
                next_round.append(home)  # placeholder winner; actual sim would choose
                week += 1
            current_round = next_round
            round_idx += 1
        return games

    def generate_exposure_career_schedule(
        self,
        hs_teams: List[str],
        aau_teams: List[str],
        *,
        rng=None,
        start_week: int = 1,
        junior_games_per_pair: int = 3,
        senior_games_per_pair: int = 3,
    ) -> List[ScheduleGame]:
        """
        Build HS (junior+senior) and AAU schedules with featured/background flags that match
        the sim-first pacing: 8-10 featured junior HS, 6-8 featured AAU, 10-12 featured senior HS.
        Non-featured games are background sims by default.
        """
        rng = rng or random.Random()
        schedule: List[ScheduleGame] = []
        week = start_week

        # Junior HS regular season: 6-7 featured, rest background
        jr_regular = self.generate_regular_season(
            {"HS_JR": hs_teams},
            games_per_pair=junior_games_per_pair,
            start_week=week,
        )
        jr_regular = self._apply_featured_targets(
            jr_regular,
            featured_range=(6, 7),
            phase="junior_hs",
            base_tags=("high_school", "regular"),
            featured_tags=("identity_building", "scouting_profile"),
            background_tags=("background_sim",),
            national_tv_ratio=0.15,
            rng=rng,
        )
        schedule.extend(jr_regular)
        week = max((g.week for g in jr_regular), default=week) + 1

        # Junior HS playoffs: 2-3 featured (single elimination)
        jr_seeds = hs_teams[:4] if len(hs_teams) >= 2 else hs_teams
        jr_playoffs = self.generate_bracket(jr_seeds, bracket_name="HS_JR_POST", start_week=week) if len(jr_seeds) >= 2 else []
        jr_playoffs = self._apply_featured_targets(
            jr_playoffs,
            featured_range=(2, 3),
            phase="junior_hs_playoffs",
            base_tags=("high_school", "playoff"),
            featured_tags=("identity_building", "scouting_profile"),
            background_tags=("background_sim",),
            national_tv_ratio=0.35,
            rng=rng,
        )
        schedule.extend(jr_playoffs)
        week = max((g.week for g in jr_playoffs), default=week) + 1 if jr_playoffs else week

        # AAU circuit: 3-4 events, each with exactly 2 featured games
        events = rng.randint(3, 4)
        anchor = hs_teams[0] if hs_teams else (aau_teams[0] if aau_teams else "TEAM")
        opponent_pool = [tid for tid in aau_teams if tid != anchor] or aau_teams or [anchor]
        opponent_idx = 0
        for evt in range(events):
            event_games: List[ScheduleGame] = []
            games_in_event = max(3, min(len(opponent_pool), 4))
            for gi in range(games_in_event):
                opp = opponent_pool[opponent_idx % len(opponent_pool)]
                opponent_idx += 1
                home, away = (anchor, opp) if gi % 2 == 0 else (opp, anchor)
                gid = f"AAU_E{evt + 1}_{home}_vs_{away}_g{gi}"
                event_games.append(
                    ScheduleGame(
                        game_id=gid,
                        home_team_id=home,
                        away_team_id=away,
                        week=week,
                        level="AAU",
                    )
                )
                week += 1
            event_games = self._apply_featured_targets(
                event_games,
                featured_range=(2, 2),
                phase="aau",
                base_tags=("aau", f"event_{evt + 1}"),
                featured_tags=("high_scout_presence", "ranking_sensitive", "media_visible"),
                background_tags=("background_sim",),
                national_tv_ratio=0.5,
                rng=rng,
            )
            schedule.extend(event_games)

        # Senior HS regular: 7-8 featured, rest background, heavier weight
        sr_regular = self.generate_regular_season(
            {"HS_SR": hs_teams},
            games_per_pair=senior_games_per_pair,
            start_week=week,
        )
        sr_regular = self._apply_featured_targets(
            sr_regular,
            featured_range=(7, 8),
            phase="senior_hs",
            base_tags=("high_school", "regular"),
            featured_tags=("ranking_weighted", "status_lock"),
            background_tags=("background_sim",),
            national_tv_ratio=0.2,
            rng=rng,
        )
        schedule.extend(sr_regular)
        week = max((g.week for g in sr_regular), default=week) + 1

        # Senior HS playoffs: 3-4 featured (single elimination)
        sr_seeds = hs_teams[:4] if len(hs_teams) >= 2 else hs_teams
        sr_playoffs = self.generate_bracket(sr_seeds, bracket_name="HS_SR_POST", start_week=week) if len(sr_seeds) >= 2 else []
        sr_playoffs = self._apply_featured_targets(
            sr_playoffs,
            featured_range=(3, 4),
            phase="senior_hs_playoffs",
            base_tags=("high_school", "playoff"),
            featured_tags=("ranking_weighted", "status_lock"),
            background_tags=("background_sim",),
            national_tv_ratio=0.5,
            rng=rng,
        )
        schedule.extend(sr_playoffs)

        return schedule

    def _apply_featured_targets(
        self,
        games: List[ScheduleGame],
        *,
        featured_range: Tuple[int, int],
        phase: str,
        base_tags: Tuple[str, ...],
        featured_tags: Tuple[str, ...] = (),
        background_tags: Tuple[str, ...] = ("background_sim",),
        national_tv_ratio: float = 0.0,
        rng=None,
    ) -> List[ScheduleGame]:
        """Tag games as featured/background, attach phase/tags, and sprinkle national TV flags."""
        if not games:
            return games
        rng = rng or random.Random()
        for g in games:
            g.phase = phase

        floor, ceiling = featured_range
        floor = max(0, floor)
        ceiling = max(floor, ceiling)
        target = floor if ceiling == floor else rng.randint(floor, ceiling)
        target = min(target, len(games))

        featured_games = set(rng.sample(games, target)) if target > 0 else set()
        for g in games:
            g.featured = g in featured_games
            tag_list = list(base_tags)
            if g.postseason_round:
                tag_list.append(g.postseason_round)
            if g.featured:
                tag_list.append("featured")
                tag_list.extend(featured_tags)
            else:
                tag_list.append("background")
                tag_list.extend(background_tags)
            # Deduplicate while preserving order
            g.tags = tuple(dict.fromkeys(tag_list))
            g.national_tv = False

        if national_tv_ratio > 0 and featured_games:
            tv_count = max(1, int(len(featured_games) * national_tv_ratio))
            tv_choices = rng.sample(list(featured_games), min(tv_count, len(featured_games)))
            for g in tv_choices:
                g.national_tv = True

        return games
