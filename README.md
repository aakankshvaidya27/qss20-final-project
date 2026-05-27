# Spatial Pressure in Badminton Rallies

QSS 20 Final Project — Milestone 2
Aakanksh Vaidya

## What this project is

I'm using stroke-level badminton data from elite men's and women's singles matches to ask whether forcing the opponent to move more (spatial pressure) is associated with winning rallies. The original idea was to treat rallies as sequences of shot types and look for common tactical patterns, but I shifted away from that because shot-type labels on their own don't really tell you much about strategy — they ignore where the shuttle actually goes and how far the opponent has to move to reach it. So this milestone reframes the analysis around spatial pressure instead.

## Data

The data comes from ShuttleSet22 (Wang et al., 2023, arXiv:2306.15664), which I pulled from the [upstream repo](https://github.com/wywyWang/CoachAI-Projects/tree/main/CoachAI-Challenge-IJCAI2023/ShuttleSet22). It covers 58 matches and 35 elite singles players from 2020–2022, for a total of 52,356 strokes across 4,944 rallies. Every stroke has the shot type (originally in Chinese), the hitter and opponent court positions, where the shuttle landed, and how the rally eventually ended.

The raw files live in `data/raw/`. I kept the original upstream README and preprocessing script in that folder too for reference.

## How to run

```bash
pip install -r requirements.txt
python code/01_load_explore.py
python code/02_clean_encode.py
python code/03_analyze_spatial.py
```

The scripts have to run in order — script 02 builds the processed stroke table that script 03 reads from.

## Repo layout

```
qss20_final_project/
├── README.md
├── requirements.txt
├── .gitignore
├── code/
│   ├── shot_translations.py
│   ├── 01_load_explore.py
│   ├── 02_clean_encode.py
│   └── 03_analyze_spatial.py
├── data/
│   ├── raw/
│   └── processed/
└── output/
```

## What each script does

`shot_translations.py` is just a dictionary that maps the 18 Chinese shot type labels in the data to English (using the translation table from the upstream README). I added two extra entries: one for a typo variant in the raw data (`過度切球` instead of `過渡切球`, both mapped to `passive drop`), and one for the dataset's own `未知球種` placeholder for unclassified shots.

`01_load_explore.py` loads `match.csv` and prints basic stats — 58 matches, 35 players, the most repeated matchups (Yamaguchi vs An Se Young played 4 times, CHEN Yufei vs HE Bingjiao 3 times), and a breakdown of how many sets each match went (34 went 2 sets, 24 went 3). It's mostly a sanity check that the data loaded right.

`02_clean_encode.py` does the actual data work. It walks every match folder, stitches together every `set{1,2,3}.csv` into one long table where each row is a single stroke, and adds three derived columns:

- `shot_type` — English shot type from the dictionary
- `displacement` — Euclidean distance from where the opponent was standing to where the shuttle landed. This is the core metric of the project: how far the opponent had to move to reach each shot.
- `hitter_won_rally` — whether the player who hit this stroke ended up winning the rally. The raw data only records the rally winner on the last stroke, so I forward/back-fill that label across every stroke in the rally.

The output is `data/processed/strokes_all.csv` with all 52,356 strokes.

`03_analyze_spatial.py` reads that processed table and produces three figures plus a summary stats CSV.

## Findings

### Figure 1 — Shot frequency

Just a descriptive baseline of how often each shot type shows up. Net shots, lobs, and return-nets are the most common; services and defensive returns are the least.

### Figure 2 — Mean opponent displacement by shot type

For each shot type, the average distance the opponent had to move to reach the shot. This reframes shot selection from "how often is this shot hit" to "how much does it actually move the opponent."

The result that stood out to me: cross-court net shots and return-nets generate the highest mean displacement (around 210 and 186 units), while services are lowest (around 70). Smashes — which I'd have guessed would top the list — sit in the middle at around 150. The reason that makes sense is that smashes travel hard but down the line, while cross-court shots force the opponent to cover lateral distance, which is usually further than the depth they already need to cover.

### Figure 3 — Cumulative displacement, winners vs losers

This is the actual test of the pressure hypothesis. For each rally, I tracked the cumulative displacement each player applied over the course of the rally, then averaged across rallies and split by whether the hitter eventually won.

The two curves are basically identical at every rally length. Mean displacement applied by rally winners is 155.46 units, by losers is 156.44. So at the aggregate level, applying more cumulative spatial pressure does not predict who wins the rally.

I want to be honest that this is a null result and that the simple version of the hypothesis didn't hold. A few reasons I think it could be coming out null:

- Pressure in a rally is mutual — if both players are hitting good shots, both accumulate displacement, and totals wash out.
- The distribution probably matters more than the mean. One or two decisive high-pressure shots could matter more than steady pressure throughout the rally.
- Cumulative across the whole rally averages the decisive end with the neutral middle, which dilutes whatever signal is there.
- The hitter's own court position probably matters too — pulling the opponent wide doesn't help much if you're also out of position.

## Summary stats (`output/summary_stats.csv`)

| metric                                    | value |
|-------------------------------------------|-------|
| total strokes                             | 52,356 |
| total rallies                             | 4,944  |
| total matches                             | 58     |
| mean displacement (all strokes)           | 155.96 |
| mean displacement (rallies won by hitter) | 155.46 |
| mean displacement (rallies lost by hitter)| 156.44 |

## Possible directions from here

A few directions I'm considering for where to take this next. I'll be making a decision on which to pursue soon.

The first is to look at the *setup* stroke before the rally-ending shot rather than the last stroke itself. Last-stroke displacement is partly an artifact of the rally ending — once the opponent can't reach the shot, you can place it almost anywhere — so the more informative question is whether displacement on the stroke that *created the opening* is higher for eventual winners.

The second is to plot per-stroke (not cumulative) displacement across the rally and see if there's a point where the winner and loser curves actually diverge. If they do diverge, where that happens would tell me when the rally actually gets decided.

A third would be to stratify by shot type. A high-displacement smash and a high-displacement cross-court net shot are doing different tactical work, and lumping them together might be hiding a real signal.

A fourth, more ambitious one would be to cluster the 35 players using their shot distributions and average court positions to get a data-driven player typology — attacking, control, defensive — and then test whether displacement predicts rally wins differently depending on the hitter-opponent style matchup. This is the most interesting direction to me but also the most time-consuming.

A fifth would be to add the hitter's own positional context — whether they're in a controlled or scrambling position when they hit — as a second spatial variable.

Right now I'm leaning toward combining the first two (setup-stroke and divergence-point analysis) as the core of the final paper, treating the cumulative null as the motivating finding. I'll bring this to my next meeting with the professor to decide.

## A note on the coordinates

The displacement values are in the dataset's native coordinate system (camera pixels, not meters). The dataset does include a homography matrix that maps to real-world coordinates, but I haven't applied it yet. So all the displacement comparisons here are relative — "smashes generate around 2× the displacement of drives" is fine to say, but "the opponent ran 1.5 meters" isn't. Converting to real units is straightforward and something I'll do if it matters for the final paper.

## Citation

Wei-Yao Wang, Wei-Wei Du, and Wen-Chih Peng. *ShuttleSet22: Benchmarking Stroke Forecasting with Stroke-Level Badminton Dataset.* arXiv:2306.15664, 2023.
