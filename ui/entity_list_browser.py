"""Explorateur d'entités : recherche asynchrone, filtre et sélection."""

import logging
import queue
import threading
import tkinter as tk
from tkinter import ttk
from typing import Any

from ui.entity_list_view import EntityListView

logger = logging.getLogger(__name__)


class EntityListBrowser(ttk.Frame):
    """Explorateur des entités GEDCOM, regroupant la recherche et la liste."""

    SEARCH_DEBOUNCE_MS = 150
    SEARCH_POLL_INTERVAL_MS = 25
    PAGE_SIZE = 500
    AUTO_PAGE_SCROLL_THRESHOLD = 0.98
    AUTO_PAGE_INTERVAL_MS = 200

    _search_after_id: Any
    _search_poll_after_id: Any
    _page_after_id: Any
    _search_worker: Any
    _entity_sort_column: Any
    filtered_entities: list[Any]
    _items: list[Any]
    _entity_by_item_id: dict[Any, Any]
    _item_id_by_pointer: dict[str, str]

    def __init__(
        self,
        parent,
        translator,
        controller_provider,
        entity_type_var,
        on_select,
        on_empty,
        tooltip_factory=None,
    ):
        """Initialise l'explorateur d'entités."""
        super().__init__(parent)
        self.translator = translator
        self._controller_provider = controller_provider
        self.entity_type_var = entity_type_var
        self.on_empty = on_empty
        self.filtered_entities = []
        self._items = []
        self._visible_limit = 0
        self._entity_by_item_id = {}
        self._item_id_by_pointer = {}
        self._search_after_id = None
        self._search_poll_after_id = None
        self._page_after_id = None
        self._search_queue: queue.Queue[tuple[int, list | None]] = queue.Queue()
        self._search_generation = 0
        self._search_in_flight = False
        self._search_worker = None
        self._entity_sort_column = None
        self._entity_sort_reverse = False
        self._scheduler = self.winfo_toplevel()
        self.panel = self._create_panel(on_select, tooltip_factory)
        self.search_var = self.panel.search_var
        self.search_entry = self.panel.search_entry
        self.clear_search_button = self.panel.clear_search_button
        self.entity_tree = self.panel.entity_tree

    @property
    def controller(self):
        """Retourne le contrôleur courant."""
        return self._controller_provider()

    @property
    def search_after_id(self):
        """Retourne l'identifiant du timer de recherche."""
        return self._search_after_id

    def _create_panel(self, on_select, tooltip_factory):
        """Crée le panneau de liste et le rattache à l'explorateur."""
        panel = EntityListView(
            self,
            self.translator,
            on_search=self.filter_entities,
            on_clear_search=self.clear_search,
            on_sort=self.sort_entities,
            on_select=on_select,
            tooltip_factory=tooltip_factory,
        )
        panel.pack(fill="both", expand=True)
        return panel

    def apply_theme(self):
        """Re-applique le thème courant au panneau de liste sous-jacent."""
        self.panel.apply_theme()

    def cancel_pending_search(self):
        """Annule la recherche différée et le polling en attente."""
        if self._search_after_id is not None:
            self._scheduler.after_cancel(self._search_after_id)
            self._search_after_id = None
        if self._search_poll_after_id is not None:
            self._scheduler.after_cancel(self._search_poll_after_id)
            self._search_poll_after_id = None
        self._search_in_flight = False

    def clear(self):
        """Réinitialise l'explorateur d'entités."""
        self.cancel_pending_search()
        self._search_generation += 1
        self.reset_search()
        self.entity_tree.delete(*self.entity_tree.get_children())
        self._entity_by_item_id.clear()
        self._item_id_by_pointer.clear()
        self._items = []
        self.filtered_entities = []
        self._visible_limit = 0

    def filter_entities(self, *args):
        """Filtre les entités selon la recherche, en arrière-plan."""
        if not self.controller.is_loaded():
            return

        self.cancel_pending_search()
        self._search_after_id = self._scheduler.after(
            self.SEARCH_DEBOUNCE_MS, self._launch_search, self.search_var.get()
        )

    def _launch_search(self, query):
        """Démarre le calcul de la recherche dans un thread worker."""
        self._search_after_id = None
        self._search_generation += 1
        generation = self._search_generation
        controller = self.controller
        entity_type = self.entity_type_var.get()

        self._search_in_flight = True
        worker = threading.Thread(
            target=self._run_search,
            args=(controller, entity_type, query, generation),
            daemon=True,
            name="entity-search",
        )
        self._search_worker = worker
        worker.start()
        self._schedule_search_poll()

    def _run_search(self, controller, entity_type, query, generation):
        """Calcule les entités filtrées hors du thread de l'interface."""
        try:
            items = controller.get_entity_list_items(entity_type, query)
        except Exception:
            logger.exception("Échec de la recherche des entités")
            items = None
        self._search_queue.put((generation, items))

    def _schedule_search_poll(self):
        """Reprogramme la lecture des résultats de recherche."""
        if self._search_poll_after_id is None:
            self._search_poll_after_id = self._scheduler.after(
                self.SEARCH_POLL_INTERVAL_MS, self._poll_search_result
            )

    def _poll_search_result(self):
        """Publie le résultat de recherche dès qu'il est disponible."""
        self._search_poll_after_id = None
        generation = self._search_generation
        result = None

        while True:
            try:
                candidate = self._search_queue.get_nowait()
            except queue.Empty:
                break
            if candidate[0] == generation:
                result = candidate

        if result is not None:
            self._search_in_flight = False
            self.refresh_entities(self.search_var.get(), result[1])
            return

        if self._search_in_flight:
            self._schedule_search_poll()

    def clear_search(self):
        """Efface le champ de recherche."""
        self.search_var.set("")

    def reset_search(self):
        """Réinitialise la recherche et la liste."""
        self.search_var.set("")

    def list_entities(self):
        """Liste les entités du type courant."""
        if self.controller.is_loaded():
            self.refresh_entities()

    def refresh_entities(self, query="", items=None):
        """Rafraîchit l'affichage des entités avec la liste fournie ou calculée."""
        self._cancel_auto_page()
        entity_type = self.entity_type_var.get()

        if entity_type not in self.controller.get_entity_types():
            self._items = []
            self._visible_limit = 0
            self._show_empty_entity_list(entity_type)
            return

        if items is None:
            items = self.controller.get_entity_list_items(entity_type, query)

        self._items = [entity for entity, _ in items]
        self._visible_limit = min(self.PAGE_SIZE, len(self._items))
        self._render_items()

    def _render_items(self):
        """Affiche la première page d'entités dans l'arbre."""
        self.entity_tree.delete(*self.entity_tree.get_children())
        self._entity_by_item_id = {}
        self._item_id_by_pointer = {}

        if not self._items:
            self._show_empty_entity_list(self.entity_type_var.get())
            return

        visible = self._items[: self._visible_limit]
        for index, entity in enumerate(visible):
            item_id = str(index)
            self._entity_by_item_id[item_id] = entity
            pointer = getattr(entity, "pointer", None)
            if pointer:
                self._item_id_by_pointer.setdefault(pointer, item_id)
            self.entity_tree.insert(
                "",
                "end",
                iid=item_id,
                values=(
                    self.controller.format_entity_display_name(
                        entity, self.entity_type_var.get()
                    ),
                    pointer or "—",
                ),
            )

        self.filtered_entities = list(visible)
        if self._visible_limit < len(self._items):
            self._schedule_auto_page()

    def _show_empty_entity_list(self, entity_type):
        """Affiche un état vide dans la liste."""
        self.entity_tree.insert(
            "",
            "end",
            iid="empty",
            values=(self.translator.get("ui.no_entity_type"), "—"),
        )
        self.on_empty(entity_type)

    def _schedule_auto_page(self):
        """Programme la vérification de défilement pour la pagination."""
        if self._page_after_id is None:
            self._page_after_id = self._scheduler.after(
                self.AUTO_PAGE_INTERVAL_MS, self._grow_page_if_needed
            )

    def _cancel_auto_page(self):
        """Annule la vérification de défilement en attente."""
        if self._page_after_id is not None:
            self._scheduler.after_cancel(self._page_after_id)
            self._page_after_id = None

    def _grow_page_if_needed(self):
        """Ajoute une page lorsque le défilement atteint le bas de la liste."""
        self._page_after_id = None
        if self._visible_limit >= len(self._items):
            return

        try:
            first, last = self.entity_tree.yview()
        except tk.TclError:
            return

        if last < self.AUTO_PAGE_SCROLL_THRESHOLD or first <= 0.0:
            self._schedule_auto_page()
            return

        self._visible_limit = min(
            self._visible_limit + self.PAGE_SIZE, len(self._items)
        )
        self._render_items()

    def get_entity(self, item_id):
        """Retourne l'entité correspondant à un item."""
        return self._entity_by_item_id.get(item_id)

    def find_entity_item_id(self, entity):
        """Retourne l'identifiant d'item d'une entité."""
        if self.entity_type_var.get() != "CITE":
            pointer = getattr(entity, "pointer", None)
            if pointer:
                item_id = self._item_id_by_pointer.get(pointer)
                if item_id is not None:
                    return item_id

        for item_id, candidate in self._entity_by_item_id.items():
            if candidate is entity:
                return item_id
        return None

    def contains_entity(self, entity):
        """Indique si une entité est présente dans la liste."""
        return self.find_entity_item_id(entity) is not None

    def select_entity(self, entity):
        """Sélectionne une entité dans l'arbre."""
        item_id = self.find_entity_item_id(entity)
        if item_id is None:
            item_id = self._reveal_entity(entity)
        if item_id is None or self.entity_tree.selection() == (item_id,):
            return False

        self.entity_tree.selection_set(item_id)
        self.entity_tree.focus(item_id)
        self.entity_tree.see(item_id)
        return True

    def _reveal_entity(self, entity):
        """Agrandit la page courante jusqu'à rendre l'entité visible."""
        pointer = getattr(entity, "pointer", None)
        for index, candidate in enumerate(self._items):
            if candidate is entity:
                break
            if pointer is not None and getattr(candidate, "pointer", None) == pointer:
                break
        else:
            return None

        self._visible_limit = max(self._visible_limit, index + 1)
        self._render_items()
        return self.find_entity_item_id(entity)

    def sort_entities(self, column):
        """Trie les entités selon la colonne."""
        if self._entity_sort_column == column:
            self._entity_sort_reverse = not self._entity_sort_reverse
        else:
            self._entity_sort_column = column
            self._entity_sort_reverse = False

        if not self._items:
            return

        entity_type = self.entity_type_var.get()
        self._items.sort(
            key=lambda entity: self.controller.get_entity_sort_key(
                entity, entity_type, column
            ),
            reverse=self._entity_sort_reverse,
        )
        self._visible_limit = min(self.PAGE_SIZE, len(self._items))
        self._render_items()
