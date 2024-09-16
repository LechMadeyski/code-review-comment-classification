import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.discriminant_analysis import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, VarianceThreshold
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.svm import SVC
from catboost import CatBoostClassifier

from features.comment_groups import add_comment_group_metrics
from simple.evaluation import evaluate

SEED = 1
EXCLUDED_COLS = ["meta.comment_id", "meta.url", "meta.label",
                 "meta.start_line", "meta.end_line", "comment.text",
                 "comment.side", "code.range.text", "code.context.text"]
LABEL_COL = "meta.label"


def main() -> None:
    df = pd.read_excel("dataset.xlsx")
    add_comment_group_metrics(df)
    X = df.drop(columns=EXCLUDED_COLS).to_numpy()
    y = df[LABEL_COL].astype("category")

    model = Pipeline([
        ("pre", make_pipeline(
            VarianceThreshold(),
            StandardScaler(),
            SelectKBest(k=50)
        )),
        ("clf", BaseEstimator())
    ])

    grid = GridSearchCV(
        estimator=model,
        scoring="accuracy",
        verbose=50,
        n_jobs=-1,
        param_grid=[
            {
                "clf": [RandomForestClassifier()],
                "clf__random_state": [SEED],
                "clf__n_jobs": [-1],

                "clf__n_estimators": [50, 100, 250, 500],
                "clf__criterion": ["gini", "entropy"],
                "clf__max_depth": [3, 6, 9, None],
                "clf__max_features": ["sqrt", "log2", None]
            },
            {
                "clf": [SVC()],
                "clf__random_state": [SEED],

                "clf__C": [0.1, 1, 10, 100],
                "clf__kernel": ["poly", "rbf", "sigmoid"],
                "clf__gamma": ["scale", "auto"]
            },
            {
                "clf": [CatBoostClassifier()],
                "clf__random_state": [SEED],
                "clf__verbose": [False],
                "clf__allow_writing_files": [False],
            }
        ])

    grid.fit(X, y)
    res = pd.DataFrame(grid.cv_results_)[["params", "mean_test_score"]
                                         ].sort_values("mean_test_score", ascending=False).head(10)
    for _, r in res.iterrows():
        print(f"{r['params']} -> {r['mean_test_score']:.2f}")
    clf = grid.best_estimator_
    evaluate(pd.DataFrame(X), y, lambda: clf, random_state=SEED)


if __name__ == "__main__":
    main()
