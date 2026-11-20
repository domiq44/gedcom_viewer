"""Tests de conformité documentaire des fichiers de code."""

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE_DIRECTORIES = ("gedcom", "controllers", "ui", "tests", "benchmarks", "scripts")
CODE_FILES = ("main.py",)
PRODUCTION_DIRECTORIES = ("gedcom", "controllers", "ui")
PRODUCTION_FILES = (
    "main.py",
    "benchmarks/benchmark_search.py",
    "scripts/smoke_test_dist.py",
)


def _iter_paths(directories, files):
    """Itère sur les fichiers Python d'un ensemble de répertoires et fichiers."""
    for directory in directories:
        yield from (ROOT / directory).rglob("*.py")
    for name in files:
        yield ROOT / name


def _code_paths():
    """Itère sur tous les fichiers de code du projet."""
    yield from _iter_paths(CODE_DIRECTORIES, CODE_FILES)


def _production_paths():
    """Itère sur les fichiers Python de production."""
    yield from _iter_paths(PRODUCTION_DIRECTORIES, PRODUCTION_FILES)


class TestCodeDocstrings(unittest.TestCase):
    """Vérifie que les fichiers de code et définitions de production sont documentés."""

    @staticmethod
    def _paths(paths):
        """Retourne les chemins sans caches Python."""
        return [path for path in paths if "__pycache__" not in path.parts]

    # Vérifie modules have docstrings.
    def test_modules_have_docstrings(self):
        """Vérifie que chaque fichier de code porte un cartouche."""
        # Given (Arrange) les fichiers de code
        paths = self._paths(_code_paths())
        # When (Act) on inspecte les cartouches
        missing = [
            str(path.relative_to(ROOT))
            for path in paths
            if ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) is None
        ]
        # Then (Assert) chaque module possède un cartouche
        self.assertEqual(missing, [])

    # Vérifie definitions have docstrings.
    def test_definitions_have_docstrings(self):
        """Vérifie que chaque définition de production porte une docstring."""
        # Given (Arrange) les fichiers de production
        paths = self._paths(_production_paths())
        # When (Act) on inspecte les définitions
        missing = []
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    if ast.get_docstring(node) is None:
                        missing.append(f"{path.relative_to(ROOT)}:{node.lineno}")
        # Then (Assert) chaque définition possède une docstring
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
