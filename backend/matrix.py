import numpy as np
class Matrix:
    def __init__(self, data):
        self._m = np.array(data, dtype=float)
        if self._m.ndim != 2:
            raise ValueError("Matrix data must be at least 2-dimensions")
    
    def __matmul__(self, other):
        if isinstance(other, np.ndarray):
            return self._m @ other
        elif isinstance(other, Matrix):
            return self._m @ other._m
        else:
            raise ValueError("Unsupported type for matrix multiplication")
        
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
        AtA =  self._m.T @ self._m 
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
