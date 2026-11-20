"""Actions de haut niveau liées aux fichiers GEDCOM."""

import gc
import logging
import os
import time
from tkinter import filedialog, messagebox
from typing import Any

from controllers.app_controller import AppController

logger = logging.getLogger(__name__)


class FileActionsMixin:
    """Gère l'ouverture, le chargement et la fermeture des fichiers GEDCOM."""

    root: Any
    translator: Any
    file_manager: Any
    file_loader: Any
    load_coordinator: Any
    controller: Any
    entity_navigator: Any
    entity_view_manager: Any
    entity_selection_coordinator: Any
    entity_browser: Any
    entity_type_var: Any
    entity_type_tabs: Any
    detail_panel: Any
    menu_bar: Any
    highlighter: Any
    status_var: Any
    recent_files: Any
    last_directory: Any
    _navigation_history: Any
    _current_entity_type: Any
    _current_entity: Any
    _sync_file_manager: Any
    _save_recent_files: Any
    _remember_recent_file: Any
    _clear_entity_views: Any
    _show_entity_view: Any
    _display_raw_text: Any
    _update_entity_type_tabs: Any
    _update_entity_type_tab_state: Any
    _update_navigation_buttons: Any

    def _file_dialog_options(self):
        """Retourne les options du dialogue de fichier."""
        self._sync_file_manager()
        return self.file_manager.file_dialog_options()

    def _load_file_async(self, filename, strict=False):
        """Lance le chargement asynchrone d'un fichier."""
        if not self.file_loader.load_async(filename, strict=strict):
            self.status_var.set(self.translator.get("ui.loading_in_progress"))

    def _snapshot_session_state(self):
        """Capture l'état UI nécessaire pour restaurer une session."""
        history = self._navigation_history
        context = None
        if 0 <= history.index < len(history.entries):
            context = history.entries[history.index]
        raw_content = (
            context.get("raw_block")
            if context is not None
            else self.detail_panel.raw_content
        )
        return {
            "controller": self.controller,
            "navigator_controller": self.entity_navigator.controller,
            "base_path": getattr(
                self.entity_view_manager.views["object"], "base_path", None
            ),
            "recent_files": list(self.recent_files),
            "last_directory": self.last_directory,
            "entity_type": self.entity_type_var.get(),
            "current_entity_type": self._current_entity_type,
            "current_entity": self._current_entity,
            "history_entries": list(history.entries),
            "history_index": history.index,
            "raw_content": raw_content,
            "search_query": self.entity_browser.search_var.get(),
            "status": self.status_var.get(),
            "selection_memory": (
                self.entity_selection_coordinator.snapshot_selection_memory()
            ),
        }

    def _restore_session_state(self, state):
        """Restaure l'état UI capturé avant un chargement."""
        self.controller = state["controller"]
        self.entity_navigator.controller = state["navigator_controller"]
        self.entity_view_manager.views["object"].set_base_path(state["base_path"])
        self.recent_files[:] = state["recent_files"]
        self.last_directory = state["last_directory"]
        self._sync_file_manager()
        self._save_recent_files()
        if hasattr(self, "menu_bar"):
            self.menu_bar.refresh_recent_menu()

        self.entity_selection_coordinator.restore_selection_memory(
            state["selection_memory"]
        )
        self._navigation_history.entries = list(state["history_entries"])
        self._navigation_history.index = state["history_index"]
        self.entity_selection_coordinator.set_entity_type_without_refresh(
            state["entity_type"]
        )
        self._update_entity_type_tabs()
        self._update_entity_type_tab_state(state["entity_type"])
        self.entity_browser.cancel_pending_search()
        self.entity_browser.search_var.set(state["search_query"])
        self.entity_browser.refresh_entities(state["search_query"])

        current_entity = state["current_entity"]
        if current_entity is not None:
            self.entity_browser.select_entity(current_entity)
            self._show_entity_view(state["current_entity_type"], current_entity)
        else:
            self._clear_entity_views()
        self._display_raw_text(state["raw_content"])
        self.highlighter.highlight()
        self._update_navigation_buttons()
        self.status_var.set(state["status"])

    def _on_file_loaded(self, filename, load_started_at, loaded_controller):
        """Publie le contrôleur chargé après succès."""
        if not loaded_controller.get_entity_types():
            logger.warning("Aucune entité trouvée dans le fichier GEDCOM")
            messagebox.showerror(
                self.translator.get("ui.error"),
                self.translator.get("ui.no_entities"),
            )
            return

        previous_state = self._snapshot_session_state()

        self.controller = loaded_controller
        self.entity_navigator.controller = loaded_controller
        try:
            self._apply_loaded_file(filename, load_started_at)
        except Exception as exc:
            logger.error(
                "Échec de l'application du GEDCOM chargé (%s)", type(exc).__name__
            )
            self._restore_session_state(previous_state)
            self._show_load_error(filename, exc)

    def _show_load_error(self, filename, error):
        """Affiche une erreur de chargement."""
        logger.error("Échec du chargement du GEDCOM (%s)", type(error).__name__)
        messagebox.showerror(
            self.translator.get("ui.error"),
            self.translator.get("ui.load_error", error=error),
        )

    def _apply_loaded_file(self, filename, load_started_at):
        """Applique un fichier chargé à l'interface."""
        self._prepare_loaded_file(filename)

        entity_types = self.controller.get_entity_types()
        self._update_entity_type_tabs()
        self.entity_type_var.set(entity_types[0])
        load_duration = time.perf_counter() - load_started_at
        logger.info("GEDCOM chargé avec succès en %.3f s", load_duration)

    def _prepare_loaded_file(self, filename):
        """Prépare l'interface après chargement."""
        base_path = os.path.dirname(filename)
        self.entity_view_manager.views["object"].set_base_path(base_path)
        logger.info("Base de chemins multimédia définie")
        self.entity_selection_coordinator.clear_selection_memory()
        self._restore_last_selected_entities()
        self._remember_recent_file(filename)
        self._clear_entity_views()
        self._navigation_history.reset()
        self._update_navigation_buttons()

    def _restore_last_selected_entities(self):
        """Restaure la dernière sélection par type depuis les préférences."""
        pointers = getattr(self, "last_selected_entities", {}) or {}

        def resolve_entity(pointer):
            """Retourne l'entité correspondant au pointeur."""
            return self.controller.get_entity(pointer)

        self.entity_selection_coordinator.load_selection_pointers(
            pointers, resolve_entity
        )
        indi_entity = self.entity_selection_coordinator._last_selected_entities.get(
            "INDI"
        )
        if indi_entity is not None:
            self._last_individual_entity = indi_entity
            self._last_individual_type = "INDI"

    def open_recent_file(self, filename):
        """Ouvre un fichier récent."""
        self._load_file_async(filename)

    def close_file(self):
        """Ferme le fichier courant."""
        if self.load_coordinator.is_loading or not self.controller.is_loaded():
            return

        self.controller = AppController(translator=self.translator)
        self.entity_navigator.controller = self.controller
        self.entity_type_var.set("")
        self._update_entity_type_tabs()
        self.entity_selection_coordinator.clear_selection_memory()
        self.entity_browser.clear()
        self._clear_entity_views()
        self._display_raw_text("")
        self.entity_view_manager.views["object"].set_base_path("")
        self._navigation_history.reset()
        self._update_navigation_buttons()
        self.status_var.set(self.translator.get("ui.ready"))
        gc.collect()

    def open_validated_file(self):
        """Ouvre un fichier en mode validation stricte."""
        filename = filedialog.askopenfilename(
            title=self.translator.get("ui.choose_file_validate"),
            filetypes=[("GEDCOM files", "*.ged")],
            **self._file_dialog_options(),
        )
        if not filename:
            return

        self._load_file_async(filename, strict=True)

    def load_file(self):
        """Ouvre un fichier GEDCOM."""
        filename = filedialog.askopenfilename(
            title=self.translator.get("ui.choose_file"),
            filetypes=[("GEDCOM files", "*.ged")],
            **self._file_dialog_options(),
        )
        if not filename:
            return

        self._load_file_async(filename)
