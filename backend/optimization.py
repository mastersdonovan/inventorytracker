import store
import numpy as np

DEFAULT_ID = "main"


class Matrix:
    def __init__(self, data):
        self._m = np.array(data, dtype=float)
        if self._m.ndim != 2:
            raise ValueError("Matrix data must be 2-dimensional")

    def __matmul__(self, other):
        if isinstance(other, np.ndarray):
            return self._m @ other
        elif isinstance(other, Matrix):
            return self._m @ other._m
        else:
            raise ValueError("Unsupported type for matrix multiplication")

    def add_column(self, values=None):
        """Append a column to the matrix. Defaults to zeros if no values provided."""
        m = self._m.shape[0]
        col = np.zeros((m, 1)) if values is None else np.array(values, dtype=float).reshape(m, 1)
        self._m = np.hstack((self._m, col))
        return self

    def remove_column(self, index):
        """Remove the column at the given index."""
        self._m = np.delete(self._m, index, axis=1)
        return self
    
    # Calculate weighted average of the units per variable across all recorded weeks, weighted by margin.
    def get_weighted_average(self):
        """Margin weighted average units per variable across all recorded weeks. 
           Weeks with higher margin pull the result up; falls back to a uniform averge if no week has positive margin yet."""
        if len(self.b < 2):
            raise ValueError("Need at least 2 weeks of data to calculate weighted average.")
        A = self.A.to_numpy()
        weights = np.maximum(self.b, 0.0)
        if weights.sum() == 0:
            weights = np.ones(len(self.b))
        weights /= weights.sum()
        return A.T @ weights


    @property
    def shape(self):
        return self._m.shape

    def to_numpy(self):
        return self._m.copy()

    def __repr__(self):
        return f"Matrix(\n{self._m}\n)"


class Optimization:
    def __init__(self, A, b, variables=None, document_id=DEFAULT_ID):
        self.document_id = document_id
        self.A = Matrix(A)
        self.b = np.array(b, dtype=float)
        self.variables = variables or []
        self._save()

    def add_week(self, week_data, margin):
        if len(week_data) != len(self.variables):
            raise ValueError(
                f"Expected {len(self.variables)} values, got {len(week_data)}."
            )
        self.A = Matrix(np.vstack((self.A.to_numpy(), week_data)))
        self.b = np.hstack((self.b, margin))
        self._save()

    def update_previous_week(self, week_index, week_data, margin):
        if len(week_data) != len(self.variables):
            raise ValueError(
                f"Expected {len(self.variables)} values, got {len(week_data)}."
            )
        self.A = Matrix(np.vstack((
            self.A.to_numpy()[:week_index],
            week_data,
            self.A.to_numpy()[week_index + 1:]
        )))
        self.b = np.hstack((self.b[:week_index], margin, self.b[week_index + 1:]))
        self._save()

    def remove_week(self, week_index):
        self.A = Matrix(np.vstack((
            self.A.to_numpy()[:week_index],
            self.A.to_numpy()[week_index + 1:]
        )))
        self.b = np.hstack((self.b[:week_index], self.b[week_index + 1:]))
        self._save()

    @classmethod
    def load(cls, document_id=DEFAULT_ID):
        A, b, variables = store.load(document_id)
        instance = object.__new__(cls)
        instance.document_id = document_id
        n_vars = len(variables) if variables else 0
        instance.A = Matrix(A) if A else Matrix(np.zeros((0, max(n_vars, 1))))
        instance.b = np.array(b, dtype=float)
        instance.variables = variables or []
        return instance

    def _save(self):
        store.save(
            self.document_id,
            self.A.to_numpy().tolist(),
            self.b.tolist(),
            self.variables,
        )
    def clear(self):
        """ Wipe all recorded weeks. Called when no variables remain, since a weeks matrix can't meaningfully exist with zero columns. """
        self.A = Matrix(np.zeros((0,0)))
        self.b = np.zeros(0)
        self._save()

