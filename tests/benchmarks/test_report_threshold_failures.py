"""Tests de rapport des dépassements de seuils du benchmark."""

import contextlib
import io
import unittest

from tests.benchmarks.test_benchmark_common import benchmark_search


class TestReportThresholdFailures(unittest.TestCase):
    """Vérifie le rapport des dépassements de seuils."""

    # Vérifie no failure returns zero.
    def test_no_failure_returns_zero(self):
        # Given (Arrange) aucun dépassement
        failures = []
        # When (Act) on produit le rapport
        code = benchmark_search.report_threshold_failures(failures)
        # Then (Assert) le code de sortie est nul
        self.assertEqual(code, 0)

    # Vérifie failure returns one and prints message.
    def test_failure_returns_one_and_prints_message(self):
        # Given (Arrange) un dépassement
        failures = ["jeu: chargement 2.000 s > 1.000 s"]
        # When (Act) on produit le rapport
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = benchmark_search.report_threshold_failures(failures)
        # Then (Assert) le code de sortie vaut un et le message est affiché
        self.assertEqual(code, 1)
        self.assertIn("Seuil dépassé", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
