"""Tests de chargement asynchrone et de fermeture de la fenêtre principale."""

import gc
import logging
import threading
import tkinter as tk
import unittest
import weakref
from unittest.mock import Mock, patch

from tests.main_window_test_case import GedcomViewerTestCase


class TestGedcomViewerLoading(GedcomViewerTestCase):
    """Vérifie le chargement asynchrone, les erreurs et la fermeture."""

    # Vérifie ui status reflects last log message.
    def test_ui_status_reflects_last_log_message(self):
        logger = logging.getLogger("ui.main_window")
        logger.error("test log ui status")

        self.viewer._ui_log_pump._drain()
        self.root.update_idletasks()
        self.assertIn("test log ui status", self.viewer.status_var.get())
        self.assertEqual(
            self.viewer.log_status_frame.status_label.cget("state"), "readonly"
        )

        self.viewer.log_status_frame.status_label.selection_range(0, tk.END)
        self.viewer.log_status_frame.status_label.event_generate("<<Copy>>")

    # Vérifie ui status handles log from worker thread.
    def test_ui_status_handles_log_from_worker_thread(self):
        # Given (Arrange) un journaliseur et la pompe de statut
        logger = logging.getLogger("ui.main_window")
        pump = self.viewer._ui_log_pump

        # When (Act) on journalise depuis un thread worker
        with patch.object(self.viewer.status_var, "set") as set_status:
            worker = threading.Thread(
                target=logger.error, args=("worker log ui status",)
            )
            worker.start()
            worker.join()
            set_status.assert_not_called()

        # Then (Assert) la pompe publie le message sur le thread de l'interface
        pump._drain()
        self.assertIn("worker log ui status", self.viewer.status_var.get())

    # Vérifie load file logs elapsed time.
    def test_load_file_logs_elapsed_time(self):
        filename = "/tmp/private-family.ged"
        self.viewer.controller.get_entity_types.return_value = ["INDI"]
        self.viewer.controller.get_all_entity_type_menu_display_items.return_value = [
            ("Individu", "INDI")
        ]

        with patch("ui.file_actions.time.perf_counter", return_value=12.345):
            with patch.object(self.viewer.entity_browser, "list_entities"):
                with self.assertLogs("ui.file_actions", level="INFO") as logs:
                    self.viewer._on_file_loaded(filename, 10.0, self.viewer.controller)

        self.assertIn("GEDCOM chargé avec succès en 2.345 s", logs.output[-1])
        self.assertNotIn(filename, "\n".join(logs.output))

    # Vérifie sync load without entities keeps previous session.
    def test_sync_load_without_entities_keeps_previous_session(self):
        previous_controller = self.viewer.controller
        loaded_controller = Mock()
        loaded_controller.get_entity_types.return_value = []

        with patch("ui.main_window.messagebox.showerror") as show_error:
            self.viewer._on_file_loaded("/tmp/empty.ged", 0.0, loaded_controller)

        self.assertIs(self.viewer.controller, previous_controller)
        show_error.assert_called_once()

    # Vérifie load error does not log filename or error text.
    def test_load_error_does_not_log_filename_or_error_text(self):
        filename = "/tmp/private-family.ged"
        error = OSError(f"cannot read {filename}")

        with patch("ui.main_window.messagebox.showerror"):
            with self.assertLogs("ui.file_actions", level="ERROR") as logs:
                self.viewer._show_load_error(filename, error)

        output = "\n".join(logs.output)
        self.assertIn("OSError", output)
        self.assertNotIn(filename, output)
        self.assertNotIn("cannot read", output)

    # Vérifie async load publishes controller only after success.
    def test_async_load_publishes_controller_only_after_success(self):
        previous_controller = self.viewer.controller
        loaded_controller = Mock()

        with patch("ui.main_window.AppController", return_value=loaded_controller):
            with patch.object(self.viewer.root, "after"):
                with patch("ui.load_coordinator.threading.Thread") as thread_class:
                    self.viewer._load_file_async("/tmp/test.ged", strict=True)

                    worker = thread_class.return_value
                    worker.start.assert_called_once_with()
                    worker_target = thread_class.call_args.kwargs["target"]
                    worker_target()

        loaded_controller.load_file.assert_called_once()
        self.assertEqual(loaded_controller.load_file.call_args.args, ("/tmp/test.ged",))
        self.assertTrue(loaded_controller.load_file.call_args.kwargs["strict"])
        self.assertIsNotNone(
            loaded_controller.load_file.call_args.kwargs["cancel_event"]
        )
        self.assertIs(self.viewer.controller, previous_controller)

        with patch.object(self.viewer, "_apply_loaded_file") as apply_loaded_file:
            self.viewer.load_coordinator._poll_result()

        self.assertIs(self.viewer.controller, loaded_controller)
        apply_loaded_file.assert_called_once_with("/tmp/test.ged", unittest.mock.ANY)

    # Vérifie apply failure restores previous session.
    def test_apply_failure_restores_previous_session(self):
        previous_controller = self.viewer.controller
        previous_navigator_controller = self.viewer.entity_navigator.controller
        previous_base_path = self.viewer.entity_view_manager.views["object"].base_path
        previous_recent_files = list(self.viewer.recent_files)
        previous_last_directory = self.viewer.last_directory
        previous_controller.get_entity_types.return_value = []
        previous_controller.get_all_entity_type_menu_display_items.return_value = []
        self.viewer.entity_selection_coordinator.set_entity_type_without_refresh("INDI")
        self.viewer.detail_panel.display_raw("raw before load")
        loaded_controller = Mock()
        loaded_controller.get_entity_types.return_value = ["INDI"]

        with patch.object(
            self.viewer,
            "_update_entity_type_tabs",
            side_effect=[RuntimeError("boom"), None],
        ):
            with patch("ui.main_window.messagebox.showerror") as show_error:
                self.viewer._on_file_loaded("/tmp/x.ged", 0.0, loaded_controller)

        self.assertIs(self.viewer.controller, previous_controller)
        self.assertIs(
            self.viewer.entity_navigator.controller, previous_navigator_controller
        )
        self.assertEqual(
            self.viewer.entity_view_manager.views["object"].base_path,
            previous_base_path,
        )
        self.assertEqual(self.viewer.recent_files, previous_recent_files)
        self.assertEqual(self.viewer.last_directory, previous_last_directory)
        self.assertEqual(self.viewer.entity_type_var.get(), "INDI")
        self.assertEqual(self.viewer.detail_panel.raw_content, "raw before load")
        show_error.assert_called_once()

    # Vérifie async load error keeps previous controller.
    def test_async_load_error_keeps_previous_controller(self):
        previous_controller = self.viewer.controller
        error = ValueError("invalid GEDCOM")
        coordinator = self.viewer.load_coordinator
        coordinator._is_loading = True
        coordinator._load_token = 1
        coordinator._results.put((1, "/tmp/test.ged", 1.0, error, None))

        with patch.object(coordinator, "on_error") as show_load_error:
            coordinator._poll_result()

        self.assertIs(self.viewer.controller, previous_controller)
        show_load_error.assert_called_once_with("/tmp/test.ged", error)

    # Vérifie empty loaded controller keeps previous session.
    def test_empty_loaded_controller_keeps_previous_session(self):
        previous_controller = self.viewer.controller
        previous_navigator_controller = self.viewer.entity_navigator.controller
        loaded_controller = Mock()
        loaded_controller.get_entity_types.return_value = []

        with patch("ui.main_window.messagebox.showerror") as show_error:
            with patch.object(self.viewer, "_prepare_loaded_file") as prepare_file:
                self.viewer._on_file_loaded("/tmp/empty.ged", 1.0, loaded_controller)

        self.assertIs(self.viewer.controller, previous_controller)
        self.assertIs(
            self.viewer.entity_navigator.controller, previous_navigator_controller
        )
        prepare_file.assert_not_called()
        show_error.assert_called_once()

    # Vérifie async load result is ignored when closing.
    def test_async_load_result_is_ignored_when_closing(self):
        coordinator = self.viewer.load_coordinator
        coordinator.close()
        coordinator._results.put((1, "/tmp/test.ged", 1.0, None, Mock()))

        with patch.object(self.viewer, "_apply_loaded_file") as apply_loaded_file:
            with patch.object(self.viewer, "_show_load_error") as show_load_error:
                coordinator._poll_result()

        apply_loaded_file.assert_not_called()
        show_load_error.assert_not_called()

    # Vérifie close stops async loading and destroys window.
    def test_close_stops_async_loading_and_destroys_window(self):
        ui_log_handler = self.viewer._ui_log_handler
        root_logger = logging.getLogger()
        self.assertIn(ui_log_handler, root_logger.handlers)

        with patch.object(self.viewer, "_save_recent_files") as save_settings:
            with patch.object(self.viewer.root, "destroy") as destroy:
                self.viewer._on_close()

        self.assertFalse(self.viewer.load_coordinator.is_loading)
        self.assertNotIn(ui_log_handler, root_logger.handlers)
        save_settings.assert_called_once_with()
        destroy.assert_called_once_with()

    # Vérifie close file releases loaded models and keeps recent files.
    def test_close_file_releases_loaded_models_and_keeps_recent_files(self):
        controller = Mock()
        controller.is_loaded.return_value = True
        controller_reference = weakref.ref(controller)
        self.viewer.controller = controller
        self.viewer.entity_navigator.controller = controller

        entity = Mock(pointer="@I1@")
        entity_reference = weakref.ref(entity)
        self.viewer.entity_browser._entity_by_item_id["0"] = entity
        self.viewer.entity_browser.filtered_entities.append(entity)
        self.viewer.entity_browser.entity_tree.insert(
            "", "end", iid="0", values=("Test person", "@I1@")
        )
        self.viewer._navigation_history.entries = [{"entity": entity}]
        self.viewer._navigation_history.index = 0
        self.viewer._display_raw_text("0 @I1@ INDI")
        self.viewer.recent_files = ["/tmp/example.ged"]
        self.viewer.entity_browser.search_var.set("person")

        preview = Mock()
        preview_reference = weakref.ref(preview)
        self.viewer.entity_view_manager.views["object"]._preview_photo = preview
        self.viewer.entity_view_manager.views["object"].preview_label.image = preview

        del controller
        del entity
        del preview
        self.viewer.close_file()
        gc.collect()

        self.assertIsNone(controller_reference())
        self.assertIsNone(entity_reference())
        self.assertIsNone(preview_reference())
        self.assertFalse(self.viewer.controller.is_loaded())
        self.assertIs(self.viewer.entity_navigator.controller, self.viewer.controller)
        self.assertEqual(self.viewer.entity_browser.entity_tree.get_children(), ())
        self.assertEqual(self.viewer.entity_browser.filtered_entities, [])
        self.assertEqual(self.viewer.entity_browser.search_var.get(), "")
        self.assertIsNone(self.viewer.entity_browser._search_after_id)
        self.assertEqual(self.viewer._navigation_history.entries, [])
        self.assertIsNone(
            self.viewer.entity_view_manager.views["object"]._preview_photo
        )
        self.assertIsNone(
            self.viewer.entity_view_manager.views["object"].preview_label.image
        )
        self.assertEqual(
            self.viewer.detail_panel.text_area.get("1.0", tk.END).strip(), ""
        )
        self.assertEqual(self.viewer.recent_files, ["/tmp/example.ged"])
