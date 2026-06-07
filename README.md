# Spatial pressure and rally outcomes in elite badminton

QSS 20 final project — Aakanksh Vaidya

Code and analysis testing whether "spatial pressure" (forcing your opponent to
move) decides who wins rallies in elite women's singles badminton, using the
stroke-level ShuttleSet22 dataset. Short version of the finding: it does not.
Cumulative pressure, playstyle, and the winner's setup shot all come up null or
within noise; the rally is decided on the single final shot, which is most often
the trailing player's error.

- **Paper:** `paper/` (PNAS-style LaTeX source and compiled PDF)
- **Website (live demo):** https://aakanksh.netlify.app/badminton/
- **Notebooks:** `code/` (run in numeric order; see below)

# Data

The analysis uses **ShuttleSet22**, a public stroke-level dataset of elite
professional badminton singles matches: 58 matches, 35 players, 2020–2022,
52,356 strokes across 4,944 rallies. The main analysis is restricted to the 13
women's-singles players (~22,500 strokes).

- Source dataset: [ShuttleSet22 (CoachAI-Projects repo)](https://github.com/wywyWang/CoachAI-Projects/tree/main/CoachAI-Challenge-IJCAI2023/ShuttleSet22)
- Dataset paper: Wang, Du, Peng, "ShuttleSet22: Benchmarking Stroke Forecasting with Stroke-Level Badminton Dataset," [arXiv:2306.15664](https://arxiv.org/abs/2306.15664) (2023)

**The raw data is not committed to this repository.** To reproduce, download
ShuttleSet22 from the source above and place it under `data/raw/` so that
`data/raw/match.csv` and `data/raw/set/<match>/set*.csv` exist, then run the
notebooks in order.

Coordinates are in the dataset's camera-derived court-coordinate units, not
meters, so all displacement values are relative.

# Directories

```
code/      analysis notebooks, plus utils.py and shot_translations.py
data/      raw/ (ShuttleSet22 input, not committed) and processed/ (notebook outputs)
output/    figure PNGs and summary CSVs
paper/     LaTeX source and compiled PDF
```

# Shared code

- [code/utils.py](https://github.com/aakankshvaidya27/qss20-final-project/blob/main/code/utils.py) — helpers imported by several notebooks (path constants, `load_strokes`, `load_matches`, `map_player_names` which resolves the A/B player codes to real names with before/after merge diagnostics, `restrict_to_womens`, `add_rally_sequence`).
- [code/shot_translations.py](https://github.com/aakankshvaidya27/qss20-final-project/blob/main/code/shot_translations.py) — dictionary mapping the 18 Chinese shot-type labels to English. Imported by notebook 02; not run on its own.

Every notebook begins with a path-bootstrap cell that locates the repo root (the
folder containing `data/`) and sets the working directory there, so the
notebooks run regardless of where they are launched.

# Order to run

1. [01_load_explore.ipynb](https://github.com/aakankshvaidya27/qss20-final-project/blob/main/code/01_load_explore.ipynb)

- Takes in:
  - `data/raw/match.csv`
  - `data/raw/set/<match>/set*.csv`
- What it does:
  - Loads match metadata, prints basic counts (matches, players)
  - Builds the matchup-frequency table and counts set files per match
  - Peeks at one stroke-level file to confirm the schema
- Outputs:
  - `data/processed/matchup_counts.csv`
  - `data/processed/set_files_per_match.csv`

2. [02_clean_encode.ipynb](https://github.com/aakankshvaidya27/qss20-final-project/blob/main/code/02_clean_encode.ipynb)

- Takes in:
  - `data/raw/match.csv` and all per-set stroke files
  - `code/shot_translations.py`
- What it does:
  - Concatenates every stroke from all 58 matches into one long table
  - Translates Chinese shot-type labels to English
  - Computes opponent `displacement` for every stroke (Euclidean distance from the opponent's position to the shuttle's landing point)
  - Attaches the rally outcome to every stroke by forward/back-filling `getpoint_player` within each rally (a within-group fill, not a join; prints row counts before/after to confirm the count is unchanged)
- Outputs:
  - `data/processed/strokes_all.csv`

3. [03_analyze_spatial.ipynb](https://github.com/aakankshvaidya27/qss20-final-project/blob/main/code/03_analyze_spatial.ipynb)

- Takes in:
  - `data/processed/strokes_all.csv`
- What it does:
  - Produces three descriptive figures: shot frequency, mean displacement by shot type, and cumulative displacement over the rally split by eventual winner vs loser
  - This is the first test of the pressure hypothesis (it comes back null: winner/loser cumulative-displacement curves are nearly identical)
- Outputs:
  - `output/shot_frequency.png`
  - `output/mean_displacement_by_shot.png`
  - `output/displacement_winners_vs_losers.png`
  - `output/summary_stats.csv`

4. [04_player_features.ipynb](https://github.com/aakankshvaidya27/qss20-final-project/blob/main/code/04_player_features.ipynb)

- Takes in:
  - `data/processed/strokes_all.csv`
  - `data/raw/match.csv`
- What it does:
  - Builds a per-player feature vector: shot-type mix, mean depth from court center, mean displacement applied, rally lengths when winning/losing, win rate, share of wins by own-winner vs opponent-error, and landing-spot variance
  - Uses `utils.map_player_names` to resolve A/B codes to real names
- Outputs:
  - `data/processed/player_features.csv`

5. [04b_assign_sex.ipynb](https://github.com/aakankshvaidya27/qss20-final-project/blob/main/code/04b_assign_sex.ipynb)

- Takes in:
  - `data/raw/match.csv`
- What it does:
  - Infers each player's sex (M/W) from match co-occurrence: matches are never mixed-sex, so co-players share a sex; a few known-sex anchors are propagated through the graph of shared matches via BFS
- Outputs:
  - `data/processed/player_sex.csv`

6. [05_cluster_players.ipynb](https://github.com/aakankshvaidya27/qss20-final-project/blob/main/code/05_cluster_players.ipynb)

- Takes in:
  - `data/processed/player_features.csv`
  - `data/processed/player_sex.csv`
- What it does:
  - Hierarchical (Ward-linkage) clustering of players within one sex into k=3 playstyle groups, with a dendrogram, a 2D PCA projection (for visualization only), and per-cluster feature profiles
  - Run once per sex: edit the `SEX` constant at the top of the config cell (`"W"` for women's, `"M"` for men's). Leave it on `"W"` after the final run, since the downstream notebooks use the women's clusters.
- Outputs (with `{SEX}` = `W` or `M`):
  - `data/processed/player_clusters_{SEX}.csv`
  - `output/dendrogram_{SEX}.png`
  - `output/players_pca_{SEX}.png`
  - `output/cluster_profiles_{SEX}.csv`

7. [05b_choose_k.ipynb](https://github.com/aakankshvaidya27/qss20-final-project/blob/main/code/05b_choose_k.ipynb)

- Takes in:
  - `data/processed/player_features.csv`
  - `data/processed/player_sex.csv`
- What it does:
  - Computes silhouette scores across k=2..6 for each sex, to let the data set the number of playstyle groups
  - Finding: women's peaks weakly (~0.22) at k=3; men's never clears the noise floor, so men's clustering is not used downstream
- Outputs:
  - `output/silhouette_by_k.png`

8. [06_conditional_pressure.ipynb](https://github.com/aakankshvaidya27/qss20-final-project/blob/main/code/06_conditional_pressure.ipynb)

- Takes in:
  - `data/processed/strokes_all.csv`
  - `data/processed/player_clusters_W.csv`
  - `data/raw/match.csv`
- What it does:
  - Women's singles only. Logistic regression of rally win on standardized displacement, fit separately within each playstyle cluster, plus an exploratory hitter-by-opponent-style win-rate grid
  - Associational and exploratory, not causal; the clusters are weak so results are read as suggestive. Mostly null.
- Outputs:
  - `output/pressure_by_style.png`
  - `output/pressure_logit_coefs.csv`
  - `output/rally_sample_table.csv`
  - `output/hitter_opponent_winrate.csv`

9. [07_displacement_escalation.ipynb](https://github.com/aakankshvaidya27/qss20-final-project/blob/main/code/07_displacement_escalation.ipynb)

- Takes in:
  - `data/processed/strokes_all.csv`
  - `data/processed/player_clusters_W.csv`
  - `data/raw/match.csv`
- What it does:
  - Tests whether the trajectory of pressure across a rally (slope, last/first ratio, peak timing, final-shot displacement) predicts winning, since the average does not
  - Plots the per-position pressure trajectory used in the paper
- Outputs:
  - `output/escalation_metrics.png`
  - `output/escalation_summary.csv`
  - `output/escalation_logit.csv`
  - `output/pressure_trajectory.png`

10. [08_desperation_check.ipynb](https://github.com/aakankshvaidya27/qss20-final-project/blob/main/code/08_desperation_check.ipynb)

- Takes in:
  - `data/processed/strokes_all.csv`
  - `data/processed/player_clusters_W.csv`
  - `data/raw/match.csv`
- What it does:
  - Women's singles only. Breaks final-stroke displacement down by how the rally ended (own placement winner vs each forced-error type), and as a broad own-winner vs forced-error split
  - Finding: final-shot displacement tracks the ending type, highest on opponent-out, lowest on netted (the netted result is the evidence against a pure geometry explanation)
- Outputs:
  - `output/final_shot_by_reason.csv`
  - `output/final_shot_by_reason.png`

11. [09_attrition_vs_moment.ipynb](https://github.com/aakankshvaidya27/qss20-final-project/blob/main/code/09_attrition_vs_moment.ipynb)

- Takes in:
  - `data/processed/strokes_all.csv`
  - `data/processed/player_clusters_W.csv`
  - `data/raw/match.csv`
- What it does:
  - Women's singles only. Tests attrition (loser progressively pushed out of position) vs single-moment (level until one decisive shot), using the hitter's own distance from court center across the rally and the winner-loser gap
  - Finding: even-execution — the gap is flat with no terminal positional break
- Outputs:
  - `output/attrition_check.png`

12. [11_setup_shot.ipynb](https://github.com/aakankshvaidya27/qss20-final-project/blob/main/code/11_setup_shot.ipynb)

- Takes in:
  - `data/processed/strokes_all.csv`
  - `data/processed/player_sex.csv`
  - `data/raw/match.csv`
- What it does:
  - Women's singles only. Compares the winner's penultimate ("setup") shot to their own rally-wide baseline, reports the share of rallies ending on the loser's racket (~63%), and plots displacement over the final shots
  - Finding: the setup shot is about average for the winner (163 vs 159 baseline); no engineered setup
- Outputs:
  - `output/setup_shot.png`

# Analysis type

Descriptive and exploratory throughout. No causal identification is claimed and
no train-test split is used. Where regressions appear (notebooks 06 and 07) they
are associational; the playstyle clusters are weak (silhouette ~0.22), so
style-conditional results are reported as suggestive only. Differences are judged
against the shot-to-shot standard deviation of displacement (~78 units) rather
than formal significance tests.

# Citation

Wei-Yao Wang, Wei-Wei Du, Wen-Chih Peng. "ShuttleSet22: Benchmarking Stroke
Forecasting with Stroke-Level Badminton Dataset." arXiv:2306.15664 (2023).
