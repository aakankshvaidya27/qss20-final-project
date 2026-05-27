## 03_analyze_spatial.py
## Three figures for Milestone 2:
## (1) shot frequency (counts) — descriptive baseline
## (2) mean opponent displacement by shot type — reframes shot selection as pressure
## (3) cumulative displacement over rally length, winners vs losers — links pressure to outcome

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

## ============================================================
## SECTION 1: LOAD PROCESSED DATA
## ============================================================

PROC_DIR = "data/processed"
OUT_DIR = "output"
os.makedirs(OUT_DIR, exist_ok=True)

strokes = pd.read_csv(os.path.join(PROC_DIR, "strokes_all.csv"))

print("=== loaded processed strokes ===")
print("rows:", len(strokes))
print("matches:", strokes["match_id"].nunique())
print()

## ============================================================
## FIGURE 1: SHOT FREQUENCY
## (the descriptive baseline — what shots are people hitting at all)
## ============================================================

shot_counts = strokes["shot_type"].value_counts()

fig, ax = plt.subplots(figsize=(10, 6))
shot_counts.plot(kind="barh", ax=ax, color="steelblue")
ax.invert_yaxis()
ax.set_xlabel("number of strokes")
ax.set_ylabel("shot type")
ax.set_title("Shot type frequency across ShuttleSet22")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "shot_frequency.png"), dpi=150)
plt.close()
print("saved output/shot_frequency.png")

## ============================================================
## FIGURE 2: MEAN OPPONENT DISPLACEMENT BY SHOT TYPE
## (the reframing — which shot types actually force the opponent to move?)
## ============================================================

## drop rows where displacement is missing (serves often have no opponent position recorded)
disp_df = strokes.dropna(subset=["displacement", "shot_type"])

## compute mean displacement per shot type, plus n for each
disp_by_type = (
    disp_df.groupby("shot_type")
    .agg(mean_displacement=("displacement", "mean"),
         n=("displacement", "size"))
    .sort_values("mean_displacement", ascending=True)
)

## only keep shot types with reasonable sample size for stability
disp_by_type = disp_by_type[disp_by_type["n"] >= 30]

fig, ax = plt.subplots(figsize=(10, 6))
disp_by_type["mean_displacement"].plot(kind="barh", ax=ax, color="firebrick")
ax.set_xlabel("mean opponent displacement (court coord units)")
ax.set_ylabel("shot type")
ax.set_title("Which shot types force the opponent to move the most?")

## annotate each bar with the sample size
for i, (val, n) in enumerate(zip(disp_by_type["mean_displacement"], disp_by_type["n"])):
    ax.text(val, i, f"  n={n}", va="center", fontsize=8, color="dimgray")

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "mean_displacement_by_shot.png"), dpi=150)
plt.close()
print("saved output/mean_displacement_by_shot.png")

print()
print("=== displacement-by-shot-type table ===")
print(disp_by_type.round(2))
print()

## ============================================================
## FIGURE 3: CUMULATIVE DISPLACEMENT OVER RALLY, WINNERS VS LOSERS
## (does the rally winner consistently apply more pressure over time?)
## ============================================================

## for each stroke, compute cumulative displacement applied BY THE HITTER
## across that rally up to that point
## key: we want displacement per player per rally, accumulated by ball_round
disp_df = strokes.dropna(subset=["displacement"]).copy()
disp_df = disp_df.sort_values(["match_id", "set_num", "rally", "ball_round"])

## cumulative displacement applied by each (rally, hitter) pair
disp_df["cum_disp_by_hitter"] = (
    disp_df.groupby(["match_id", "set_num", "rally", "player"])["displacement"]
    .cumsum()
)

## label: did this hitter win this rally?
## (already computed in step 02 as `hitter_won_rally`)
## now collapse: for each (rally, hitter) and each ball_round, what's the cum disp?
## then average across rallies, split by whether the hitter won

## bin by ball_round to get a curve
## cap ball_round at 20 since beyond that, sample size drops sharply
disp_df["ball_round_capped"] = disp_df["ball_round"].clip(upper=20)

curve = (
    disp_df.groupby(["ball_round_capped", "hitter_won_rally"])["cum_disp_by_hitter"]
    .mean()
    .reset_index()
)

## pivot for plotting
curve_pivot = curve.pivot(index="ball_round_capped",
                         columns="hitter_won_rally",
                         values="cum_disp_by_hitter")
curve_pivot.columns = ["lost rally", "won rally"]  ## False, True -> labels

fig, ax = plt.subplots(figsize=(10, 6))
curve_pivot.plot(ax=ax, marker="o", linewidth=2)
ax.set_xlabel("ball round (stroke number in rally)")
ax.set_ylabel("mean cumulative displacement applied by hitter")
ax.set_title("Do rally winners apply more cumulative pressure on the opponent?")
ax.legend(title="rally outcome for hitter")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "displacement_winners_vs_losers.png"), dpi=150)
plt.close()
print("saved output/displacement_winners_vs_losers.png")

print()
print("=== curve values ===")
print(curve_pivot.round(2))
print()

## ============================================================
## SECTION: SUMMARY TABLE
## ============================================================

summary = pd.DataFrame({
    "metric": [
        "total strokes",
        "total rallies",
        "total matches",
        "mean displacement (all strokes)",
        "mean displacement (rallies won by hitter)",
        "mean displacement (rallies lost by hitter)",
    ],
    "value": [
        len(strokes),
        strokes.groupby(["match_id", "set_num", "rally"]).ngroups,
        strokes["match_id"].nunique(),
        round(strokes["displacement"].mean(), 2),
        round(strokes.loc[strokes["hitter_won_rally"] == True, "displacement"].mean(), 2),
        round(strokes.loc[strokes["hitter_won_rally"] == False, "displacement"].mean(), 2),
    ],
})

summary.to_csv(os.path.join(OUT_DIR, "summary_stats.csv"), index=False)
print("=== summary ===")
print(summary.to_string(index=False))
print()
print("saved output/summary_stats.csv")
