import unittest

from ui.i18n import DEFAULT_LANGUAGE, Translator


class TestTranslator(unittest.TestCase):
    def test_french_is_the_default_language(self):
        translator = Translator()

        self.assertEqual(translator.language, DEFAULT_LANGUAGE)
        self.assertEqual(translator.get("menu.file"), "Fichier")

    def test_unknown_key_falls_back_to_key(self):
        translator = Translator()

        self.assertEqual(translator.get("missing.key"), "missing.key")

    def test_unknown_language_is_rejected(self):
        translator = Translator()

        with self.assertRaises(ValueError):
            translator.set_language("en")


if __name__ == "__main__":
    unittest.main()
