"""Helpers partagés pour les tests du benchmark de recherche."""

import importlib.util
import types
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[2] / "benchmarks" / "benchmark_search.py"
SPEC = importlib.util.spec_from_file_location("benchmark_search", MODULE_PATH)
benchmark_search = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark_search)


def make_arguments(**overrides):
    """Construit des arguments de benchmark avec des seuils optionnels."""
    arguments = types.SimpleNamespace(
        max_load_seconds=None,
        max_search_median_ms=None,
        max_rss_mib=None,
    )
    for name, value in overrides.items():
        setattr(arguments, name, value)
    return arguments


if __name__ == "__main__":
    unittest.main()
