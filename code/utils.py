## utils.py
## Shared helper functions imported by the analysis notebooks.
## Keeping these in one place avoids repeating the same data-prep logic
## (loading strokes, mapping A/B codes to player names, restricting to one sex)
## across notebooks 04, 06, 07, 08, 09, and 11.

import os
import numpy as np
import pandas as pd

## ------------------------------------------------------------
## PATHS
## All paths are relative to the repo root, so the notebooks must be run
## with the repo root as the working directory. No absolute paths anywhere.
## ------------------------------------------------------------

RAW_DIR = "data/raw"
PROC_DIR = "data/processed"
OUT_DIR = "output"


def ensure_dirs():
    """Create the processed-data and output directories if they don't exist."""
    os.makedirs(PROC_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)


def load_strokes():
    """Load the cleaned long-format stroke table produced by 02_clean_encode."""
    path = os.path.join(PROC_DIR, "strokes_all.csv")
    strokes = pd.read_csv(path)
    return strokes


def load_matches():
    """Load match-level metadata (winner/loser names, tournament, round)."""
    return pd.read_csv(os.path.join(RAW_DIR, "match.csv"))


def map_player_names(strokes, matches):
    """Resolve the per-match 'A'/'B' player codes to real player names.

    In the raw data the `player` column is 'A' or 'B' within each match, where
    'A' is the match winner and 'B' is the match loser (per the upstream
    README). This merges the winner/loser names from match.csv onto every
    stroke and creates a `player_name` column.

    Prints row counts before and after the merge (rubric: diagnostics around
    merges). The merge is a left join on match_id, so the stroke count must
    not change; the assert guards against an accidental fan-out.
    """
    n_before = len(strokes)
    strokes = strokes.merge(
        matches[["id", "winner", "loser"]].rename(columns={"id": "match_id"}),
        on="match_id",
        how="left",
        suffixes=("", "_m"),
    )
    n_after = len(strokes)
    print(f"map_player_names: rows before merge = {n_before}, after = {n_after}")
    assert n_after == n_before, "row count changed during player-name merge (unexpected fan-out)"

    strokes["player_name"] = np.where(
        strokes["player"] == "A", strokes["winner"], strokes["loser"]
    )
    print(f"map_player_names: unique players resolved = {strokes['player_name'].nunique()}")
    return strokes


def restrict_to_womens(strokes, how="sex"):
    """Restrict strokes to women's-singles players.

    how='sex'      -> use data/processed/player_sex.csv (sex == 'W')
    how='clusters' -> use data/processed/player_clusters_W.csv (the clustered
                      women's players; identical membership, but this is what
                      some notebooks keyed on)

    Prints row counts before and after the filter.
    """
    n_before = len(strokes)
    if how == "clusters":
        ref = pd.read_csv(os.path.join(PROC_DIR, "player_clusters_W.csv"))
        womens = set(ref["player_name"])
    else:
        sex = pd.read_csv(os.path.join(PROC_DIR, "player_sex.csv"))
        womens = set(sex[sex["sex"] == "W"]["player_name"])
    strokes = strokes[strokes["player_name"].isin(womens)].copy()
    print(f"restrict_to_womens: rows before filter = {n_before}, after = {len(strokes)}")
    return strokes


def add_rally_sequence(strokes, min_shots=None, rally_keys=("match_id", "set_num", "rally")):
    """Sort strokes within each rally and add sequence indices.

    Adds:
      rally_len -> number of shots in the rally
      seq       -> 0-based index from the start of the rally
      from_end  -> 0 = last shot, 1 = penultimate, 2 = before that, ...

    Optionally drops rallies shorter than `min_shots`.
    """
    rally_keys = list(rally_keys)
    strokes = strokes.sort_values(rally_keys + ["ball_round"]).copy()
    g = strokes.groupby(rally_keys)
    strokes["rally_len"] = g["ball_round"].transform("size")
    strokes["seq"] = g.cumcount()
    strokes["from_end"] = strokes["rally_len"] - 1 - strokes["seq"]
    if min_shots is not None:
        strokes = strokes[strokes["rally_len"] >= min_shots].copy()
    return strokes
