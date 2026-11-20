"""Tests des préférences de session de la fenêtre principale."""

from unittest.mock import patch

from tests.main_window_test_case import GedcomViewerTestCase
from ui.themes import COLORS, set_theme


class TestGedcomViewerPreferences(GedcomViewerTestCase):
    """Vérifie le thème, les fichiers récents et les cases de vue."""

    # Vérifie toggle theme reapplies widget colors.
    def test_toggle_theme_reapplies_widget_colors(self):
        # Given (Arrange) un thème clair appliqué aux widgets
        set_theme("light")
        self.viewer.theme = "light"
        self.viewer._apply_theme()
        light_header = self.viewer.app_header.cget("bg")
        # When (Act) on bascule vers le thème sombre
        try:
            self.viewer.toggle_theme("dark")
            # Then (Assert) les widgets tk reflètent la palette sombre
            self.assertEqual(
                self.viewer.app_header.cget("bg"), COLORS["header_background"]
            )
            self.assertEqual(
                self.viewer.entity_browser.panel.title_label.cget("fg"),
                COLORS["section_title"],
            )
            self.assertNotEqual(self.viewer.app_header.cget("bg"), light_header)
        finally:
            set_theme("light")

    # Vérifie clear recent files removes all entries.
    def test_clear_recent_files_removes_all_entries(self):
        self.viewer.recent_files = ["/tmp/one.ged", "/tmp/two.ged"]
        with patch.object(self.viewer, "_save_recent_files") as save_recent:
            self.viewer.clear_recent_files()

        self.assertEqual(self.viewer.recent_files, [])
        save_recent.assert_called_once_with()

    # Vérifie save recent files writes settings and last directory.
    def test_save_recent_files_writes_settings_and_last_directory(self):
        self.viewer.recent_files = ["/tmp/example.ged"]
        self.viewer.last_directory = "/tmp"
        self.viewer.detail_panel.indent_var.set(False)
        self.viewer.detail_panel.show_gedcom_view_var.set(False)
        self.viewer.detail_panel.show_entity_view_var.set(True)

        with patch.object(self.viewer.root, "winfo_width", return_value=1280):
            with patch.object(self.viewer.root, "winfo_height", return_value=800):
                with patch("ui.session_preferences.open", create=True) as open_file:
                    self.viewer._save_recent_files()

        write_mock = open_file.return_value.__enter__.return_value.write
        written = "".join(call_args.args[0] for call_args in write_mock.call_args_list)
        self.assertIn('"recent_files": ["/tmp/example.ged"]', written)
        self.assertIn('"last_directory": "/tmp"', written)
        self.assertIn('"window_size": {"width": 1280, "height": 800}', written)
        self.assertIn(
            '"view_preferences": {"indent": false, "show_gedcom_view": false, "show_entity_view": true, "max_age_for_deceased": 110}',
            written,
        )

    # Vérifie load recent files restores window size.
    def test_load_recent_files_restores_window_size(self):
        with patch("ui.session_preferences.RecentFilesStore") as store_factory:
            store = store_factory.return_value
            store.load.return_value = ([], self.viewer.last_directory, None)
            store.window_size = (1280, 800)

            with patch.object(self.viewer.root, "geometry") as set_geometry:
                self.viewer._load_recent_files()

        set_geometry.assert_called_once_with("1280x800")

    # Vérifie view preferences restore checkbox states.
    def test_view_preferences_restore_checkbox_states(self):
        self.viewer.view_preferences = {
            "indent": False,
            "show_gedcom_view": False,
            "show_entity_view": True,
        }

        self.viewer._apply_view_preferences()

        self.assertFalse(self.viewer.detail_panel.indent_var.get())
        self.assertTrue(self.viewer.detail_panel.show_entity_view_var.get())
        self.assertFalse(self.viewer.detail_panel.show_gedcom_view_var.get())
        self.assertEqual(
            self.viewer.detail_panel.split_pane.paneconfigure(
                self.viewer.detail_panel.gedcom_frame, "hide"
            )[-1],
            1,
        )
        self.assertEqual(
            self.viewer.detail_panel.split_pane.paneconfigure(
                self.viewer.detail_panel.entity_detail_frame, "hide"
            )[-1],
            0,
        )

    # Vérifie save recent files logs write errors.
    def test_save_recent_files_logs_write_errors(self):
        self.viewer.recent_files = ["/tmp/example.ged"]

        with patch(
            "ui.session_preferences.open", side_effect=OSError("permission denied")
        ):
            with self.assertLogs("ui.session_preferences", level="WARNING") as logs:
                self.viewer._save_recent_files()

        self.assertIn(
            "Impossible d'enregistrer la liste des fichiers récents", logs.output[0]
        )

    # Vérifie load recent files logs read errors.
    def test_load_recent_files_logs_read_errors(self):
        with patch("ui.session_preferences.os.path.isfile", return_value=True):
            with patch(
                "ui.session_preferences.open", side_effect=OSError("permission denied")
            ):
                with self.assertLogs("ui.session_preferences", level="WARNING") as logs:
                    recent_files = self.viewer._load_recent_files()

        self.assertEqual(recent_files, [])
        self.assertIn(
            "Impossible de lire la liste des fichiers récents", logs.output[0]
        )
