"""Tests de détection des dépassements de seuils du benchmark."""

import unittest

from tests.benchmarks.test_benchmark_common import (
    benchmark_search,
    make_arguments,
)


class TestThresholdFailures(unittest.TestCase):
    """Vérifie la détection des dépassements de seuils."""

    # Vérifie no threshold produces no failure.
    def test_no_threshold_produces_no_failure(self):
        # Given (Arrange) des mesures sans seuil configuré
        arguments = make_arguments()
        # When (Act) on vérifie les seuils
        failures = benchmark_search.threshold_failures(
            "jeu", 1.0, 2.0, 3 * 1024 * 1024, arguments
        )
        # Then (Assert) aucun dépassement n'est signalé
        self.assertEqual(failures, [])

    # Vérifie load threshold exceeded is reported.
    def test_load_threshold_exceeded_is_reported(self):
        # Given (Arrange) un chargement au-dessus du seuil
        arguments = make_arguments(max_load_seconds=1.0)
        # When (Act) on vérifie les seuils
        failures = benchmark_search.threshold_failures("jeu", 2.0, 1.0, 0, arguments)
        # Then (Assert) le dépassement du chargement est signalé
        self.assertEqual(len(failures), 1)
        self.assertIn("chargement", failures[0])

    # Vérifie search threshold exceeded is reported.
    def test_search_threshold_exceeded_is_reported(self):
        # Given (Arrange) une recherche médiane au-dessus du seuil
        arguments = make_arguments(max_search_median_ms=10.0)
        # When (Act) on vérifie les seuils
        failures = benchmark_search.threshold_failures("jeu", 1.0, 20.0, 0, arguments)
        # Then (Assert) le dépassement de la recherche est signalé
        self.assertEqual(len(failures), 1)
        self.assertIn("recherche", failures[0])

    # Vérifie rss threshold exceeded is reported.
    def test_rss_threshold_exceeded_is_reported(self):
        # Given (Arrange) une mémoire RSS au-dessus du seuil
        arguments = make_arguments(max_rss_mib=1.0)
        # When (Act) on vérifie les seuils
        failures = benchmark_search.threshold_failures(
            "jeu", 1.0, 1.0, 2 * 1024 * 1024, arguments
        )
        # Then (Assert) le dépassement de la mémoire est signalé
        self.assertEqual(len(failures), 1)
        self.assertIn("RSS", failures[0])


if __name__ == "__main__":
    unittest.main()
