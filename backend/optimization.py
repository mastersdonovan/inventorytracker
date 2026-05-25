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

    # Convert the matrix to Row Echelon Form (REF) and apply the same operations to vector b.
    def rref(self, b):
        """Convert the matrix to Reduced Row Echelon Form (RREF) and apply the same operations to vector b."""
        m, n = self._m.shape
        augmented = np.hstack((self._m, b.reshape(-1, 1)))
        row = 0
        for col in range(n):
            if row >= m:
                break
            # Find the pivot row
            pivot_row = np.argmax(np.abs(augmented[row:, col])) + row
            if augmented[pivot_row, col] == 0:
                continue
            # Swap the current row with the pivot row
            augmented[[row, pivot_row]] = augmented[[pivot_row, row]]
            # Normalize the pivot row
            augmented[row] /= augmented[row, col]
            # Eliminate the current column in the rows below
            for r in range(row + 1, m):
                augmented[r] -= augmented[row] * augmented[r, col]
            row += 1
        # Back substitution to get RREF form
        for r in range(m - 1, -1, -1):
            # Find the leading 1 in the current row
            leading_one_col = np.where(augmented[r, :-1] == 1)[0]
            if len(leading_one_col) == 0:
                continue
            leading_one_col = leading_one_col[0]
            # Eliminate the current column in the rows above
            for r_above in range(r - 1, -1, -1):
                augmented[r_above] -= augmented[r] * augmented[r_above, leading_one_col]
        return augmented[:, -1]

    # Solve the least squares problem Ax = b by converting it to the normal equations A^T A x = A^T b
    def leastSquares(self, b):
        # find A^t * A
        AtA = self._m.T @ self._m
        # find A^t * b
        Atb = self._m.T @ b
        return Matrix(AtA).rref(Atb)

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

    def get_optimal_x(self):
        return self.A.leastSquares(self.b)

    @classmethod
    def load(cls, document_id=DEFAULT_ID):
        A, b, variables = store.load(document_id)
        instance = object.__new__(cls)
        instance.document_id = document_id
        instance.A = Matrix(A)
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
