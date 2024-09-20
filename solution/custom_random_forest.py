
from sklearn.base import BaseEstimator
from sklearn.discriminant_analysis import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, VarianceThreshold
from sklearn.pipeline import make_pipeline


class CustomRandomForest(BaseEstimator):
    def __init__(self, random_state: int = None) -> None:
        self._pipeline = make_pipeline(
            VarianceThreshold(),
            StandardScaler(),
            SelectKBest(k=50),
            RandomForestClassifier(n_estimators=250, random_state=random_state),
        )

    def fit(self, X, y):
        self._pipeline.fit(X, y)
        return self

    def predict_proba(self, X):
        return self._pipeline.predict_proba(X)
