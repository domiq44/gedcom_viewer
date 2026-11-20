"""Tests du calcul des percentiles du benchmark."""

import unittest

from tests.benchmarks.test_benchmark_common import benchmark_search


class TestPercentile(unittest.TestCase):
    """Vérifie le calcul des percentiles du benchmark."""

    # Vérifie percentile interpolates between values.
    def test_percentile_interpolates_between_values(self):
        # Given (Arrange) une série ordonnée
        values = [1.0, 2.0, 3.0, 4.0]
        # When (Act) on calcule la médiane
        result = benchmark_search.percentile(values, 50)
        # Then (Assert) la valeur interpolée est retournée
        self.assertAlmostEqual(result, 2.5)

    # Vérifie percentile returns zero for empty series.
    def test_percentile_returns_zero_for_empty_series(self):
        # Given (Arrange) une série vide
        values = []
        # When (Act) on calcule un percentile
        result = benchmark_search.percentile(values, 95)
        # Then (Assert) la valeur par défaut est nulle
        self.assertEqual(result, 0.0)


if __name__ == "__main__":
    unittest.main()
