import store
import numpy as np

DEFAULT_ID = "main"


class Optimization:
    def __init__(self, A, b, variables=None, document_id=DEFAULT_ID):
        self.document_id = document_id
        self.A = np.array(A, dtype=float)
        if self.A.ndim != 2:
            raise ValueError("A must be 2-dimensional")
        self.b = np.array(b, dtype=float)
        self.variables = variables or []
        self._save()

# variables
    def get_variables(self):
        return [dict(v) for v in self.variables]

    def add_variable(self, name, unit_cost):
        if len(self.variables) == 0:
            self.A = np.zeros((0, 0))
            self.b = np.zeros(0)
        self.variables.append({"name": name, "unit_cost": unit_cost})
        self.A = np.hstack((self.A, np.zeros((self.A.shape[0], 1))))
        self._save()
        return self.get_variables()

    def update_variable(self, index, name, unit_cost):
        self._check_variable_index(index)
        self.variables[index] = {"name": name, "unit_cost": unit_cost}
        self._save()
        return self.get_variables()

    def remove_variable(self, index):
        self._check_variable_index(index)
        self.variables.pop(index)
        self.A = np.delete(self.A, index, axis=1)
        if len(self.variables) == 0:
            self.clear()
        else:
            self._save()
        return self.get_variables()

    def clear(self):
        """Wipe all recorded weeks. Called when no variables remain, since a
        weeks matrix can't meaningfully exist with zero columns."""
        self.A = np.zeros((0, 0))
        self.b = np.zeros(0)
        self._save()

# weeks
    def get_weeks(self):
        if not self.variables:
            return []
        return [{"units": row, "margin": margin}
                for row, margin in zip(self.A.tolist(), self.b.tolist())]

    def add_week(self, week_data, margin):
        self._check_week_length(week_data)
        self.A = np.vstack((self.A, week_data))
        self.b = np.hstack((self.b, margin))
        self._save()

    def update_week(self, week_index, week_data, margin):
        self._check_week_index(week_index)
        self._check_week_length(week_data)
        self.A[week_index] = week_data
        self.b[week_index] = margin
        self._save()

    def remove_week(self, week_index):
        self._check_week_index(week_index)
        self.A = np.delete(self.A, week_index, axis=0)
        self.b = np.delete(self.b, week_index)
        self._save()

# calculation
    def get_weighted_average(self):
        """Margin-weighted average units per variable across all weeks.
        Falls back to a uniform average if no week has a positive margin."""
        if len(self.b) < 2:
            raise ValueError("Need at least 2 weeks of data to calculate")
        weights = np.maximum(self.b, 0.0)
        if weights.sum() == 0:
            weights = np.ones(len(self.b))
        weights = weights / weights.sum()
        return self.A.T @ weights

# validation
    def _check_variable_index(self, index):
        if index < 0 or index >= len(self.variables):
            raise IndexError("Index out of range")

    def _check_week_index(self, index):
        if index < 0 or index >= len(self.b):
            raise IndexError("Index out of range")

    def _check_week_length(self, week_data):
        if len(week_data) != len(self.variables):
            raise ValueError(
                f"Expected {len(self.variables)} values, got {len(week_data)}."
            )

# persistence
    @classmethod
    def load(cls, document_id=DEFAULT_ID):
        A, b, variables = store.load(document_id)
        instance = object.__new__(cls)
        instance.document_id = document_id
        n_vars = len(variables) if variables else 0
        instance.A = np.array(A, dtype=float) if A else np.zeros((0, n_vars))
        instance.b = np.array(b, dtype=float)
        instance.variables = variables or []
        return instance

    @classmethod
    def load_or_create(cls, document_id=DEFAULT_ID):
        try:
            return cls.load(document_id)
        except FileNotFoundError:
            return cls(np.zeros((0, 0)), [], document_id=document_id)

    def _save(self):
        store.save(
            self.document_id,
            self.A.tolist(),
            self.b.tolist(),
            self.variables,
        )