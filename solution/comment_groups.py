import pandas as pd

COMMENT_COL = "comment.text"
COMMENT_GROUPS = [
    # Fregnan et al.
    ["comment", "style", "messag", "string", "log", "error", "read"],
    ["method", "scope", "enum", "tag", "call"],
    ["return"],
    ["chang", "remov", "miss", "order", "delet", "sort"],
    ["final"],
    ["test", "bug"],
    ["implement", "ad"],
    # Conventional comments
    ["praise"],
    ["nit", "quibble"],
    ["suggest", "polish"],
    ["issue"],
    ["todo", "typo"],
    ["question"],
    ["thought"],
    ["chore"],
    ["note"],
]


def add_comment_group_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for group in COMMENT_GROUPS:
        df[f"{COMMENT_COL}.group.{'-'.join(group)}"] = df.apply(
            lambda row: sum(row[COMMENT_COL].lower().count(kw) for kw in group),
            axis=1
        )
    return df
