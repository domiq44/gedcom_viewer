"""Actions liées à la sélection, l'affichage et la navigation des entités."""

from tkinter import messagebox
from typing import Any


class EntityDisplayMixin:
    """Gère la sélection, l'affichage et la navigation des entités."""

    root: Any
    translator: Any
    controller: Any
    entity_navigator: Any
    entity_view_manager: Any
    entity_selection_coordinator: Any
    entity_browser: Any
    entity_type_tabs: Any
    entity_type_var: Any
    nav_toolbar: Any
    menu_bar: Any
    detail_panel: Any
    highlighter: Any
    status_var: Any
    _navigation_history: Any
    _entity_selection_after_id: Any
    _current_entity_type: Any
    _current_entity: Any
    _ancestor_tree_mode: bool
    _previous_entity_type: Any
    _last_individual_entity: Any
    _last_individual_type: Any
    DISPLAY_TYPE_MAP: Any

    def _switch_to_ancestor_tree_view(self) -> None:
        """Passe à l'affichage de l'arbre d'ascendance (implémenté par GedcomViewer)."""
        ...

    def _switch_back_to_normal_view(self) -> None:
        """Revient à l'affichage normal (implémenté par GedcomViewer)."""
        ...

    def _clear_entity_views(self, keep_type=None):
        """Réinitialise les vues d'entité."""
        self.entity_view_manager.clear(keep_type=keep_type)
        if keep_type is None:
            self._current_entity_type = None
            self._current_entity = None
            self.detail_panel.set_context(None, None)

    def _show_entity_view(self, entity_type, entity=None):
        """Affiche la vue d'un type d'entité."""
        self._current_entity_type = entity_type
        self._current_entity = entity
        self.entity_view_manager.show(entity_type, entity=entity)
        self.detail_panel.set_context(entity_type, entity)

    def _update_navigation_buttons(self):
        """Met à jour l'état des boutons de navigation."""
        total = len(self._navigation_history.entries)
        current = (
            self._navigation_history.index + 1
            if self._navigation_history.index >= 0
            else 0
        )
        self.nav_toolbar.update_state(
            self._navigation_history.can_go_back,
            self._navigation_history.can_go_forward,
            current,
            total,
        )
        self.menu_bar.refresh_state()

    def on_entity_type_change(self, *args):
        """Réagit au changement de type d'entité."""
        entity_type = self.entity_type_var.get()
        if entity_type == "ANCESTOR_TREE":
            if self._last_individual_entity is None:
                coordinator = self.entity_selection_coordinator
                self._last_individual_entity = (
                    coordinator._last_selected_entities.get("INDI")
                    if coordinator is not None
                    else None
                )
                if self._last_individual_entity is not None:
                    self._last_individual_type = "INDI"
            if (
                self._last_individual_entity is None
                or self._last_individual_type != "INDI"
            ):
                messagebox.showinfo(
                    self.translator.get("menu.ancestor_tree_title"),
                    self.translator.get("view.ancestor_tree.no_individual"),
                )
                self.entity_selection_coordinator.set_entity_type_without_refresh(
                    self._previous_entity_type or "INDI"
                )
                return
            self._switch_to_ancestor_tree_view()
            return
        self._previous_entity_type = entity_type
        if self._ancestor_tree_mode:
            self._switch_back_to_normal_view()
        self.entity_selection_coordinator.on_entity_type_change()

    def _update_entity_type_tabs(self):
        """Met à jour les onglets de types d'entité."""
        self.entity_type_tabs.set_items(
            self.controller.get_all_entity_type_menu_display_items()
        )
        self._update_entity_type_tab_state(self.entity_type_var.get())

    def _update_entity_type_tab_state(self, selected_type):
        """Met à jour la sélection d'un onglet."""
        self.entity_type_tabs.update_selection(selected_type)

    def list_entities(self):
        """Liste les entités du type courant."""
        self.entity_browser.list_entities()

    def clear_search(self):
        """Efface la recherche."""
        self.entity_browser.clear_search()

    def filter_entities(self, *args):
        """Filtre les entités selon la recherche."""
        self.entity_browser.filter_entities(*args)

    def _clear_empty_entity_selection(self, entity_type):
        """Affiche un état vide pour un type d'entité."""
        self._show_entity_view(entity_type, None)
        self._display_raw_text("")

    def show_entity(self, event):
        """Réagit à la sélection d'une entité."""
        if event is not None:
            if self._entity_selection_after_id is None:
                self._entity_selection_after_id = self.root.after_idle(
                    self._show_selected_entity
                )
            return
        self._show_selected_entity()

    def _show_selected_entity(self):
        """Affiche l'entité sélectionnée."""
        self._entity_selection_after_id = None
        selection = self.entity_browser.entity_tree.selection()
        if not selection:
            return
        if not self.controller.is_loaded():
            return

        item_id = selection[0]
        if item_id == "empty":
            self._show_entity_view(self.entity_type_var.get(), None)
            self._display_raw_text("")
            return

        entity = self.entity_browser.get_entity(item_id)
        if entity is None:
            return
        self.entity_selection_coordinator.remember_selection(
            self.entity_type_var.get(), entity
        )
        if self.entity_selection_coordinator.should_ignore_selection(entity):
            return
        context = self.controller.get_entity_display_info(entity)
        self.display_entity_context(context)
        if self.entity_type_var.get() == "INDI":
            self._last_individual_entity = entity
            self._last_individual_type = "INDI"

    def _display_raw_text(self, content):
        """Affiche le texte GEDCOM brut."""
        self.detail_panel.display_raw(content)

    def show_header(self):
        """Affiche le bloc HEAD."""
        if not self.controller.is_loaded():
            return

        block = self.controller.extract_head()
        if not block:
            messagebox.showerror(
                self.translator.get("ui.error"),
                self.translator.get("ui.no_header"),
            )
            return

        self._display_raw_text(block)
        self.highlighter.highlight()

    def show_trailer(self):
        """Affiche le bloc TRLR."""
        if not self.controller.is_loaded():
            return

        block = self.controller.extract_trailer()
        if not block:
            messagebox.showerror(
                self.translator.get("ui.error"),
                self.translator.get("ui.no_trailer"),
            )
            return

        self._display_raw_text(block)
        self.highlighter.highlight()

    def _record_navigation(self, context):
        """Enregistre un contexte de navigation."""
        self.entity_navigator.record(context)
        self._update_navigation_buttons()

    def navigate_to(self, pointer):
        """Navigue vers un pointeur."""
        self.entity_navigator.controller = self.controller
        self.entity_navigator.history = self._navigation_history
        self.entity_navigator.navigate_to(pointer)

    def go_back(self):
        """Revient à l'entité précédente."""
        self.entity_navigator.controller = self.controller
        self.entity_navigator.history = self._navigation_history
        self.entity_navigator.go_back()
        self._update_navigation_buttons()

    def go_forward(self):
        """Avance à l'entité suivante."""
        self.entity_navigator.controller = self.controller
        self.entity_navigator.history = self._navigation_history
        self.entity_navigator.go_forward()
        self._update_navigation_buttons()

    def display_entity_context(self, context):
        """Affiche un contexte d'entité."""
        self.entity_selection_coordinator.synchronize_to_context(
            context, self.DISPLAY_TYPE_MAP
        )
        self._record_navigation(context)

        entity_type = self.DISPLAY_TYPE_MAP.get(context["type"])
        if entity_type is not None:
            self._show_entity_view(entity_type, context["entity"])
        else:
            self._clear_entity_views()

        if context.get("raw_block") is not None:
            self._display_raw_text(context["raw_block"])
            self.highlighter.highlight()
