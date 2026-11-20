"""Tests de la barre de navigation."""

import tkinter as tk
import unittest
from unittest.mock import Mock

from ui.i18n import Translator
from ui.navigation_bar import NavigationBar


class TestNavigationBar(unittest.TestCase):
    """Vérifie l'état des boutons et le compteur d'historique."""

    def setUp(self):
        """Crée une fenêtre racine et une barre de navigation."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.translator = Translator("fr")
        self.on_back = Mock()
        self.on_forward = Mock()
        self.tooltip_factory = Mock()
        self.bar = NavigationBar(
            self.root,
            self.translator,
            self.on_back,
            self.on_forward,
            tooltip_factory=self.tooltip_factory,
        )

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie update state enables only available directions.
    def test_update_state_enables_only_available_directions(self):
        # Given une barre de navigation
        # When on peut reculer mais pas avancer
        self.bar.update_state(True, False, 1, 3)

        # Then seul le bouton précédent est actif
        self.assertTrue(self.bar.back_button.instate(["!disabled"]))
        self.assertFalse(self.bar.forward_button.instate(["!disabled"]))
        self.assertIn("1", self.bar.history_status.cget("text"))
        self.assertIn("3", self.bar.history_status.cget("text"))

    # Vérifie tooltip factory receives navigation buttons.
    def test_tooltip_factory_receives_navigation_buttons(self):
        # Given une barre de navigation avec fabrique d'infobulles
        # When on inspecte les appels
        # Then les deux boutons reçoivent une infobulle
        self.assertEqual(self.tooltip_factory.call_count, 2)
        targets = {call.args[0] for call in self.tooltip_factory.call_args_list}
        self.assertEqual(targets, {self.bar.back_button, self.bar.forward_button})


if __name__ == "__main__":
    unittest.main()
