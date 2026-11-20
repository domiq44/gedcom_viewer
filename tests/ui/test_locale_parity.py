"""Tests de parité des catalogues de locale."""

import json
import unittest
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parents[2] / "ui" / "locales"


class TestLocaleParity(unittest.TestCase):
    """Vérifie que toutes les locales exposent les mêmes clés que l'anglais."""

    # Vérifie all locales have same keys as english.
    def test_all_locales_have_same_keys_as_english(self):
        # Given (Arrange) le catalogue anglais et les autres locales
        reference_path = LOCALES_DIR / "en.json"
        reference = json.loads(reference_path.read_text(encoding="utf-8"))
        locale_files = sorted(LOCALES_DIR.glob("*.json"))

        # Then (Assert) chaque locale expose exactement les mêmes clés
        self.assertGreater(len(locale_files), 1)
        for locale_file in locale_files:
            with self.subTest(locale=locale_file.name):
                catalog = json.loads(locale_file.read_text(encoding="utf-8"))
                self.assertEqual(set(catalog), set(reference))


if __name__ == "__main__":
    unittest.main()
