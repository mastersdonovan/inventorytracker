import json
import os
import matrix
import numpy as np

DATA_FILE = os.path.join(os.path.dirname(__file__), "optimization_data.json")


class Optimization:
    def __init__(self, A, b, filepath=DATA_FILE):
        self.filepath = filepath
        self.A = matrix.Matrix(A)
        self.b = np.array(b, dtype=float)
        self._save()

    def add_week(self, week_data):
        self.A = matrix.Matrix(np.vstack((self.A.to_numpy(), week_data[:-1])))
        self.b = np.hstack((self.b, week_data[-1]))
        self._save()

    def update_previous_week(self, week_index, week_data):
        self.A = matrix.Matrix(np.vstack((
            self.A.to_numpy()[:week_index],
            week_data[:-1],
            self.A.to_numpy()[week_index + 1:]
        )))
        self.b = np.hstack((self.b[:week_index], week_data[-1], self.b[week_index + 1:]))
        self._save()

    def remove_week(self, week_index):
        self.A = matrix.Matrix(np.vstack((
            self.A.to_numpy()[:week_index],
            self.A.to_numpy()[week_index + 1:]
        )))
        self.b = np.hstack((self.b[:week_index], self.b[week_index + 1:]))
        self._save()

    def get_optimal_x(self):
        return self.A.leastSquares(self.b)

    @classmethod
    def load(cls, filepath=DATA_FILE):
        """Reconstruct an Optimization instance from a saved JSON file."""
        with open(filepath) as f:
            data = json.load(f)
        instance = object.__new__(cls)
        instance.filepath = filepath
        instance.A = matrix.Matrix(data["A"])
        instance.b = np.array(data["b"], dtype=float)
        return instance

    def _save(self):
        payload = {
            "A": self.A.to_numpy().tolist(),
            "b": self.b.tolist(),
        }
        with open(self.filepath, "w") as f:
            json.dump(payload, f, indent=2)
