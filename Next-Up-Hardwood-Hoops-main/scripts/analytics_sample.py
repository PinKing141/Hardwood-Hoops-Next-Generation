"""
Example ad-hoc analytics using pandas and polars against the SQLite DB.
Run: python scripts/analytics_sample.py --db courthoops.db
"""
import argparse
import polars as pl
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="courthoops.db")
    parser.add_argument("--universe", default=None, help="Filter by universe_id if present.")
    args = parser.parse_args()

    con = pl.read_database(
        "select game_id, home_team_id, away_team_id, home_score, away_score, universe_id from box_scores",
        f"sqlite:///{args.db}",
    )
    if args.universe:
        con = con.filter(pl.col("universe_id") == args.universe)
    # Simple margin stats with polars
    con = con.with_columns((pl.col("home_score") - pl.col("away_score")).alias("margin"))
    print("Top 5 blowouts (polars):")
    print(con.sort("margin", descending=True).head(5))

    # Pandas: aggregate team records
    df = pd.read_sql_query(
        "select home_team_id as team_id, home_score as for_pts, away_score as against_pts, universe_id from box_scores",
        f"sqlite:///{args.db}",
    )
    if args.universe:
        df = df[df["universe_id"] == args.universe]
    summary = (
        df.groupby("team_id")[["for_pts", "against_pts"]]
        .sum()
        .assign(point_diff=lambda x: x.for_pts - x.against_pts)
        .sort_values("point_diff", ascending=False)
        .head(5)
    )
    print("\nTop 5 point differential (pandas):")
    print(summary)


if __name__ == "__main__":
    main()
