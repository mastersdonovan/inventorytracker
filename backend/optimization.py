import store
import matrix
import numpy as np

DEFAULT_ID = "main"


class Optimization:
    def __init__(self, A, b, document_id=DEFAULT_ID):
        self.document_id = document_id
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
    def load(cls, document_id=DEFAULT_ID):
        A, b = store.load(document_id)
        instance = object.__new__(cls)
        instance.document_id = document_id
        instance.A = matrix.Matrix(A)
        instance.b = np.array(b, dtype=float)
        return instance

    def _save(self):
        store.save(self.document_id, self.A.to_numpy().tolist(), self.b.tolist())
