"""Tests des préférences de session."""

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from ui.session_preferences import SessionHost, SessionPreferencesMixin


class _Host(SessionPreferencesMixin):
    """Hôte minimal exposant les attributs attendus par le mixin."""

    def __init__(self):
        """Initialise les dépendances simulées du mixin."""
        self.root = Mock()
        self.translator = Mock()
        self.translator.language = "fr"
        self.status_var = Mock()
        self.file_manager = Mock()
        self.menu_bar = Mock()
        self.detail_panel = Mock()
        self.app_header = Mock()
        self.entity_type_tabs = Mock()
        self.entity_browser = Mock()
        self.nav_toolbar = Mock()
        self.log_status_frame = Mock()
        self.highlighter = Mock()
        self.recent_files = []
        self.last_directory = "/tmp"
        self.theme = "light"
        self.window_size = None
        self.view_preferences = {}
        self.last_selected_entities = {}
        self._apply_theme = Mock()
        self._save_recent_files = Mock()
        self._load_file_async = Mock()
        self._restart_application = Mock()

    def _show_entity_view(self, entity_type, entity):
        """Méthode factice utilisée lors du re-thème."""
        return None


class TestSessionPreferences(unittest.TestCase):
    """Vérifie les préférences de thème, de langue et de fichiers récents."""

    def setUp(self):
        """Crée un hôte de test."""
        self.host = _Host()

    # Vérifie host satisfies session protocol.
    def test_host_satisfies_session_protocol(self):
        # Given un hôte complet
        self.host.theme_registry = Mock()

        # When on vérifie le protocole
        # Then l'hôte est reconnu comme conforme
        self.assertIsInstance(self.host, SessionHost)

    # Vérifie apply view preferences updates detail panel.
    def test_apply_view_preferences_updates_detail_panel(self):
        # Given des préférences d'affichage
        self.host.view_preferences = {
            "indent": True,
            "show_gedcom_view": True,
            "show_entity_view": False,
        }
        self.host.detail_panel.indent_var = Mock()

        # When on applique les préférences
        self.host._apply_view_preferences()

        # Then le panneau de détail est mis à jour
        self.host.detail_panel.indent_var.set.assert_called_once_with(True)
        self.host.detail_panel.set_view_visibility.assert_called_once_with(True, False)

    # Vérifie sync file manager copies current state.
    def test_sync_file_manager_copies_current_state(self):
        # Given un gestionnaire de fichiers et un état courant
        self.host.file_manager = Mock()
        self.host.last_directory = "/tmp"
        self.host.recent_files = ["/tmp/a.ged"]

        # When on synchronise
        self.host._sync_file_manager()

        # Then le gestionnaire reflète l'état courant
        self.assertEqual(self.host.file_manager.last_directory, "/tmp")
        self.assertEqual(self.host.file_manager.recent_files, ["/tmp/a.ged"])

    # Vérifie clear recent files resets list and refreshes menu.
    def test_clear_recent_files_resets_list_and_refreshes_menu(self):
        # Given des fichiers récents
        self.host.recent_files = ["/tmp/a.ged"]

        # When on les efface
        self.host.clear_recent_files()

        # Then la liste est vidée, sauvegardée et le menu rafraîchi
        self.assertEqual(self.host.recent_files, [])
        self.host._save_recent_files.assert_called_once()
        self.host.menu_bar.refresh_recent_menu.assert_called_once()

    # Vérifie toggle theme switches and saves.
    def test_toggle_theme_switches_and_saves(self):
        # Given un thème clair
        with (
            patch("ui.session_preferences.set_theme") as set_theme,
            patch("ui.session_preferences.apply_app_theme") as apply_app_theme,
        ):
            # When on bascule vers le thème sombre
            self.host.toggle_theme("dark")

        # Then le thème et les widgets sont mis à jour puis sauvegardés
        self.assertEqual(self.host.theme, "dark")
        set_theme.assert_called_once_with("dark")
        apply_app_theme.assert_called_once_with(self.host.root)
        self.host._apply_theme.assert_called_once()
        self.host._save_recent_files.assert_called_once()

    # Vérifie toggle theme ignores same theme.
    def test_toggle_theme_ignores_same_theme(self):
        # Given un thème déjà sombre
        self.host.theme = "dark"

        # When on redemande le même thème
        with patch("ui.session_preferences.set_theme") as set_theme:
            self.host.toggle_theme("dark")

        # Then aucune bascule n'a lieu
        set_theme.assert_not_called()

    # Vérifie set language confirmed schedules restart.
    def test_set_language_confirmed_schedules_restart(self):
        # Given un traducteur et une confirmation acceptée
        self.host.translator.set_language = Mock()
        self.host.menu_bar.language_var = Mock()

        # When on change de langue
        with patch("ui.session_preferences.messagebox.askyesno", return_value=True):
            self.host.set_language("en")

        # Then la langue est changée, sauvegardée et le redémarrage programmé
        self.host.translator.set_language.assert_called_once_with("en")
        self.host._save_recent_files.assert_called_once()
        self.host.root.after.assert_called_once_with(
            100, self.host._restart_application
        )

    # Vérifie set language declined restores previous language.
    def test_set_language_declined_restores_previous_language(self):
        # Given une confirmation refusée
        self.host.translator.set_language = Mock()
        self.host.menu_bar.language_var = Mock()

        # When on change de langue
        with patch("ui.session_preferences.messagebox.askyesno", return_value=False):
            self.host.set_language("en")

        # Then la langue précédente est restaurée
        self.host.translator.set_language.assert_called_with("fr")
        self.host.menu_bar.language_var.set.assert_called_once_with("fr")
        self.host._save_recent_files.assert_not_called()

    # Vérifie open recent file on startup schedules load.
    def test_open_recent_file_on_startup_schedules_load(self):
        # Given un fichier récent existant
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        self.host.recent_files = [temp_file.name]

        try:
            # When on ouvre le dernier fichier au démarrage
            self.host._open_recent_file_on_startup()

            # Then le chargement est programmé
            self.host.status_var.set.assert_called_once()
            self.host.root.after.assert_called_once_with(
                50, self.host._load_file_async, temp_file.name
            )
        finally:
            os.unlink(temp_file.name)

    # Vérifie open recent file on startup without file does nothing.
    def test_open_recent_file_on_startup_without_file_does_nothing(self):
        # Given aucun fichier récent
        self.host.recent_files = []

        # When on ouvre le dernier fichier au démarrage
        self.host._open_recent_file_on_startup()

        # Then aucun chargement n'est programmé
        self.host.root.after.assert_not_called()

    # Vérifie open recent file on startup with missing file does nothing.
    def test_open_recent_file_on_startup_with_missing_file_does_nothing(self):
        # Given un fichier récent qui n'existe plus
        self.host.recent_files = ["/tmp/missing.ged"]

        # When on ouvre le dernier fichier au démarrage
        self.host._open_recent_file_on_startup()

        # Then aucun chargement n'est programmé
        self.host.root.after.assert_not_called()

    # Vérifie load recent files warns on unsupported language.
    def test_load_recent_files_warns_on_unsupported_language(self):
        # Given des préférences avec une langue non supportée
        store = Mock()
        store.load.return_value = ([], "/tmp", "xx")
        store.window_size = None
        store.view_preferences = {}
        store.theme = "light"
        self.host.translator.set_language = Mock(side_effect=ValueError)

        # When on charge les préférences
        with patch("ui.session_preferences.RecentFilesStore", return_value=store):
            with patch("ui.session_preferences.set_theme"):
                with patch("ui.session_preferences.apply_app_theme"):
                    with self.assertLogs(
                        "ui.session_preferences", level="WARNING"
                    ) as logs:
                        self.host._load_recent_files()

        # Then un avertissement est journalisé
        self.assertIn("Langue non supportee", logs.output[0])

    # Vérifie apply theme reapplies current entity.
    def test_apply_theme_reapplies_current_entity(self):
        # Given une entité courante et un registre de thème
        self.host.theme_registry = Mock()
        self.host._current_entity = Mock()
        self.host._current_entity_type = "INDI"
        self.host._show_entity_view = Mock()

        # When on applique le thème
        SessionPreferencesMixin._apply_theme(self.host)

        # Then la vue courante est réaffichée
        self.host._show_entity_view.assert_called_once_with(
            "INDI", self.host._current_entity
        )

    # Vérifie set language ignores same language.
    def test_set_language_ignores_same_language(self):
        # Given la langue déjà active
        self.host.translator.language = "fr"
        self.host.translator.set_language = Mock()

        # When on redemande la même langue
        self.host.set_language("fr")

        # Then aucune opération n'a lieu
        self.host.translator.set_language.assert_not_called()
        self.host._save_recent_files.assert_not_called()

    # Vérifie restart application lance une nouvelle instance et quitte.
    def test_restart_application_replaces_process(self):
        # Given un hôte de session
        # When on redémarre l'application
        with patch("ui.session_preferences.os.execv") as execv:
            SessionPreferencesMixin._restart_application(self.host)

        # Then la fenêtre est détruite et le processus est remplacé par
        # une nouvelle instance (sans sys.exit qui perturbe la boucle Tk)
        self.host.root.destroy.assert_called_once()
        execv.assert_called_once_with(sys.executable, [sys.executable, sys.argv[0]])

    # Vérifie apply theme delegates to registry.
    def test_apply_theme_delegates_to_registry(self):
        # Given un registre de thème et un surligneur
        registry = Mock()
        self.host.theme_registry = registry

        # When on applique le thème
        SessionPreferencesMixin._apply_theme(self.host)

        # Then le registre re-thème les widgets et le surligneur se met à jour
        registry.apply_theme.assert_called_once()
        self.host.highlighter.highlight.assert_called_once()

    # Vérifie remember recent file syncs state and menu.
    def test_remember_recent_file_syncs_state_and_menu(self):
        # Given un gestionnaire de fichiers
        self.host.file_manager.last_directory = "/tmp"
        self.host.file_manager.recent_files = ["/tmp/a.ged"]

        # When on mémorise un fichier
        self.host._remember_recent_file("/tmp/a.ged")

        # Then l'état et le menu sont synchronisés
        self.host.file_manager.remember_recent_file.assert_called_once_with(
            "/tmp/a.ged"
        )
        self.assertEqual(self.host.last_directory, "/tmp")
        self.assertEqual(self.host.recent_files, ["/tmp/a.ged"])
        self.host._save_recent_files.assert_called_once()
        self.host.menu_bar.refresh_recent_menu.assert_called_once()


if __name__ == "__main__":
    unittest.main()
