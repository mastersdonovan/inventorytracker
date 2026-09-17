import unittest
import numpy as np
import store
from optimization import Matrix
from optimization import Optimization
from inventory import Inventory

TEST_ID = "_unit_test"


def _col():
    return store._get_collection()


# ---------------------------------------------------------------------------
# Matrix  (no MongoDB needed)
# ---------------------------------------------------------------------------

class TestMatrix(unittest.TestCase):

    def setUp(self):
        self.m = Matrix([[1, 2, 3],
                         [4, 5, 6],
                         [7, 8, 9]])

    def test_rejects_1d(self):
        with self.assertRaises(ValueError):
            Matrix([1, 2, 3])

    def test_rejects_3d(self):
        with self.assertRaises(ValueError):
            Matrix([[[1, 2], [3, 4]]])

    def test_shape(self):
        self.assertEqual(self.m.shape, (3, 3))

    def test_matmul_ndarray(self):
        m = Matrix([[1, 0], [0, 1]])
        v = np.array([3.0, 4.0])
        np.testing.assert_array_equal(m @ v, v)

    def test_matmul_matrix(self):
        m = Matrix([[1, 0], [0, 1]])
        np.testing.assert_array_equal(m @ m, m.to_numpy())

    def test_matmul_invalid_raises(self):
        with self.assertRaises(ValueError):
            self.m @ "invalid"



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

    @classmethod
    def setUpClass(cls):
        _col().delete_one({"_id": TEST_ID})
        cls.opt = Optimization(cls.A_data, cls.b_data, variables=cls.vars_data, document_id=TEST_ID)

    @classmethod
    def tearDownClass(cls):
        _col().delete_one({"_id": TEST_ID})

    def test_initial_shape(self):
        self.assertEqual(self.opt.A.shape, (4, 3))
        self.assertEqual(len(self.opt.b), 4)

    def test_save_and_load_roundtrip(self):
        loaded = Optimization.load(TEST_ID)
        np.testing.assert_array_almost_equal(
            loaded.A.to_numpy(), self.opt.A.to_numpy()
        )
        np.testing.assert_array_almost_equal(loaded.b, self.opt.b)

    def test_add_week(self):
        opt = Optimization(self.A_data, self.b_data, variables=self.vars_data, document_id=TEST_ID + "_add")
        opt.add_week([105, 2.1, 12], 100)
        self.assertEqual(opt.A.shape, (5, 3))
        reloaded = Optimization.load(TEST_ID + "_add")
        self.assertEqual(reloaded.A.shape, (5, 3))
        _col().delete_one({"_id": TEST_ID + "_add"})

    def test_remove_week(self):
        opt = Optimization(self.A_data, self.b_data, variables=self.vars_data, document_id=TEST_ID + "_rm")
        opt.remove_week(0)
        self.assertEqual(opt.A.shape, (3, 3))
        _col().delete_one({"_id": TEST_ID + "_rm"})

    def test_update_previous_week(self):
        opt = Optimization(self.A_data, self.b_data, variables=self.vars_data, document_id=TEST_ID + "_upd")
        opt.update_previous_week(0, [99, 2.05, 25], 90)
        np.testing.assert_array_almost_equal(opt.A.to_numpy()[0], [99, 2.05, 25])
        self.assertAlmostEqual(opt.b[0], 90)
        _col().delete_one({"_id": TEST_ID + "_upd"})


# ---------------------------------------------------------------------------
# Inventory (MongoDB)
# ---------------------------------------------------------------------------

class TestInventory(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _col().delete_one({"_id": TEST_ID})
        vars_data = [
            {"name": "units_purchased", "unit_cost": 2.0},
            {"name": "unit_cost",       "unit_cost": 1.0},
            {"name": "current_stock",   "unit_cost": 0.0},
        ]
        Optimization(
            [[100, 2.0, 20], [120, 1.8, 15], [90, 2.2, 30], [110, 2.0, 10]],
            [95, 110, 80, 105],
            variables=vars_data,
            document_id=TEST_ID,
        )
        cls.inv = Inventory(document_id=TEST_ID)

    @classmethod
    def tearDownClass(cls):
        _col().delete_one({"_id": TEST_ID})

    def test_loads_existing_data(self):
        self.assertEqual(self.inv.optimization.A.shape, (4, 3))

    def test_fresh_init_when_no_document(self):
        fresh_id = TEST_ID + "_fresh"
        _col().delete_one({"_id": fresh_id})
        inv = Inventory(document_id=fresh_id)
        self.assertEqual(inv.optimization.A.shape, (1, 3))
        _col().delete_one({"_id": fresh_id})

    def test_add_week(self):
        inv = Inventory(document_id=TEST_ID)
        before = inv.optimization.A.shape[0]
        inv.add_week([105, 2.1, 12], 100)
        self.assertEqual(inv.optimization.A.shape[0], before + 1)

    def test_optimal_purchase_low_stock(self):
        p = self.inv.optimal_purchase(unit_cost=2.0, current_stock=5)
        self.assertGreater(p, 0)

    def test_optimal_purchase_high_stock(self):
        p = self.inv.optimal_purchase(unit_cost=2.0, current_stock=200)
        self.assertEqual(p, 0.0)

    def test_get_margin_keys(self):
        result = self.inv.get_margin(unit_cost=2.0, current_stock=5, selling_price=5.0)
        self.assertIn("optimal_purchase", result)
        self.assertIn("units_remaining", result)
        self.assertIn("dollar_profit", result)

    def test_get_margin_profit_positive(self):
        result = self.inv.get_margin(unit_cost=2.0, current_stock=5, selling_price=5.0)
        self.assertGreater(result["dollar_profit"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
