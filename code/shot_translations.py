## shot_translations.py
## Chinese to English mapping for the 18 shot types in ShuttleSet22.
## Source: official README in the upstream repo.
## Imported by 02_clean_encode.py.

SHOT_TYPE_MAP = {
    "放小球": "net shot",
    "擋小球": "return net",
    "殺球": "smash",
    "點扣": "wrist smash",
    "挑球": "lob",
    "防守回挑": "defensive return lob",
    "長球": "clear",
    "平球": "drive",
    "小平球": "driven flight",
    "後場抽平球": "back-court drive",
    "切球": "drop",
    "過渡切球": "passive drop",
    "過度切球": "passive drop",  ## typo variant found in raw data (度 vs 渡)
    "推球": "push",
    "撲球": "rush",
    "防守回抽": "defensive return drive",
    "勾球": "cross-court net shot",
    "發短球": "short service",
    "發長球": "long service",
    "未知球種": "unknown",        ## dataset's own placeholder for unclassified shots
}
