"""Tests de mesure du fichier de benchmark."""

import os
import tempfile
import unittest

from tests.benchmarks.test_benchmark_common import benchmark_search


class TestBenchmarkFile(unittest.TestCase):
    """Vérifie que le benchmark mesure des entités réellement indexées."""

    # Vérifie benchmark file counts indexed entities and matches.
    def test_benchmark_file_counts_indexed_entities_and_matches(self):
        # Given un fichier GEDCOM avec un individu
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".ged", delete=False
        ) as handle:
            handle.write(
                "0 HEAD\n1 CHAR UTF-8\n" "0 @I1@ INDI\n1 NAME John /Doe/\n" "0 TRLR\n"
            )
            filename = handle.name
        try:
            # When on mesure le fichier
            result = benchmark_search.benchmark_file(filename, "Doe", 1)
        finally:
            os.unlink(filename)
        # Then les compteurs et les résultats de recherche sont non nuls
        self.assertEqual(result[12], 1)
        self.assertEqual(result[8], 1)
        self.assertEqual(result[9], 1)


if __name__ == "__main__":
    unittest.main()
