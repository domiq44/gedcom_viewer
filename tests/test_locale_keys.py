"""Tests de conformité des clés de traduction utilisées dans le code."""

import ast
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORIES = ("ui", "controllers")
LOCALES_DIR = ROOT / "ui" / "locales"
LANGUAGES = ("en", "fr", "es", "de", "it", "pt")
KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+$")


def _string_keys(node):
    """Retourne les clés littérales contenues dans un nœud d'argument."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value] if KEY_PATTERN.match(node.value) else []
    if isinstance(node, ast.IfExp):
        return _string_keys(node.body) + _string_keys(node.orelse)
    return []


def _literal_keys():
    """Retourne les clés de traduction littérales et leurs emplacements."""
    keys = {}
    for directory in SOURCE_DIRECTORIES:
        for path in sorted((ROOT / directory).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not node.args:
                    continue
                func = node.func
                is_translator_get = (
                    isinstance(func, ast.Attribute) and func.attr == "get"
                )
                is_tr_helper = isinstance(func, ast.Name) and func.id == "tr"
                if not (is_translator_get or is_tr_helper):
                    continue
                location = f"{path.relative_to(ROOT)}:{node.lineno}"
                for key in _string_keys(node.args[0]):
                    keys.setdefault(key, []).append(location)
    return keys


class TestLocaleKeys(unittest.TestCase):
    """Vérifie que les clés de traduction littérales existent dans les locales."""

    @classmethod
    def setUpClass(cls):
        """Charge les catalogues de traduction de toutes les langues."""
        cls.catalogs = {
            language: json.loads(
                (LOCALES_DIR / f"{language}.json").read_text(encoding="utf-8")
            )
            for language in LANGUAGES
        }

    # Vérifie le collecteur repère bien les clés littérales.
    def test_collector_finds_literal_keys(self):
        # Given le code de production
        # When on collecte les clés littérales
        keys = _literal_keys()

        # Then une clé connue du panneau de détail est présente
        self.assertIn("view.divorces", keys)

    # Vérifie chaque clé littérale est traduite dans toutes les langues.
    def test_literal_keys_exist_in_every_locale(self):
        # Given les catalogues et les clés utilisées
        keys = _literal_keys()

        # When on vérifie la présence de chaque clé dans chaque langue
        missing = {
            language: sorted(key for key in keys if key not in catalog)
            for language, catalog in self.catalogs.items()
        }

        # Then aucune langue ne présente de clé manquante
        self.assertEqual({key: value for key, value in missing.items() if value}, {})


if __name__ == "__main__":
    unittest.main()
