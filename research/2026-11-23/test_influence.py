import unittest
import numpy as np
from influence import weighted_fit, influence, block_deletion

class TestInfluence(unittest.TestCase):
    def setUp(self):
        self.w = np.linspace(1, 3, 24)
        self.x = np.column_stack([np.ones(24), self.w - 2])
        self.s = np.full(24, 0.2)
        self.y = self.x @ [5., 2.]

    def test_exact_fit_and_covariance(self):
        beta, cov = weighted_fit(self.x, self.y, self.s)
        np.testing.assert_allclose(beta, [5, 2], atol=1e-12)
        np.testing.assert_allclose(cov, np.linalg.inv((self.x/self.s[:,None]).T @ (self.x/self.s[:,None])), atol=1e-12)

    def test_leverage_sum_and_zero_influence(self):
        h, shifts = influence(self.x, self.y, self.s)
        self.assertAlmostEqual(h.sum(), 2)
        np.testing.assert_allclose(shifts, 0, atol=1e-12)

    def test_outlier_influence(self):
        y = self.y.copy()
        y[-1] += 3
        _, shifts = influence(self.x, y, self.s)
        self.assertGreater(np.linalg.norm(shifts[-1]), 0.05)

    def test_block_deletion(self):
        result = block_deletion(self.x, self.y, self.s, self.w, 0.5)
        self.assertGreaterEqual(len(result), 4)
        for _, _, delta in result:
            np.testing.assert_allclose(delta, 0, atol=1e-12)

    def test_bad_sigma(self):
        with self.assertRaises(ValueError):
            weighted_fit(self.x, self.y, np.zeros(24))

if __name__ == "__main__":
    unittest.main()
