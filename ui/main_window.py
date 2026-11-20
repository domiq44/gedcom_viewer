"""Fenêtre principale : façade d'orchestration de l'interface."""

import logging
import os
import queue
from tkinter import messagebox
from typing import Any

from controllers.app_controller import AppController
from controllers.entity_types import ENTITY_TYPE_BY_CONTEXT
from controllers.navigation_history import NavigationHistory
from ui.application_menu import ApplicationMenu
from ui.entity_display import EntityDisplayMixin
from ui.entity_navigator import EntityNavigator
from ui.entity_view_manager import EntityViewManager
from ui.file_actions import FileActionsMixin
from ui.file_manager import FileManager
from ui.gedcom_file_loader import GedcomFileLoader
from ui.i18n import Translator
from ui.main_window_builder import MainWindowBuilder
from ui.session_preferences import SessionPreferencesMixin
from ui.syntax_highlighter import GedcomHighlighter
from ui.theme_aware import ThemeRegistry
from ui.themes import COLORS
from ui.tooltip import Tooltip
from ui.ui_log_handler import UiLogHandler, UiLogPump
from ui.views.ancestor_tree_view import AncestorTreeView

logger = logging.getLogger(__name__)


class GedcomViewer(SessionPreferencesMixin, FileActionsMixin, EntityDisplayMixin):
    """Fenêtre principale : façade d'orchestration de l'interface."""

    DISPLAY_TYPE_MAP = ENTITY_TYPE_BY_CONTEXT
    _ui_log_handler: Any
    _ui_log_pump: Any
    _ancestor_tree_view: Any
    _ancestor_tree_mode: bool
    _previous_entity_type: Any
    _last_individual_entity: Any
    _last_individual_type: Any

    def __init__(self, root: Any):
        """Initialise la fenêtre, les préférences et l'interface."""
        self.root: Any = root
        self.translator = Translator()
        self.root.title("GEDCOM Viewer 5.5.1")
        self.root.configure(bg=COLORS["background"])
        self.root.minsize(1100, 700)

        self.last_directory = os.path.expanduser("~")
        self.recent_files = self._load_recent_files()
        self.file_manager = FileManager(
            self.root,
            self.translator,
            last_directory=self.last_directory,
            recent_files=self.recent_files,
        )
        self.menu_bar = ApplicationMenu(self.root, self)
        self.controller = AppController(translator=self.translator)
        self._initialize_state()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        MainWindowBuilder(self).build()
        self._update_entity_type_tabs()

        self.highlighter = GedcomHighlighter(self.detail_panel.text_area)
        self.theme_registry.register(self.highlighter)
        self.detail_panel.highlighter = self.highlighter
        self._attach_ui_log_handler()
        self._update_navigation_buttons()
        self._open_recent_file_on_startup()

        self.root.grid_columnconfigure(0, weight=1)

    def _initialize_state(self):
        """Initialise l'historique et les collaborateurs d'état."""
        self.theme_registry = ThemeRegistry()
        self._navigation_history = NavigationHistory()
        self._entity_selection_after_id = None
        self._current_entity_type = None
        self._current_entity = None
        self._ancestor_tree_mode = False
        self._previous_entity_type = None
        self._last_individual_entity = None
        self._last_individual_type = None
        self.entity_navigator = EntityNavigator(
            controller=self.controller,
            history=self._navigation_history,
            on_display=self.display_entity_context,
            on_error=lambda error_key, message_key, **kwargs: messagebox.showerror(
                self.translator.get(error_key),
                self.translator.get(message_key, **kwargs),
            ),
        )
        self.entity_view_manager = EntityViewManager({})

        self.file_loader = GedcomFileLoader(
            root=self.root,
            controller_factory=lambda: AppController(translator=self.translator),
            on_loaded=self._on_file_loaded,
            on_error=self._show_load_error,
            on_loading=lambda: self.status_var.set(
                self.translator.get("ui.loading_last_file")
            ),
        )
        self.load_coordinator = self.file_loader.load_coordinator

    def _attach_ui_log_handler(self):
        """Branche le handler de log vers la barre de statut."""
        if hasattr(self, "_ui_log_handler"):
            return

        log_queue: queue.Queue[str] = queue.Queue()
        self._ui_log_handler = UiLogHandler(log_queue)
        self._ui_log_handler.setFormatter(
            logging.Formatter("%(levelname)s: %(message)s")
        )
        logging.getLogger().addHandler(self._ui_log_handler)
        self._ui_log_pump = UiLogPump(self.root, self.status_var, log_queue)
        self._ui_log_pump.start()

    def show_ancestor_tree(self):
        """Affiche l'arbre d'ascendance horizontal du dernier individu sélectionné."""
        if not self.controller.is_loaded():
            return
        if self._last_individual_entity is None:
            coordinator = getattr(self, "entity_selection_coordinator", None)
            if coordinator is not None:
                self._last_individual_entity = coordinator._last_selected_entities.get(
                    "INDI"
                )
                if self._last_individual_entity is not None:
                    self._last_individual_type = "INDI"
        if self._last_individual_entity is None or self._last_individual_type != "INDI":
            messagebox.showinfo(
                self.translator.get("menu.ancestor_tree_title"),
                self.translator.get("view.ancestor_tree.no_individual"),
            )
            return

        self._switch_to_ancestor_tree_view()

    def _switch_to_ancestor_tree_view(self):
        """Remplace la liste des entités et les vues par l'arbre d'ascendance."""
        main_pane = getattr(self, "main_pane", None)
        ancestor_tree_frame = getattr(self, "ancestor_tree_frame", None)
        if main_pane is None or ancestor_tree_frame is None:
            return
        main_pane.grid_remove()
        ancestor_tree_frame.grid()
        self._ancestor_tree_mode = True

        if hasattr(self, "entity_type_tabs"):
            self.entity_type_tabs.update_selection("ANCESTOR_TREE")

        for widget in ancestor_tree_frame.winfo_children():
            widget.destroy()

        tree_view = AncestorTreeView(
            ancestor_tree_frame,
            lambda: self.controller,
            self.translator,
            individual_pointer=self._last_individual_entity.pointer,
            tooltip_factory=Tooltip,
            on_individual_selected=self._on_ancestor_individual_clicked,
            base_path=getattr(
                self.entity_view_manager.views.get("object"), "base_path", None
            ),
        )
        tree_view.pack(fill="both", expand=True)
        tree_view.apply_theme()
        self._ancestor_tree_view = tree_view

    def _switch_back_to_normal_view(self):
        """Rétablit la liste des entités et les vues de détail."""
        ancestor_tree_frame = getattr(self, "ancestor_tree_frame", None)
        main_pane = getattr(self, "main_pane", None)
        if ancestor_tree_frame is None or main_pane is None:
            return
        ancestor_tree_frame.grid_remove()
        main_pane.grid()
        self._ancestor_tree_mode = False
        self._ancestor_tree_view = None

    def _on_ancestor_individual_clicked(self, pointer: str) -> None:
        """Sélectionne l'individu et recentre l'arbre sans changer de vue.

        Un clic sur un nœud de l'arbre d'ascendance :
        1. sélectionne l'individu comme individu courant (_current_entity) et
           le mémorise dans le coordinateur de sélection pour le type INDI ;
        2. recentre l'arbre sur cet individu (il devient la racine) ;
        3. ne bascule pas vers le type d'entité Individu ni vers la vue
           individuelle détaillée ; l'utilisateur reste sur l'arbre.
        Quand l'utilisateur bascule ensuite vers le type Individu, le
        coordinateur restaure cet individu comme sélectionné.
        """
        if not self.controller.is_loaded() or self._ancestor_tree_view is None:
            return
        entity = self.controller.get_individual(pointer)
        if entity is None:
            return
        self._current_entity = entity
        coordinator = self.entity_selection_coordinator
        coordinator.remember_selection("INDI", entity)
        self._ancestor_tree_view.load_tree(pointer)

    def _on_close(self):
        """Enregistre les préférences et ferme l'application."""
        self._save_recent_files()
        if self._entity_selection_after_id is not None:
            self.root.after_cancel(self._entity_selection_after_id)
            self._entity_selection_after_id = None
        self.file_loader.close()
        self.entity_browser.cancel_pending_search()
        ui_log_handler = getattr(self, "_ui_log_handler", None)
        if ui_log_handler is not None:
            logging.getLogger().removeHandler(ui_log_handler)
            self._ui_log_handler = None
        ui_log_pump = getattr(self, "_ui_log_pump", None)
        if ui_log_pump is not None:
            ui_log_pump.stop()
            self._ui_log_pump = None
        self.root.destroy()
