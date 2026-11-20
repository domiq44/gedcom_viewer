"""Tests de la mesure de mémoire résidente du benchmark."""

import unittest

from tests.benchmarks.test_benchmark_common import benchmark_search


class TestPeakRss(unittest.TestCase):
    """Vérifie la mesure de mémoire résidente du benchmark."""

    # Vérifie peak rss retourne un entier positif ou nul.
    def test_peak_rss_returns_non_negative_int(self):
        # Given (Arrange) aucune condition particulière
        # When (Act) on mesure la mémoire résidente
        result = benchmark_search.peak_rss_bytes()
        # Then (Assert) le résultat est un entier positif ou nul
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
