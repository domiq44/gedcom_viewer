"""Tests du balisage des URL dans un widget texte."""

import tkinter as tk
import unittest

from ui.views import link_utils


class TestConfigureTextUrls(unittest.TestCase):
    """Vérifie le balisage des URL dans un widget texte."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.text = tk.Text(self.root)

    def tearDown(self):
        self.root.destroy()

    # Vérifie applies url tag to url span.
    def test_applies_url_tag_to_url_span(self):
        # Given (Arrange) un widget texte contenant une URL
        self.text.insert("1.0", "Visit https://example.com now")
        # When (Act) on configure les URLs
        link_utils.configure_text_urls(self.text)
        # Then (Assert) un tag url est présent
        self.assertTrue(self.text.tag_ranges("url"))

    # Vérifie no url tag without url.
    def test_no_url_tag_without_url(self):
        # Given (Arrange) un widget texte sans URL
        self.text.insert("1.0", "plain text")
        # When (Act) on configure les URLs
        link_utils.configure_text_urls(self.text)
        # Then (Assert) aucun tag url n'est appliqué
        self.assertFalse(self.text.tag_ranges("url"))

    # Vérifie trailing punctuation is excluded from url tag.
    def test_strips_trailing_punctuation_from_url_tag(self):
        # Given (Arrange) une URL suivie d'un point
        self.text.insert("1.0", "See https://example.com.")
        # When (Act) on configure les URLs
        link_utils.configure_text_urls(self.text)
        # Then (Assert) le tag couvre l'URL sans le point final
        start, end = self.text.tag_ranges("url")
        self.assertEqual(self.text.get(start, end), "https://example.com")


if __name__ == "__main__":
    unittest.main()
