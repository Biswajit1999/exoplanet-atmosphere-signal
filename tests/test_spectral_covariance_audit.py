import unittest
import numpy as np
from research.spectral_covariance_audit import (
    ar1_covariance, template_gls, rho_sensitivity, injection_coverage)


class TestSpectralCovariance(unittest.TestCase):
    def test_diagonal_closed_form(self):
        t = np.array([1., 2., 3.])
        a, s, chi = template_gls(2*t, t, np.eye(3)*4)
        self.assertAlmostEqual(a, 2)
        self.assertAlmostEqual(s, 2/np.sqrt(14))
        self.assertAlmostEqual(chi, 0)

    def test_correlated_exact_recovery(self):
        t = np.array([1., -1., 2., 0.])
        c = ar1_covariance(4, .2, .65)
        self.assertAlmostEqual(template_gls(3*t, t, c)[0], 3)

    def test_covariance_positive_definite(self):
        self.assertTrue(np.all(np.linalg.eigvalsh(ar1_covariance(8, 1, -.8)) > 0))
        with self.assertRaises(ValueError):
            ar1_covariance(4, 1, 1)

    def test_singular_rejected(self):
        with self.assertRaises(ValueError):
            template_gls([1, 2], [1, 1], [[1, 1], [1, 1]])

    def test_sensitivity(self):
        values = rho_sensitivity([1, 2, 1], [1, 1, 1], 1, [0, .5])
        self.assertEqual(len(values), 2)
        self.assertGreater(values[1]["sigma_amplitude"], values[0]["sigma_amplitude"])

    def test_seeded_coverage(self):
        t = np.ones(5)
        r = injection_coverage(t, ar1_covariance(5, .2, .4), draws=600, seed=12)
        self.assertTrue(.60 < r["one_sigma_coverage"] < .76)
        self.assertAlmostEqual(r["empirical_sd"], r["analytic_sd"], delta=.015)


if __name__ == "__main__":
    unittest.main()
