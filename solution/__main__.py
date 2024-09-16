import numpy as np
import torch
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import matthews_corrcoef, precision_score, accuracy_score, f1_score, recall_score

from solution.args import read_args
from solution.data import get_data, partition_data
from solution.model import Model, train, evaluate
from solution.custom_random_forest import CustomRandomForest
from solution.metrics import Metrics

TEST_SIZE = 0.2

if __name__ == "__main__":
    seed, epochs, batch_size, folds, path = read_args()

    torch.manual_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else
                          "mps" if torch.backends.mps.is_available() else "cpu")

    print(f"Starting training with seed {seed}, {epochs} epochs, {batch_size} batch size, {folds} folds")
    print(f"Using device: {device}")

    # Read data
    X, Y = get_data(path)

    # Prepare metrics
    metric_calculator = {"accuracy": lambda true, predicted: accuracy_score(true, predicted),
                         "mcc": lambda true, predicted: matthews_corrcoef(true, predicted),
                         "precision_macro": lambda true, predicted: precision_score(true, predicted, average='macro'),
                         "precision_micro": lambda true, predicted: precision_score(true, predicted, average='micro'),
                         "precision_weighted": lambda true, predicted: precision_score(true, predicted, average='weighted'),
                         "f1_macro": lambda true, predicted: f1_score(true, predicted, average='macro'),
                         "f1_micro": lambda true, predicted: f1_score(true, predicted, average='micro'),
                         "f1_weighted": lambda true, predicted: f1_score(true, predicted, average='weighted'),
                         "recall_macro": lambda true, predicted: recall_score(true, predicted, average='macro'),
                         "recall_micro": lambda true, predicted: recall_score(true, predicted, average='micro'),
                         "recall_weighted": lambda true, predicted: recall_score(true, predicted, average='weighted')}
    metrics = Metrics(metric_calculator.keys())

    kf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    for fold, (train_idx, val_idx) in enumerate(kf.split(Y, Y.argmax(axis=1))):
        print(f"Fold {fold + 1}")

        # Divide the training set into training and validation sets
        X_train, Y_train = partition_data(X, train_idx), Y[train_idx,]
        X_val, Y_val = partition_data(X, val_idx), Y[val_idx,]

        # Evaluate random forest
        forest = CustomRandomForest(random_state=seed)
        forest.fit(X_train["metrics"], Y_train.argmax(axis=1).astype(str))
        X_train["metrics"] = forest.predict_proba(X_train["metrics"]).astype(np.float32)
        X_val["metrics"] = forest.predict_proba(X_val["metrics"]).astype(np.float32)

        # Prepare model
        model = Model(X_train["metrics"].shape[1]).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5, eps=1e-7)

        # Train the model
        train(model, device, optimizer, epochs, batch_size, X_train, Y_train, X_val, Y_val)

        # Evaluate the model
        results = evaluate(model, device, X_val, Y_val, metric_calculator)
        metrics.append(**results)

    metrics.print_all_values()
    metrics.print()
