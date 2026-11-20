"""Tests du panneau de sélection du type d'entité."""

import tkinter as tk
import unittest

from ui.entity_type_panel import EntityTypePanel
from ui.i18n import Translator
from ui.themes import COLORS


class TestEntityTypePanel(unittest.TestCase):
    """Vérifie la sélection des boutons et la surbrillance."""

    def setUp(self):
        """Crée une fenêtre racine et un panneau de types."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.selected_type = tk.StringVar(value="INDI")
        self.panel = EntityTypePanel(self.root, Translator("fr"), self.selected_type)

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie set items updates selected type.
    def test_set_items_updates_selected_type(self):
        # Given un panneau de types
        self.panel.set_items([("Individus", "INDI"), ("Familles", "FAM")])

        # When on clique sur le bouton Familles puis on met à jour la surbrillance
        self.panel._buttons["FAM"].invoke()
        self.panel.update_selection("FAM")

        # Then la variable et la surbrillance suivent la sélection
        self.assertEqual(self.selected_type.get(), "FAM")
        self.assertEqual(self.panel._buttons["INDI"].cget("relief"), "flat")
        self.assertEqual(self.panel._buttons["FAM"].cget("relief"), "solid")

    # Vérifie apply theme uses sidebar colors.
    def test_apply_theme_uses_sidebar_colors(self):
        # Given un panneau de types
        self.panel.set_items([("Individus", "INDI")])

        # When on réapplique le thème
        self.panel.apply_theme()

        # Then la couleur de fond correspond au thème courant
        self.assertEqual(self.panel.cget("bg"), COLORS["sidebar"])


if __name__ == "__main__":
    unittest.main()
