"""Tests de la barre de menus de l'application."""

import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ui.application_menu import ApplicationMenu
from ui.i18n import Translator


class TestApplicationMenu(unittest.TestCase):
    """Vérifie les entrées de menu et leur état."""

    def setUp(self):
        """Crée une fenêtre racine et une application simulée."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = SimpleNamespace(
            translator=Translator("fr"),
            recent_files=[],
            controller=None,
            _navigation_history=None,
            theme="light",
            load_file=Mock(),
            open_validated_file=Mock(),
            close_file=Mock(),
            show_header=Mock(),
            show_trailer=Mock(),
            go_back=Mock(),
            go_forward=Mock(),
            open_recent_file=Mock(),
            set_language=Mock(),
            toggle_theme=Mock(),
            clear_recent_files=Mock(),
            show_ancestor_tree=Mock(),
            _on_close=Mock(),
        )
        self.menu = ApplicationMenu(self.root, self.app)

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie refresh recent menu lists files.
    def test_refresh_recent_menu_lists_files(self):
        # Given un fichier récent
        self.app.recent_files = ["/tmp/fichier.ged"]

        # When on rafraîchit le menu
        self.menu.refresh_recent_menu()

        # Then le fichier apparaît comme entrée
        self.assertEqual(
            self.menu.recent_menu.entrycget(0, "label"), "/tmp/fichier.ged"
        )

    # Vérifie refresh state enables loaded controls.
    def test_refresh_state_enables_loaded_controls(self):
        # Given un contrôleur chargé et un historique avec retour possible
        controller = Mock()
        controller.is_loaded.return_value = True
        self.app.controller = controller
        self.app._navigation_history = Mock(can_go_back=True, can_go_forward=False)

        # When on rafraîchit l'état
        self.menu.refresh_state()

        # Then les commandes chargées sont activées et l'avant désactivé
        self.assertEqual(
            self.menu.file_menu.entrycget(self.menu.close_file_index, "state"),
            "normal",
        )
        self.assertEqual(self.menu.navigation_menu.entrycget(0, "state"), "normal")
        self.assertEqual(self.menu.navigation_menu.entrycget(1, "state"), "disabled")

    # Vérifie quit app delegates to window close.
    def test_quit_app_delegates_to_window_close(self):
        # Given un menu avec une application minimale
        # When on demande à quitter
        self.menu.quit_app()

        # Then la fermeture orchestrée de la fenêtre est appelée
        self.app._on_close.assert_called_once_with()

    # Vérifie clear recent files confirms before clearing.
    def test_clear_recent_files_confirms_before_clearing(self):
        # Given un fichier récent et une confirmation acceptée
        self.app.recent_files = ["/tmp/fichier.ged"]

        # When on efface les fichiers récents
        with patch("ui.application_menu.messagebox.askyesno", return_value=True):
            self.menu.clear_recent_files()

        # Then le contrôleur applicatif est appelé
        self.app.clear_recent_files.assert_called_once()

    # Vérifie clear recent files does nothing without files.
    def test_clear_recent_files_does_nothing_without_files(self):
        # Given aucun fichier récent
        # When on appelle l'effacement
        self.menu.clear_recent_files()

        # Then aucune confirmation n'est demandée
        self.app.clear_recent_files.assert_not_called()


if __name__ == "__main__":
    unittest.main()
