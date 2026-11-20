"""Tests du traducteur : langue par défaut, replis et exhaustivité des clés."""

import os
import tempfile
import unittest
from unittest.mock import patch

from ui.i18n import DEFAULT_LANGUAGE, Translator, _load_catalog


class TestTranslator(unittest.TestCase):
    """Vérifie la langue par défaut, les replis et l'exhaustivité des traductions."""

    # Vérifie english is the default language.
    def test_english_is_the_default_language(self):
        translator = Translator()

        self.assertEqual(translator.language, DEFAULT_LANGUAGE)
        self.assertEqual(translator.get("menu.file"), "File")

    # Vérifie missing placeholder returns unformatted text.
    def test_missing_placeholder_returns_unformatted_text(self):
        translator = Translator("en")

        self.assertEqual(
            translator.get("ui.load_error"),
            "Unable to load the GEDCOM file:\n{error}",
        )

    # Vérifie unexpected placeholder is logged and returns unformatted text.
    def test_unexpected_placeholder_is_logged(self):
        translator = Translator("en")

        with self.assertLogs("ui.i18n", level="WARNING") as logs:
            text = translator.get("ui.load_error", wrong="value")

        self.assertEqual(text, "Unable to load the GEDCOM file:\n{error}")
        self.assertIn("ui.load_error", logs.output[0])

    # Vérifie unknown key falls back to key.
    def test_unknown_key_falls_back_to_key(self):
        translator = Translator()

        self.assertEqual(translator.get("missing.key"), "missing.key")

    # Vérifie unknown language is rejected.
    def test_unknown_language_is_rejected(self):
        translator = Translator()

        with self.assertRaises(ValueError):
            translator.set_language("xx")

    # Vérifie english is available.
    def test_english_is_available(self):
        translator = Translator("en")

        self.assertEqual(translator.get("menu.file"), "File")

    # Vérifie citation category is translated in all languages.
    def test_citation_category_is_translated_in_all_languages(self):
        for language in ("fr", "en", "es", "de", "it", "pt"):
            with self.subTest(language=language):
                translator = Translator(language)

                self.assertNotEqual(
                    translator.get("entity.CITE"),
                    "entity.CITE",
                )

    # Vérifie individual detail tabs are translated in all languages.
    def test_individual_detail_tabs_are_translated_in_all_languages(self):
        keys = ("view.tag", "view.value", "view.value_preview")
        for language in ("fr", "en", "es", "de", "it", "pt"):
            with self.subTest(language=language):
                translator = Translator(language)

                for key in keys:
                    self.assertNotEqual(translator.get(key), key)

    # Vérifie load catalog returns empty for missing language.
    def test_load_catalog_returns_empty_for_missing_language(self):
        self.assertEqual(_load_catalog("missing-language"), {})

    # Vérifie load catalog returns empty for invalid json.
    def test_load_catalog_returns_empty_for_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            with open(
                os.path.join(directory, "invalid.json"), "w", encoding="utf-8"
            ) as handle:
                handle.write("{invalid")

            with patch("ui.i18n.LOCALES_DIR", directory):
                self.assertEqual(_load_catalog("invalid"), {})

    # Vérifie citation view is translated in all languages.
    def test_citation_view_is_translated_in_all_languages(self):
        for language in ("fr", "en", "es", "de", "it", "pt"):
            with self.subTest(language=language):
                translator = Translator(language)

                for key in (
                    "view.citation",
                    "view.citation_pointer",
                    "view.citation_details",
                ):
                    self.assertNotEqual(translator.get(key), key)


if __name__ == "__main__":
    unittest.main()
