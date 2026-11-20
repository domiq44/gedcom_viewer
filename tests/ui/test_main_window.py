"""Tests de la fenêtre principale : assemblage, démarrage et menus."""

import os
import tempfile
import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from tests.main_window_test_case import GedcomViewerTestCase
from ui.app_header import AppHeader
from ui.application_menu import ApplicationMenu as MenuBar
from ui.detail_panel import DetailPanel
from ui.entity_type_panel import EntityTypePanel
from ui.file_manager import FileManager
from ui.main_window import GedcomViewer
from ui.themes import COLORS


class TestGedcomViewer(GedcomViewerTestCase):
    """Vérifie l'assemblage, le démarrage et les menus de la fenêtre principale."""

    # Vérifie opens last recent file on startup.
    def test_opens_last_recent_file_on_startup(self):
        root = tk.Tk()
        root.withdraw()
        viewer = None

        try:
            with (
                patch.object(
                    GedcomViewer,
                    "_load_recent_files",
                    return_value=["/tmp/last_gedcom.ged"],
                ),
                patch("ui.main_window.os.path.isfile", return_value=True),
                patch.object(GedcomViewer, "_load_file_async") as load_file,
                patch.object(root, "after") as schedule,
            ):
                viewer = GedcomViewer(root)

            startup_call = next(
                call
                for call in schedule.call_args_list
                if call.args[0] == 50 and call.args[2] == "/tmp/last_gedcom.ged"
            )
            startup_call.args[1](*startup_call.args[2:])
            load_file.assert_called_once_with("/tmp/last_gedcom.ged")
        finally:
            if viewer is not None:
                viewer._on_close()
            else:
                root.destroy()

    # Vérifie startup logs when no recent file is available.
    def test_startup_logs_when_no_recent_file_is_available(self):
        with self.assertLogs("ui.session_preferences", level="INFO") as logs:
            self.viewer._open_recent_file_on_startup()

        self.assertIn(
            "Aucun fichier GEDCOM récent à charger au démarrage",
            logs.output[0],
        )

    # Vérifie open validated file uses strict loading.
    def test_open_validated_file_uses_strict_loading(self):
        with patch(
            "ui.file_actions.filedialog.askopenfilename",
            return_value="/tmp/validated.ged",
        ):
            with patch.object(self.viewer, "_load_file_async") as load_file:
                self.viewer.open_validated_file()

        load_file.assert_called_once_with("/tmp/validated.ged", strict=True)

    # Vérifie set language saves and schedules restart.
    def test_set_language_saves_and_schedules_restart(self):
        with patch("ui.main_window.messagebox.askyesno", return_value=True):
            with patch.object(self.viewer, "_save_recent_files") as save_settings:
                with patch.object(self.viewer.root, "after") as schedule_restart:
                    self.viewer.set_language("fr")

        self.assertEqual(self.viewer.translator.language, "fr")
        save_settings.assert_called_once_with()
        schedule_restart.assert_called_once_with(100, self.viewer._restart_application)

    # Vérifie set language decline restores previous language.
    def test_set_language_decline_restores_previous_language(self):
        with patch.object(self.viewer, "_save_recent_files") as save_settings:
            with patch("ui.main_window.messagebox.askyesno", return_value=False):
                self.viewer.set_language("fr")

            self.assertEqual(self.viewer.translator.language, "en")
        save_settings.assert_not_called()

    # Vérifie file dialog uses last directory.
    def test_file_dialog_uses_last_directory(self):
        temp_dir = tempfile.gettempdir()
        self.viewer.last_directory = temp_dir

        with patch(
            "ui.file_actions.filedialog.askopenfilename",
            return_value=os.path.join(temp_dir, "example.ged"),
        ) as askopenfilename:
            with patch.object(self.viewer, "_load_file_async"):
                self.viewer.load_file()

        self.assertEqual(askopenfilename.call_args.kwargs["initialdir"], temp_dir)

    # Vérifie entity type panel updates selected button state.
    def test_entity_type_panel_updates_selected_button_state(self):
        panel = EntityTypePanel(
            self.root,
            self.viewer.translator,
            selected_type_var=tk.StringVar(value="FAM"),
        )
        panel.set_items([("Individu", "INDI"), ("Famille", "FAM")])

        panel.update_selection("FAM")

        self.assertEqual(panel._buttons["FAM"].cget("bg"), COLORS["sidebar_active"])
        self.assertEqual(panel._buttons["INDI"].cget("bg"), COLORS["sidebar"])

    # Vérifie entity list view titles filter and list.
    def test_entity_list_view_titles_filter_and_list(self):
        panel = self.viewer.entity_browser.panel

        self.assertEqual(
            panel.title_label.cget("text"), self.viewer.translator.get("ui.entities")
        )
        self.assertEqual(
            panel.search_label.cget("text"), self.viewer.translator.get("ui.search")
        )
        self.assertEqual(
            panel.search_entry.grid_info()["row"],
            panel.clear_search_button.grid_info()["row"],
        )
        self.assertGreater(
            int(panel.entity_tree.grid_info()["row"]),
            int(panel.search_entry.grid_info()["row"]),
        )

    # Vérifie detail panel displays raw content.
    def test_detail_panel_displays_raw_content(self):
        panel = DetailPanel(self.root, self.viewer.translator)
        panel.display_raw("0 @I1@ INDI")

        self.assertEqual(panel.text_area.get("1.0", tk.END).strip(), "0 @I1@ INDI")

    # Vérifie detail panel indents gedcom by default.
    def test_detail_panel_indents_gedcom_by_default(self):
        panel = DetailPanel(self.root, self.viewer.translator)
        panel.display_raw("0 @I1@ INDI\n1 NAME John /DOE/")

        self.assertTrue(panel.indent_var.get())
        self.assertIn("  1 NAME John /DOE/", panel.text_area.get("1.0", tk.END))

    # Vérifie entity view is visible by default and both views are toggleable.
    def test_entity_view_is_visible_by_default_and_both_views_are_toggleable(self):
        tooltip_factory = Mock()
        panel = DetailPanel(
            self.root, self.viewer.translator, tooltip_factory=tooltip_factory
        )
        self.assertFalse(panel.show_gedcom_view_var.get())
        self.assertTrue(panel.show_entity_view_var.get())
        self.assertIs(panel.show_gedcom_view_checkbox.master, panel.gedcom_header)
        self.assertIs(panel.show_entity_view_checkbox.master, panel.entity_header)
        self.assertIsNot(panel.show_entity_view_checkbox.master, panel.gedcom_frame)
        self.assertEqual(int(panel.gedcom_header.grid_info()["column"]), 0)
        self.assertEqual(int(panel.entity_header.grid_info()["column"]), 1)
        self.assertEqual(panel.entity_header.grid_info()["sticky"], "w")
        self.assertIs(panel.copy_button.master, panel.gedcom_header)
        self.assertEqual(panel.copy_button.cget("style"), "Copy.TButton")
        self.assertEqual(panel.copy_button.cget("text"), "⧉")
        self.assertTrue(panel.copy_button.instate(["disabled"]))
        self.assertEqual(panel.indent_checkbox.cget("state"), tk.DISABLED)
        tooltip_factory.assert_called_once_with(
            panel.copy_button, self.viewer.translator.get("ui.copy_gedcom")
        )
        self.assertIs(panel.indent_checkbox.master, panel.gedcom_header)
        self.assertEqual(panel.gedcom_title.cget("text"), "GEDCOM")
        self.assertEqual(
            panel.entity_view_title.cget("text"),
            self.viewer.translator.get("ui.entity_view"),
        )
        self.assertEqual(panel.text_area.cget("relief"), "flat")
        self.assertEqual(panel.entity_detail_container.cget("relief"), "flat")
        self.assertEqual(
            panel.text_area.cget("bg"),
            panel.entity_detail_container.cget("bg"),
        )
        # Chaque toggle doit inverser l'état du panneau concerné, quel que soit
        # l'état initial laissé par les tests précédents sur le même root Tk.
        gedcom_hidden_before = (
            panel.split_pane.paneconfigure(panel.gedcom_frame, "hide")[-1] == 1
        )
        panel.show_gedcom_view_checkbox.invoke()
        self.assertTrue(panel.show_gedcom_view_var.get())
        self.assertTrue(panel.show_entity_view_var.get())
        self.assertTrue(panel.copy_button.instate(["!disabled"]))
        self.assertEqual(panel.indent_checkbox.cget("state"), tk.NORMAL)
        gedcom_hidden_after = (
            panel.split_pane.paneconfigure(panel.gedcom_frame, "hide")[-1] == 1
        )
        self.assertNotEqual(gedcom_hidden_after, gedcom_hidden_before)

        entity_hidden_before = (
            panel.split_pane.paneconfigure(panel.entity_detail_frame, "hide")[-1] == 1
        )
        panel.show_entity_view_checkbox.invoke()
        self.assertFalse(panel.show_entity_view_var.get())
        entity_hidden_after = (
            panel.split_pane.paneconfigure(panel.entity_detail_frame, "hide")[-1] == 1
        )
        self.assertNotEqual(entity_hidden_after, entity_hidden_before)

        gedcom_hidden_before = (
            panel.split_pane.paneconfigure(panel.gedcom_frame, "hide")[-1] == 1
        )
        panel.show_gedcom_view_checkbox.invoke()
        self.assertFalse(panel.show_gedcom_view_var.get())
        self.assertTrue(panel.show_entity_view_var.get())
        self.assertTrue(panel.copy_button.instate(["disabled"]))
        self.assertEqual(panel.indent_checkbox.cget("state"), tk.DISABLED)
        gedcom_hidden_after = (
            panel.split_pane.paneconfigure(panel.gedcom_frame, "hide")[-1] == 1
        )
        self.assertNotEqual(gedcom_hidden_after, gedcom_hidden_before)

        entity_hidden_before = (
            panel.split_pane.paneconfigure(panel.entity_detail_frame, "hide")[-1] == 1
        )
        panel.show_entity_view_checkbox.invoke()
        self.assertFalse(panel.show_entity_view_var.get())
        self.assertTrue(panel.show_gedcom_view_var.get())
        self.assertTrue(panel.copy_button.instate(["!disabled"]))
        self.assertEqual(panel.indent_checkbox.cget("state"), tk.NORMAL)
        entity_hidden_after = (
            panel.split_pane.paneconfigure(panel.entity_detail_frame, "hide")[-1] == 1
        )
        self.assertNotEqual(entity_hidden_after, entity_hidden_before)

    # Vérifie header columns follow splitter position.
    def test_header_columns_follow_splitter_position(self):
        panel = DetailPanel(self.root, self.viewer.translator)
        panel.show_gedcom_view_var.set(True)
        panel.show_entity_view_var.set(True)

        with patch.object(panel.split_pane, "sash_coord", return_value=(312, 0)):
            panel._sync_header_columns()

        left_column = panel.view_toolbar.grid_columnconfigure(0)
        self.assertEqual(int(left_column["minsize"]), 312)
        self.assertEqual(int(left_column["weight"]), 0)

        panel.show_entity_view_var.set(False)
        panel._sync_header_columns()

        left_column = panel.view_toolbar.grid_columnconfigure(0)
        self.assertEqual(int(left_column["minsize"]), 0)
        self.assertEqual(int(left_column["weight"]), 1)

    # Vérifie detail panel can indent gedcom by level.
    def test_detail_panel_can_indent_gedcom_by_level(self):
        panel = DetailPanel(self.root, self.viewer.translator)
        panel.indent_var.set(True)
        panel.display_raw("0 @I1@ INDI\n1 NAME John /DOE/\n2 GIVN John\n0 TRLR")

        rendered = panel.text_area.get("1.0", tk.END)
        self.assertIn("0 @I1@ INDI", rendered)
        self.assertIn("  1 NAME John /DOE/", rendered)
        self.assertIn("    2 GIVN John", rendered)
        self.assertIn("0 TRLR", rendered)

    # Vérifie detail panel can copy raw gedcom to clipboard.
    def test_detail_panel_can_copy_raw_gedcom_to_clipboard(self):
        panel = DetailPanel(self.root, self.viewer.translator)
        panel.show_gedcom_view_checkbox.invoke()
        panel.indent_var.set(True)
        panel.display_raw("0 @I1@ INDI\n1 NAME John /DOE/\n0 TRLR")

        with (
            patch.object(self.root, "clipboard_clear") as clear,
            patch.object(self.root, "clipboard_append") as append,
        ):
            panel.copy_button.invoke()

        clear.assert_called_once_with()
        append.assert_called_once()
        self.assertIn("  1 NAME John /DOE/", append.call_args[0][0])
        self.assertEqual(panel.copy_button.cget("text"), "✓")

    # Vérifie app header displays title and subtitle.
    def test_app_header_displays_title_and_subtitle(self):
        header = AppHeader(self.root, self.viewer.translator)

        self.assertEqual(
            header.app_title.cget("text"), self.viewer.translator.get("app.title")
        )
        self.assertEqual(
            header.app_subtitle.cget("text"), self.viewer.translator.get("app.subtitle")
        )

    # Vérifie file manager remembers last directory for open dialog.
    def test_file_manager_remembers_last_directory_for_open_dialog(self):
        temp_dir = tempfile.gettempdir()
        manager = FileManager(
            self.root, self.viewer.translator, last_directory=temp_dir
        )

        options = manager.file_dialog_options()

        self.assertEqual(options["initialdir"], temp_dir)

    # Vérifie menu bar refreshes recent entries.
    def test_menu_bar_refreshes_recent_entries(self):
        self.viewer.recent_files = ["/tmp/recent.ged"]
        menu = MenuBar(self.root, self.viewer)

        self.assertEqual(menu.recent_menu.entrycget(0, "label"), "/tmp/recent.ged")

    # Vérifie file menu contains close file command.
    def test_file_menu_contains_close_file_command(self):
        menu = self.viewer.menu_bar

        self.assertEqual(
            menu.file_menu.entrycget(menu.close_file_index, "label"),
            self.viewer.translator.get("menu.close_file"),
        )

    # Vérifie file menu states follow loaded file.
    def test_file_menu_states_follow_loaded_file(self):
        menu = self.viewer.menu_bar
        self.viewer.controller.is_loaded.return_value = False
        menu.refresh_state()

        self.assertEqual(menu.file_menu.entrycget(0, "state"), "normal")
        self.assertEqual(
            menu.file_menu.entrycget(menu.close_file_index, "state"), "disabled"
        )
        self.assertEqual(
            menu.file_menu.entrycget(menu.inspect_index, "state"), "disabled"
        )
        self.assertEqual(
            menu.file_menu.entrycget(menu.navigation_index, "state"), "disabled"
        )

        self.viewer.controller.is_loaded.return_value = True
        menu.refresh_state()

        self.assertEqual(
            menu.file_menu.entrycget(menu.close_file_index, "state"), "normal"
        )
        self.assertEqual(
            menu.file_menu.entrycget(menu.inspect_index, "state"), "normal"
        )
        self.assertEqual(
            menu.file_menu.entrycget(menu.navigation_index, "state"), "normal"
        )
        self.assertEqual(menu.navigation_menu.entrycget(0, "state"), "disabled")
        self.assertEqual(menu.navigation_menu.entrycget(1, "state"), "disabled")

    # Vérifie empty entity list clears raw and detail views.
    def test_empty_entity_list_clears_raw_and_detail_views(self):
        self.viewer.controller.is_loaded.return_value = True
        self.viewer.controller.get_entity_types.return_value = ["INDI"]
        self.viewer.controller.get_entity_list_items.return_value = []
        self.viewer.entity_type_var.set("INDI")

        self.viewer._show_entity_view("INDI", object())
        self.viewer._display_raw_text("0 @I1@ INDI")

        self.viewer.list_entities()

        self.assertEqual(
            self.viewer.detail_panel.text_area.get("1.0", tk.END).strip(), ""
        )
        self.assertEqual(
            self.viewer.entity_view_manager.views["individual"].title_label.cget(
                "text"
            ),
            self.viewer.translator.get("view.individual"),
        )

    # Vérifie clic sur arbre sélectionne et recentre sans basculer la vue.
    def test_ancestor_individual_clicked_selects_and_recentres_without_view_switch(
        self,
    ):
        # Given un individu et une vue d'arbre simulée
        entity = Mock()
        entity.pointer = "@I2@"
        self.viewer.controller.get_individual.return_value = entity
        self.viewer.controller.is_loaded.return_value = True
        tree_view = Mock()
        self.viewer._ancestor_tree_view = tree_view
        coordinator = self.viewer.entity_selection_coordinator

        # When on clique sur un nœud de l'arbre
        with (
            patch.object(coordinator, "set_entity_type_without_refresh") as set_type,
            patch.object(coordinator, "remember_selection") as remember,
            patch.object(self.viewer.entity_browser, "select_entity") as select_entity,
        ):
            self.viewer._on_ancestor_individual_clicked("@I2@")

        # Then l'individu est sélectionné comme courant
        self.assertEqual(self.viewer._current_entity, entity)
        # le type d'entité affiché n'est pas changé (reste Ancestor tree)
        set_type.assert_not_called()
        # l'individu est mémorisé pour le type INDI (restauré au basculement)
        remember.assert_called_once_with("INDI", entity)
        select_entity.assert_not_called()
        # l'arbre est recentré sur l'individu cliqué
        tree_view.load_tree.assert_called_once_with("@I2@")
        # la vue individuelle n'est pas basculée (pas de résolution d'affichage)
        self.viewer.controller.get_entity_display_info.assert_not_called()


if __name__ == "__main__":
    unittest.main()
