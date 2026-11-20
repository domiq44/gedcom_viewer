"""Tests de la barre de statut."""

import tkinter as tk
import unittest

from ui.i18n import Translator
from ui.status_bar import StatusBar


class TestStatusBar(unittest.TestCase):
    """Vérifie l'affichage et le caractère non éditable du statut."""

    def setUp(self):
        """Crée une fenêtre racine, un traducteur et une variable de statut."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.translator = Translator("fr")
        self.status_var = tk.StringVar(value="message")

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie status label shows status variable.
    def test_status_label_shows_status_variable(self):
        # Given une barre de statut avec un message
        bar = StatusBar(self.root, self.translator, self.status_var)

        # When on lit le champ de statut
        # Then il affiche le message et reste en lecture seule
        self.assertEqual(bar.status_label.get(), "message")
        self.assertEqual(bar.status_label.cget("state"), "readonly")

    # Vérifie apply theme updates readonly background.
    def test_apply_theme_updates_readonly_background(self):
        # Given une barre de statut
        bar = StatusBar(self.root, self.translator, self.status_var)

        # When on réapplique le thème
        bar.apply_theme()

        # Then la couleur de fond du champ suit celle du cadre
        self.assertEqual(
            bar.status_label.cget("readonlybackground"), bar.cget("background")
        )


if __name__ == "__main__":
    unittest.main()
