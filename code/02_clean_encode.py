## 02_clean_encode.py
## Load every stroke from every set file across all matches.
## Translate shot types, compute opponent displacement, attach rally outcome.
## Save the processed long-format stroke table to data/processed/strokes_all.csv.

import os
import sys
import numpy as np
import pandas as pd

## let this script import shot_translations.py which lives in the same code/ folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shot_translations import SHOT_TYPE_MAP

## ============================================================
## SECTION 1: PATHS
## ============================================================

RAW_DIR = "data/raw"
SET_DIR = os.path.join(RAW_DIR, "set")
PROC_DIR = "data/processed"
os.makedirs(PROC_DIR, exist_ok=True)

## load match metadata so we can join winner/loser names onto strokes
matches = pd.read_csv(os.path.join(RAW_DIR, "match.csv"))

## the match.csv `video` column equals the folder name in set/
## so we can match folder -> match row via that column
matches_lookup = matches.set_index("video")[["id", "winner", "loser", "tournament", "round"]]

## ============================================================
## SECTION 2: WALK SET FOLDERS AND CONCATENATE ALL STROKES
## ============================================================

set_folders = [f for f in os.listdir(SET_DIR) if os.path.isdir(os.path.join(SET_DIR, f))]

all_strokes = []
skipped_folders = []

for folder in set_folders:
    folder_path = os.path.join(SET_DIR, folder)

    ## skip if this folder isn't in match.csv (defensive check)
    if folder not in matches_lookup.index:
        skipped_folders.append(folder)
        continue

    match_info = matches_lookup.loc[folder]

    ## load every set file in this folder (set1.csv, set2.csv, optionally set3.csv)
    set_files = sorted([f for f in os.listdir(folder_path) if f.startswith("set") and f.endswith(".csv")])
    for sf in set_files:
        set_num = int(sf.replace("set", "").replace(".csv", ""))
        df = pd.read_csv(os.path.join(folder_path, sf))

        ## tag each stroke with its match identity
        df["match_video"] = folder
        df["match_id"] = match_info["id"]
        df["match_winner"] = match_info["winner"]
        df["match_loser"] = match_info["loser"]
        df["tournament"] = match_info["tournament"]
        df["round"] = match_info["round"]
        df["set_num"] = set_num

        all_strokes.append(df)

strokes = pd.concat(all_strokes, ignore_index=True)

print("=== concatenated stroke data ===")
print("shape:", strokes.shape)
print("matches loaded:", strokes["match_id"].nunique())
print("skipped folders (not in match.csv):", len(skipped_folders))
if skipped_folders:
    print("  examples:", skipped_folders[:3])
print()

## ============================================================
## SECTION 3: TRANSLATE SHOT TYPES TO ENGLISH
## ============================================================

## the `type` column is in Chinese; map to English using the upstream README
strokes["shot_type"] = strokes["type"].map(SHOT_TYPE_MAP)

## report any unmapped values (should be empty if the translation map is complete)
unmapped = strokes[strokes["shot_type"].isna() & strokes["type"].notna()]["type"].unique()
print("=== shot type translation ===")
print("unique raw shot types:", strokes["type"].nunique())
print("translated successfully:", strokes["shot_type"].notna().sum())
print("unmapped values:", list(unmapped) if len(unmapped) > 0 else "none")
print()

## ============================================================
## SECTION 4: COMPUTE OPPONENT DISPLACEMENT
## (how far the receiving opponent had to move from their position
## to reach the shuttle landing point)
## ============================================================

## euclidean distance between opponent location and shuttle landing point
## note: coordinates are in the camera/court coordinate system from the dataset.
## we treat this as a relative measure, not an absolute distance in meters.
strokes["displacement"] = np.sqrt(
    (strokes["opponent_location_x"] - strokes["landing_x"]) ** 2
    + (strokes["opponent_location_y"] - strokes["landing_y"]) ** 2
)

print("=== displacement summary ===")
print(strokes["displacement"].describe())
print()

## ============================================================
## SECTION 5: ATTACH RALLY OUTCOME TO EVERY STROKE
## (getpoint_player is recorded only on the last stroke of each rally;
##  we want every stroke in the rally to know who won that rally)
## ============================================================

## within each (match, set, rally) group, forward+backward fill getpoint_player
## so every stroke in the rally carries the winner of that rally
strokes["rally_winner"] = (
    strokes.groupby(["match_id", "set_num", "rally"])["getpoint_player"]
    .transform(lambda s: s.ffill().bfill())
)

## the player column is "A" or "B" where A is the match winner
## getpoint_player is also "A" or "B"
## so rally_winner_is_match_winner = (rally_winner == "A")
strokes["rally_winner_is_match_winner"] = strokes["rally_winner"] == "A"

## did the player who hit THIS stroke end up winning the rally?
strokes["hitter_won_rally"] = strokes["player"] == strokes["rally_winner"]

print("=== rally outcome attachment ===")
print("strokes with a rally_winner:", strokes["rally_winner"].notna().sum(), "/", len(strokes))
print("share where hitter won the rally:", strokes["hitter_won_rally"].mean().round(3))
print()

## ============================================================
## SECTION 6: SAVE PROCESSED OUTPUT
## ============================================================

## keep a focused set of columns for downstream analysis
keep_cols = [
    "match_id", "match_video", "tournament", "round",
    "match_winner", "match_loser",
    "set_num", "rally", "ball_round",
    "player", "server", "type", "shot_type",
    "hit_area", "hit_x", "hit_y",
    "landing_area", "landing_x", "landing_y",
    "player_location_area", "player_location_x", "player_location_y",
    "opponent_location_area", "opponent_location_x", "opponent_location_y",
    "displacement",
    "lose_reason", "win_reason", "getpoint_player",
    "rally_winner", "hitter_won_rally",
]

## only keep cols that actually exist (defensive)
keep_cols = [c for c in keep_cols if c in strokes.columns]
strokes_out = strokes[keep_cols].copy()

out_path = os.path.join(PROC_DIR, "strokes_all.csv")
strokes_out.to_csv(out_path, index=False)

print("=== saved ===")
print("rows:", len(strokes_out))
print("path:", out_path)
