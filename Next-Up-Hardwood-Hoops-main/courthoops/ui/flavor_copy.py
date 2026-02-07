from typing import List

from courthoops.domain.game.boxscore import BoxScore
from courthoops.domain.schedule.game import ScheduleGame


def pre_game_lines(schedule_game: ScheduleGame) -> List[str]:
    """Pre-game flavor surfaced in UI; no gameplay control implied."""
    lines: List[str] = []
    if schedule_game.featured:
        lines.append("Featured sim: full play-by-play with scouting, rankings, and media fallout.")
    else:
        lines.append("Background sim: quick stat update with a light perception nudge.")

    if schedule_game.phase:
        lines.append(f"Phase: {schedule_game.phase.replace('_', ' ').title()}")
    if schedule_game.national_tv:
        lines.append("National TV slot: sim can pause so you can hop in and watch live.")

    tags = set(schedule_game.tags or ())
    if "high_scout_presence" in tags:
        lines.append("Scout-heavy gym; every touch will be logged.")
    if "ranking_sensitive" in tags:
        lines.append("Ranking-sensitive: expect board movement after the buzzer.")
    if "media_visible" in tags:
        lines.append("Media-visible: a post-game blurb will hit the feed.")
    if "ranking_weighted" in tags:
        lines.append("Weighted stakes: senior/postseason games swing status harder.")
    if "identity_building" in tags:
        lines.append("Identity-builder: this sim shapes your scouting dossier.")
    return lines


def post_game_lines(schedule_game: ScheduleGame, box_score: BoxScore) -> List[str]:
    """Post-game flavor surfaced in UI; captures consequences, not control."""
    lines: List[str] = []
    lines.append(
        f"Final: {box_score.home_team_id} {box_score.home_score} — {box_score.away_team_id} {box_score.away_score}"
    )
    tags = set(schedule_game.tags or ())
    if "media_visible" in tags:
        lines.append("Media blurb queued from this sim.")
    if "ranking_sensitive" in tags or "ranking_weighted" in tags:
        lines.append("Rankings recalculated with this result baked in.")
    if "identity_building" in tags:
        lines.append("Scouting profile updated off this run, win or lose.")
    if not schedule_game.featured:
        lines.append("Background outcome: reputational shift is light by design.")
    return lines


def schedule_line(schedule_game: ScheduleGame) -> str:
    """Compact schedule row describing featured/background, tags, and TV."""
    tag_str = ", ".join(schedule_game.tags or ())
    feature_flag = "FEATURED" if schedule_game.featured else "BG"
    tv = " [NAT-TV]" if schedule_game.national_tv else ""
    phase = f" {schedule_game.phase}" if schedule_game.phase else ""
    return f"{schedule_game.week:02d} | {schedule_game.game_id} | {feature_flag}{tv}{phase} | {schedule_game.home_team_id} vs {schedule_game.away_team_id} | {tag_str}"
