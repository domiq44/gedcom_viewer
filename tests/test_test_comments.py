"""Contrôle la présence d'un commentaire avant chaque méthode de test."""

import ast
import unittest
from pathlib import Path


class TestTestComments(unittest.TestCase):
    """Vérifie la conformité des commentaires des tests."""

    # Vérifie que chaque méthode de test est précédée d'un commentaire.
    def test_every_test_has_preceding_comment(self):
        # Given (Arrange) l'ensemble des fichiers de test
        test_files = sorted(Path("tests").rglob("test_*.py"))

        # When (Act) on inspecte chaque méthode de test
        missing = []
        for path in test_files:
            source = path.read_text(encoding="utf-8")
            lines = source.splitlines()
            for node in ast.walk(ast.parse(source)):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not node.name.startswith("test_"):
                    continue
                previous = node.lineno - 2
                while previous >= 0 and (
                    not lines[previous].strip()
                    or lines[previous].lstrip().startswith("@")
                ):
                    previous -= 1
                has_comment = previous >= 0 and lines[previous].lstrip().startswith("#")
                if not has_comment:
                    missing.append(f"{path}:{node.lineno}:{node.name}")

        # Then (Assert) chaque test est précédé d'un commentaire
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
