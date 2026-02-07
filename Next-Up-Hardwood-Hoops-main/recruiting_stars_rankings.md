FINAL RECRUITING, STARS, AND RANKINGS SYSTEM
(Sim-driven, player-first, visible lists, hidden mechanics)

1) CORE DECISIONS (LOCKED)
Star visibility and ranges
- AI uses 0-5 stars internally.
- Player starts internally as a 3-star.
- Player only ever sees 3-5 stars.
- 0-2 stars exist only for AI and background prospects.

Rankings visibility
- National Top 100 list is visible to the player.
- Class rankings are visible to the player.
- Player rank number is visible (if ranked).
- The player never sees underlying scores or thresholds.

2) INTERNAL SYSTEM (WHAT DRIVES EVERYTHING)
These are system-only values. They are saved to the database for analysis, but not displayed to the player.

Exposure Score (0-100)
- Represents national visibility.
- Influenced by: featured games only; event importance (AAU > playoffs > regular season); expectations vs outcome; opponent quality; scout/media presence.
- Decay: slow decay when not appearing in featured games; much slower decay once ranked (Top 100).

Performance Delta (per featured game)
- Contextual performance band, not box-score spam: Major Positive / Positive / Neutral / Negative / Major Negative.
- Based on: role expectation (primary/secondary/glue); efficiency vs volume; defensive impact relative to assignment; discipline (turnovers/fouls); clutch situations (if used).

Recruit Momentum
- Short-term trend: Rising / Stable / Falling.
- Affects how quickly things move, not the direction.

3) NATIONAL TOP 100 (VISIBLE LIST, CONTROLLED UPDATES)
What Top 100 means
- Top 100 is a visibility gate that also shows as a public ranking list.
- Being Top 100 causes (system effects): increased scout attendance in future featured games; colleges evaluate with higher confidence (less uncertainty); offers arrive earlier and with stronger tiers; media attention increases.

What the player sees (Top 100 screen)
- Ranked list #1-#100.
- Name, position, school/AAU team, class year.
- Visible stars: 3-5 only.
- Optional trend tag: Rising / Falling / Stable.

What the player never sees
- Exposure Score values.
- Performance Delta values.
- Momentum values.
- Exact reasons for jumps.
- Entry thresholds.

Update windows (ONLY THESE)
- Rankings refresh only at checkpoints: end of AAU events; mid Senior HS season; end of Senior HS regular season.
- Never: after each game; mid-week; after background sims.

Movement rules (banded, believable)
- Players move mostly within bands: Top 10; 11-25; 26-50; 51-100; outside Top 100.
- Crossing bands requires: Major Positive performances; high-visibility stages (AAU, playoffs).

Entering the Top 100 (system logic)
- Checked only at checkpoints.
- Requirements: exposure crosses hidden threshold; recent Performance Delta at least Positive; momentum is not Falling.
- Player-facing feedback: "You have entered the National Top 100."; increased scout presence; media blurbs.

Dropping out (rare, gradual)
- Requires multiple poor checkpoint updates.
- Usually gradual: 88 -> 97 -> out.
- Sudden drops only with major injuries or collapses (if modeled).

4) CLASS RANKINGS (VISIBLE, FILTERED VIEW)
- Class Rankings are simply Top 100 filtered by class, plus near-miss tracking if desired.
- Player can view: their class list; rank bands (Top 10 / Top 25 / Top 50 / Top 100); stars (3-5 only).
- Same rules apply: updates only at checkpoints; reasons hidden.

5) STAR SYSTEM (COARSE, PLAYER-FACING SUMMARY)
Stars represent perception tier, not ratings.

Player-visible star tiers
- 3-star (***): Legit prospect (regional to fringe national).
- 4-star (****): Nationally recognised.
- 5-star (*****): Elite.

Stars update only at checkpoints
- End of AAU; mid Senior HS; end Senior HS.

How stars change
- Promotions:
  - 3-star -> 4-star: enter Top 100 or very strong AAU plus strong Senior HS start.
  - 4-star -> 5-star: sustained Top 100 presence; multiple high-impact checkpoints; strong momentum, no collapse.
- Demotions:
  - Rare and slow.
  - Only after prolonged underperformance at multiple checkpoints.

Stars vs Rank (critical separation)
- A 3-star can be Top 100.
- A 4-star might be ranked lower than another 4-star.
- A 5-star is usually Top 25, but not guaranteed.

6) AI-ONLY STARS (0-2) AND WORLD POPULATION
- AI-only 0-2 star prospects exist to: fill teams realistically; populate AAU fields; commit to low-tier programmes; occasionally produce rare late risers.
- Player experience rule: player never sees "1-star prospects"; player never feels unfairly compared to low-tier fillers.

7) COLLEGE RECRUITING INTERACTION (WHAT COLLEGES USE)
- Colleges evaluate players using: star tier (quick filter); Top 100 status (confidence multiplier); team fit (needs/position/style); risk profile (injury, consistency, discipline); momentum trend.
- Important behaviour outcomes: a 3-star ranked Top 100 can out-recruit a quiet 4-star; a 5-star with falling momentum still gets offers, but with caution.

8) FINAL LOCK-IN SUMMARY
- AI uses 0-5 stars.
- Player starts internally 3-star.
- Player only sees 3-5 stars.
- National Top 100 is visible.
- Class rankings are visible.
- Rankings update only at checkpoints.
- Movement is banded and believable.
- Exposure maths remains hidden.
- No per-game ranking updates.
- No frequent star changes.

If you want the next pillar, say so and I will lock offer structure in the same "canon" format:
- soft vs committable offers
- scholarship tiers
- offer expiry/pulls
- commitment timing and flips
