"""Tests de l'en-tête applicatif."""

import tkinter as tk
import unittest

from ui.app_header import AppHeader
from ui.i18n import Translator
from ui.themes import COLORS


class TestAppHeader(unittest.TestCase):
    """Vérifie le titre, le sous-titre et l'application du thème."""

    def setUp(self):
        """Crée une fenêtre racine et un traducteur français."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.translator = Translator("fr")

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie builds translated title and subtitle.
    def test_builds_translated_title_and_subtitle(self):
        # Given un en-tête applicatif
        header = AppHeader(self.root, self.translator)

        # When on lit les libellés
        # Then ils proviennent du traducteur
        self.assertEqual(
            header.app_title.cget("text"), self.translator.get("app.title")
        )
        self.assertEqual(
            header.app_subtitle.cget("text"), self.translator.get("app.subtitle")
        )

    # Vérifie apply theme uses current colors.
    def test_apply_theme_uses_current_colors(self):
        # Given un en-tête applicatif
        header = AppHeader(self.root, self.translator)

        # When on réapplique le thème
        header.apply_theme()

        # Then la couleur de fond correspond au thème courant
        self.assertEqual(header.cget("bg"), COLORS["header_background"])


if __name__ == "__main__":
    unittest.main()
