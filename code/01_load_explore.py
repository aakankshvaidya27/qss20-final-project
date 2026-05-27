## 01_load_explore.py
## Load match-level metadata and confirm the dataset structure.
## Prints basic counts and the matchup-frequency table.
## Saves a small summary CSV to data/processed/ for use later.

import os
import pandas as pd

## ============================================================
## SECTION 1: LOAD MATCH METADATA
## ============================================================

RAW_DIR = "data/raw"
SET_DIR = os.path.join(RAW_DIR, "set")
PROC_DIR = "data/processed"

## load match.csv
matches = pd.read_csv(os.path.join(RAW_DIR, "match.csv"))

print("=== match.csv loaded ===")
print("shape:", matches.shape)
print("columns:", list(matches.columns))
print()
print(matches.head())
print()

## ============================================================
## SECTION 2: BASIC COUNTS
## ============================================================

n_matches = len(matches)
players = pd.unique(matches[["winner", "loser"]].values.ravel())
n_players = len(players)

print("=== basic counts ===")
print("number of matches:", n_matches)
print("number of unique players:", n_players)
print()

## ============================================================
## SECTION 3: MATCHUP FREQUENCY
## (which pairs of players play each other most often)
## ============================================================

## build a normalized (player1, player2) tuple where order doesn't matter
def matchup_pair(row):
    a, b = row["winner"], row["loser"]
    return tuple(sorted([a, b]))

matches["matchup"] = matches.apply(matchup_pair, axis=1)
matchup_counts = matches["matchup"].value_counts().reset_index()
matchup_counts.columns = ["matchup", "n_matches"]

print("=== top matchups (most repeated) ===")
print(matchup_counts.head(10))
print()

## ============================================================
## SECTION 4: COUNT SET FILES PER MATCH
## (each match folder has set1.csv, set2.csv, sometimes set3.csv)
## ============================================================

set_folders = [f for f in os.listdir(SET_DIR) if os.path.isdir(os.path.join(SET_DIR, f))]
print("=== set/ folder contents ===")
print("number of match folders:", len(set_folders))

## count set CSVs in each match folder
set_file_counts = []
for folder in set_folders:
    folder_path = os.path.join(SET_DIR, folder)
    csvs = [f for f in os.listdir(folder_path) if f.startswith("set") and f.endswith(".csv")]
    set_file_counts.append({"match_folder": folder, "n_set_files": len(csvs)})

set_files_df = pd.DataFrame(set_file_counts)
print("distribution of set files per match:")
print(set_files_df["n_set_files"].value_counts().sort_index())
print()

## ============================================================
## SECTION 5: PEEK AT ONE STROKE-LEVEL FILE
## ============================================================

## pick the first match folder and load its set1.csv
sample_folder = set_folders[0]
sample_set_path = os.path.join(SET_DIR, sample_folder, "set1.csv")
sample_strokes = pd.read_csv(sample_set_path)

print("=== sample stroke-level file ===")
print("path:", sample_set_path)
print("shape:", sample_strokes.shape)
print("columns:", list(sample_strokes.columns))
print()
print(sample_strokes.head(3))
print()

## ============================================================
## SECTION 6: SAVE A SUMMARY FOR LATER SCRIPTS
## ============================================================

os.makedirs(PROC_DIR, exist_ok=True)
matchup_counts.to_csv(os.path.join(PROC_DIR, "matchup_counts.csv"), index=False)
set_files_df.to_csv(os.path.join(PROC_DIR, "set_files_per_match.csv"), index=False)

print("=== saved ===")
print("- data/processed/matchup_counts.csv")
print("- data/processed/set_files_per_match.csv")
