import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.compose import make_column_selector, make_column_transformer
from sklearn.discriminant_analysis import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, VarianceThreshold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from imblearn.base import BaseSampler
from imblearn.over_sampling import RandomOverSampler, SMOTE, ADASYN
from imblearn.combine import SMOTETomek, SMOTEENN
from supervised.automl import AutoML

from features.comment_groups import add_comment_group_metrics
from simple.evaluation import evaluate

SEED = 1
META_COLS = ["meta.comment_id", "meta.url", "meta.label", "meta.start_line", "meta.end_line"]
LABEL_COL = "meta.label"
TEXTUAL_COL = "comment.text"
CATEGORICAL_COLS = ["comment.side"]


def load_dataset() -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_excel("dataset.xlsx")
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    add_comment_group_metrics(df)
    return df.drop(columns=META_COLS), df[LABEL_COL]


class Simple(BaseEstimator):
    def __init__(self) -> None:
        self._pipeline = make_pipeline(
            make_column_transformer(
                (OneHotEncoder(), CATEGORICAL_COLS),
                (TfidfVectorizer(stop_words="english", sublinear_tf=True), TEXTUAL_COL),
                (StandardScaler(), make_column_selector(dtype_include="number")),
            ),
            VarianceThreshold(),
            SelectKBest(k=32),
            RandomForestClassifier(random_state=SEED),
        )

    def fit(self, X, y):
        self._pipeline.fit(X, y)
        return self

    def predict(self, X):
        return self._pipeline.predict(X)


class Sampled(Simple):
    def __init__(self, sampler: BaseSampler) -> None:
        self._sampler = sampler
        self._pipeline = make_pipeline(
            StandardScaler(),
            VarianceThreshold(),
            SelectKBest(k=32),
            RandomForestClassifier(random_state=SEED),
        )

    def fit(self, X, y):
        X = Sampled._numericize(X)
        X, y = self._sampler.fit_resample(X, y)
        return super().fit(X, y)

    def predict(self, X):
        return super().predict(Sampled._numericize(X))

    @staticmethod
    def _numericize(X):
        X = X.copy()
        for col in CATEGORICAL_COLS:
            X[col] = X[col].astype("category").cat.codes
        return X.select_dtypes([np.number])


def main():
    X, y = load_dataset()

    print("Evaluating base:")
    evaluate(X, y, Simple, random_state=SEED)

    for Sampler in [RandomOverSampler, SMOTE, ADASYN, SMOTETomek, SMOTEENN]:
        print(f"Evaluating oversampling with {Sampler.__name__}:")
        evaluate(X, y, lambda: Sampled(sampler=Sampler(random_state=SEED)), random_state=SEED)

    for percent in range(25, 101, 25):
        n = int(len(X) * percent / 100)
        print(f"Evaluating base with {n=}:")
        evaluate(X.head(n), y.head(n), Simple, random_state=SEED)

    for mode in ["Perform", "Compete", "Optuna"]:
        print(f"Evaluating AutoML with {mode=}:")
        evaluate(X, y, lambda: AutoML(mode=mode, max_single_prediction_time=None, random_state=SEED), random_state=SEED)


if __name__ == "__main__":
    main()
