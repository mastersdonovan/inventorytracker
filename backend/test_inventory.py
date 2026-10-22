import unittest
import numpy as np
import store
from optimization import Optimization

TEST_ID = "_unit_test"


def _col():
    return store._get_collection()


# ---------------------------------------------------------------------------
# Optimization (MongoDB)
# ---------------------------------------------------------------------------

class TestOptimization(unittest.TestCase):

    A_data = [[100, 2.0, 20], [120, 1.8, 15], [90, 2.2, 30], [110, 2.0, 10]]
    b_data = [95, 110, 80, 105]
    vars_data = [
        {"name": "units_purchased", "unit_cost": 2.0},
        {"name": "unit_cost",       "unit_cost": 1.0},
        {"name": "current_stock",   "unit_cost": 0.0},
    ]

    def _make(self, suffix=""):
        """Create a fresh document for one test and delete it afterwards."""
        doc_id = TEST_ID + suffix
        _col().delete_one({"_id": doc_id})
        self.addCleanup(_col().delete_one, {"_id": doc_id})
        return Optimization(
            self.A_data,
            self.b_data,
            variables=[dict(v) for v in self.vars_data],
            document_id=doc_id,
        )

    # --- construction / persistence ---------------------------------------

    def test_initial_shape(self):
        opt = self._make()
        self.assertEqual(opt.A.shape, (4, 3))
        self.assertEqual(len(opt.b), 4)

    def test_rejects_1d_A(self):
        with self.assertRaises(ValueError):
            Optimization([1, 2, 3], [1], document_id=TEST_ID + "_bad")

    def test_save_and_load_roundtrip(self):
        opt = self._make()
        loaded = Optimization.load(TEST_ID)
        np.testing.assert_array_almost_equal(loaded.A, opt.A)
        np.testing.assert_array_almost_equal(loaded.b, opt.b)
        self.assertEqual(loaded.variables, opt.variables)

    def test_load_or_create_when_no_document(self):
        fresh_id = TEST_ID + "_fresh"
        _col().delete_one({"_id": fresh_id})
        self.addCleanup(_col().delete_one, {"_id": fresh_id})
        opt = Optimization.load_or_create(fresh_id)
        self.assertEqual(opt.A.shape, (0, 0))
        self.assertEqual(opt.get_variables(), [])

    # --- weeks ------------------------------------------------------------

    def test_add_week(self):
        opt = self._make("_add")
        opt.add_week([105, 2.1, 12], 100)
        self.assertEqual(opt.A.shape, (5, 3))
        self.assertEqual(Optimization.load(TEST_ID + "_add").A.shape, (5, 3))

    def test_add_week_wrong_length(self):
        opt = self._make("_len")
        with self.assertRaises(ValueError):
            opt.add_week([1, 2], 50)

    def test_update_week(self):
        opt = self._make("_upd")
        opt.update_week(0, [99, 2.05, 25], 90)
        np.testing.assert_array_almost_equal(opt.A[0], [99, 2.05, 25])
        self.assertAlmostEqual(opt.b[0], 90)

    def test_update_week_out_of_range(self):
        opt = self._make("_upd_oob")
        with self.assertRaises(IndexError):
            opt.update_week(99, [99, 2.05, 25], 90)

    def test_remove_week(self):
        opt = self._make("_rm")
        opt.remove_week(0)
        self.assertEqual(opt.A.shape, (3, 3))
        self.assertEqual(len(opt.b), 3)

    def test_remove_week_out_of_range(self):
        opt = self._make("_rm_oob")
        with self.assertRaises(IndexError):
            opt.remove_week(-1)

    def test_get_weeks(self):
        opt = self._make("_weeks")
        weeks = opt.get_weeks()
        self.assertEqual(len(weeks), 4)
        self.assertEqual(weeks[0]["units"], [100, 2.0, 20])
        self.assertEqual(weeks[0]["margin"], 95)

    # --- variables --------------------------------------------------------

    def test_add_variable_adds_zero_column(self):
        opt = self._make("_addvar")
        opt.add_variable("new", 1.5)
        self.assertEqual(opt.A.shape, (4, 4))
        np.testing.assert_array_equal(opt.A[:, 3], np.zeros(4))

    def test_update_variable_out_of_range(self):
        opt = self._make("_updvar_oob")
        with self.assertRaises(IndexError):
            opt.update_variable(99, "x", 1.0)

    def test_remove_variable(self):
        opt = self._make("_rmvar")
        opt.remove_variable(0)
        self.assertEqual(opt.A.shape, (4, 2))
        self.assertEqual(len(opt.get_variables()), 2)

    def test_remove_last_variable_clears_weeks(self):
        opt = self._make("_clear")
        for _ in range(3):
            opt.remove_variable(0)
        self.assertEqual(opt.A.shape, (0, 0))
        self.assertEqual(len(opt.b), 0)

    def test_add_variable_and_week_after_clear(self):
        opt = self._make("_reuse")
        for _ in range(3):
            opt.remove_variable(0)
        opt.add_variable("a", 1.0)
        opt.add_week([5], 10)
        self.assertEqual(opt.A.shape, (1, 1))

    def test_get_variables_returns_copies(self):
        opt = self._make("_copies")
        opt.get_variables()[0]["name"] = "changed"
        self.assertEqual(opt.variables[0]["name"], "units_purchased")

    # --- calculation ------------------------------------------------------

    def test_weighted_average_length(self):
        opt = self._make("_avg")
        self.assertEqual(len(opt.get_weighted_average()), 3)

    def test_weighted_average_favors_high_margin_weeks(self):
        opt = Optimization(
            [[10], [20]], [1, 3],
            variables=[{"name": "x", "unit_cost": 1.0}],
            document_id=TEST_ID + "_wavg",
        )
        self.addCleanup(_col().delete_one, {"_id": TEST_ID + "_wavg"})
        # weights 0.25 / 0.75  ->  10*0.25 + 20*0.75 = 17.5
        np.testing.assert_array_almost_equal(opt.get_weighted_average(), [17.5])

    def test_weighted_average_needs_two_weeks(self):
        opt = self._make("_avg_few")
        for _ in range(3):
            opt.remove_week(0)
        with self.assertRaises(ValueError):
            opt.get_weighted_average()


if __name__ == "__main__":
    unittest.main(verbosity=2)