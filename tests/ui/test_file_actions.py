"""Tests des actions de fichier de la fenêtre principale."""

import unittest
from unittest.mock import Mock, patch

from ui.file_actions import FileActionsMixin


class _FileActionsHost(FileActionsMixin):
    """Hôte minimal exposant les dépendances des actions de fichier."""

    def __init__(self):
        """Initialise les dépendances simulées."""
        self.translator = Mock()
        self.file_manager = Mock()
        self.file_manager.file_dialog_options.return_value = {}
        self.file_loader = Mock()
        self.load_coordinator = Mock()
        self.load_coordinator.is_loading = False
        self.controller = Mock()
        self.entity_navigator = Mock()
        self.entity_view_manager = Mock()
        self.entity_view_manager.views = {"object": Mock()}
        self.entity_selection_coordinator = Mock()
        self.entity_browser = Mock()
        self.entity_type_var = Mock()
        self.status_var = Mock()
        self.recent_files = []
        self.last_directory = "/tmp"
        self._navigation_history = Mock()
        self._sync_file_manager = Mock()
        self._save_recent_files = Mock()
        self._remember_recent_file = Mock()
        self._clear_entity_views = Mock()
        self._display_raw_text = Mock()
        self._update_entity_type_tabs = Mock()
        self._update_entity_type_tab_state = Mock()
        self._update_navigation_buttons = Mock()
        self._load_file_async = Mock()
        self._apply_loaded_file = Mock()


class TestFileActionsMixin(unittest.TestCase):
    """Vérifie les actions de fichier de la fenêtre principale."""

    def setUp(self):
        """Crée un hôte d'actions de fichier."""
        self.host = _FileActionsHost()

    # Vérifie open recent file delegates to loader.
    def test_open_recent_file_delegates_to_loader(self):
        # Given un hôte d'actions
        # When on ouvre un fichier récent
        self.host.open_recent_file("/tmp/example.ged")

        # Then le chargement est délégué
        self.host._load_file_async.assert_called_once_with("/tmp/example.ged")

    # Vérifie close file returns when loading.
    def test_close_file_returns_when_loading(self):
        # Given un chargement en cours
        self.host.load_coordinator.is_loading = True
        controller = self.host.controller

        # When on ferme le fichier
        self.host.close_file()

        # Then le contrôleur reste inchangé
        self.assertIs(self.host.controller, controller)

    # Vérifie close file returns when not loaded.
    def test_close_file_returns_when_not_loaded(self):
        # Given un contrôleur sans fichier chargé
        self.host.controller.is_loaded.return_value = False
        controller = self.host.controller

        # When on ferme le fichier
        self.host.close_file()

        # Then le contrôleur reste inchangé
        self.assertIs(self.host.controller, controller)

    # Vérifie close file resets entity type.
    def test_close_file_resets_entity_type(self):
        # Given un fichier chargé
        self.host.controller.is_loaded.return_value = True
        self.host.load_coordinator.is_loading = False

        # When on ferme le fichier
        self.host.close_file()

        # Then le type courant et les onglets sont réinitialisés
        self.host.entity_type_var.set.assert_called_once_with("")
        self.host._update_entity_type_tabs.assert_called_once()

    # Vérifie load file reports when already loading.
    def test_load_file_reports_when_already_loading(self):
        # Given un chargement refusé par le coordinateur
        self.host.file_loader.load_async.return_value = False
        self.host.translator.get.return_value = "busy"

        # When on demande un chargement
        FileActionsMixin._load_file_async(self.host, "/tmp/test.ged")

        # Then le statut signale le chargement en cours
        self.host.translator.get.assert_called_once_with("ui.loading_in_progress")
        self.host.status_var.set.assert_called_once_with("busy")

    # Vérifie open validated file returns without filename.
    def test_open_validated_file_returns_without_filename(self):
        # Given un dialogue annulé
        # When on ouvre un fichier validé
        with patch("ui.file_actions.filedialog.askopenfilename", return_value=""):
            self.host.open_validated_file()

        # Then aucun chargement n'est lancé
        self.host._load_file_async.assert_not_called()

    # Vérifie load file returns without filename.
    def test_load_file_returns_without_filename(self):
        # Given un dialogue annulé
        # When on ouvre un fichier
        with patch("ui.file_actions.filedialog.askopenfilename", return_value=""):
            self.host.load_file()

        # Then aucun chargement n'est lancé
        self.host._load_file_async.assert_not_called()


if __name__ == "__main__":
    unittest.main()
