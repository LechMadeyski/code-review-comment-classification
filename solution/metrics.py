import numpy as np


class Metrics:
    def __init__(self, metrics):
        self.metrics = {metric: [] for metric in metrics}

    def append(self, **kwargs):
        for metric in self.metrics:
            self.metrics[metric].append(kwargs[metric])

    def print_all_values(self):
        for name, values in self.metrics.items():
            for i, value in enumerate(values):
                print(f"Fold:{i}, {name}: value: {value}")

    def print(self):
        for name, values in self.metrics.items():
            print(f"Average {name}: {np.mean(values)}")
            print(f"{name} standard deviation: {np.std(values)}")
            print(f"{name} standard error: {np.std(values, ddof=1) / np.sqrt(len(values))}")
