from typing import Callable
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.metrics import accuracy_score, matthews_corrcoef
from sklearn.model_selection import KFold
from tqdm import tqdm

FOLDS = 10


def evaluate(X: pd.DataFrame, y: pd.Series, model_factory: Callable[[], BaseEstimator], random_state: int | None = None) -> None:
    fold = KFold(n_splits=FOLDS, shuffle=True, random_state=random_state)
    acc_sum, mcc_sum, count = 0, 0, 0
    for train_idx, valid_idx in tqdm(fold.split(X), total=FOLDS, leave=False):
        X_train, y_train = X.loc[train_idx, :], y.loc[train_idx]
        X_valid, y_valid = X.loc[valid_idx, :], y.loc[valid_idx]

        model = model_factory()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_valid)

        acc_sum += accuracy_score(y_valid, y_pred)
        mcc_sum += matthews_corrcoef(y_valid, y_pred)
        count += 1

    print(f"ACC: {acc_sum/count:.3f}, MCC: {mcc_sum/count:.3f}")
