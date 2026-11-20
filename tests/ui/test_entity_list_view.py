"""Tests de la vue de liste des entités."""

import tkinter as tk
import unittest
from unittest.mock import Mock

from ui.entity_list_view import EntityListView
from ui.i18n import Translator


class TestEntityListView(unittest.TestCase):
    """Vérifie les callbacks de recherche et de remise à zéro."""

    def setUp(self):
        """Crée une fenêtre racine et une vue de liste avec callbacks simulés."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.on_search = Mock()
        self.on_clear_search = Mock()
        self.on_sort = Mock()
        self.on_select = Mock()
        self.tooltip_factory = Mock()
        self.view = EntityListView(
            self.root,
            Translator("fr"),
            self.on_search,
            self.on_clear_search,
            self.on_sort,
            self.on_select,
            tooltip_factory=self.tooltip_factory,
        )

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie search variable triggers search callback.
    def test_search_variable_triggers_search_callback(self):
        # Given une vue de liste
        # When on modifie le champ de recherche
        self.view.search_var.set("Dupont")

        # Then le callback de recherche est appelé
        self.on_search.assert_called_once()

    # Vérifie clear button invokes clear callback.
    def test_clear_button_invokes_clear_callback(self):
        # Given une vue de liste
        # When on clique sur le bouton d'effacement
        self.view.clear_search_button.invoke()

        # Then le callback de remise à zéro est appelé
        self.on_clear_search.assert_called_once()

    # Vérifie tooltip factory receives clear button.
    def test_tooltip_factory_receives_clear_button(self):
        # Given une vue de liste avec fabrique d'infobulles
        # When on inspecte les appels
        # Then le bouton d'effacement reçoit une infobulle
        self.assertIn(
            self.view.clear_search_button,
            [call.args[0] for call in self.tooltip_factory.call_args_list],
        )


if __name__ == "__main__":
    unittest.main()
