import tkinter as tk
from tkinter import ttk


class EntityBrowser(ttk.Frame):
    """Explorateur des entités GEDCOM, regroupant la recherche et la liste."""

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
        super().__init__(parent)
        self.translator = translator
        self._controller_provider = controller_provider
        self.entity_type_var = entity_type_var
        self.on_empty = on_empty
        self.panel = None
        self.search_var = tk.StringVar()
        self.search_entry = None
        self.clear_search_button = None
        self.entity_tree = None
        self.filtered_entities = []
        self._entity_by_item_id = {}
        self._search_after_id = None
        self._entity_sort_column = None
        self._entity_sort_reverse = False
        self._scheduler = self.winfo_toplevel()
        self._build(on_select, tooltip_factory)

    @property
    def controller(self):
        return self._controller_provider()

    @property
    def search_after_id(self):
        return self._search_after_id

    def _build(self, on_select, tooltip_factory):
        from ui.entity_list_panel import EntityListPanel

        self.panel = EntityListPanel(
            self,
            self.translator,
            on_search=self.filter_entities,
            on_clear_search=self.clear_search,
            on_sort=self.sort_entities,
            on_select=on_select,
            tooltip_factory=tooltip_factory,
        )
        self.panel.pack(fill="both", expand=True)

        self.search_var = self.panel.search_var
        self.search_entry = self.panel.search_entry
        self.clear_search_button = self.panel.clear_search_button
        self.entity_tree = self.panel.entity_tree

    def cancel_pending_search(self):
        if self._search_after_id is not None:
            self._scheduler.after_cancel(self._search_after_id)
            self._search_after_id = None

    def clear(self):
        self.cancel_pending_search()
        self.reset_search()
        self.entity_tree.delete(*self.entity_tree.get_children())
        self._entity_by_item_id.clear()
        self.filtered_entities.clear()

    def filter_entities(self, *args):
        if not self.controller.is_loaded():
            return

        self.cancel_pending_search()
        self._search_after_id = self._scheduler.after(
            100, self._apply_search_filter, self.search_var.get()
        )

    def _apply_search_filter(self, query):
        self._search_after_id = None
        if self.controller.is_loaded():
            self.refresh_entities(query)

    def clear_search(self):
        self.search_var.set("")
        self.search_entry.focus_set()

    def reset_search(self):
        self.search_var.set("")

    def list_entities(self):
        if self.controller.is_loaded():
            self.refresh_entities()

    def refresh_entities(self, query=""):
        entity_type = self.entity_type_var.get()
        self.entity_tree.delete(*self.entity_tree.get_children())
        self._entity_by_item_id = {}
        self.filtered_entities = []

        if entity_type not in self.controller.get_entity_types():
            self._show_empty_entity_list(entity_type)
            return

        items = self.controller.get_entity_list_items(entity_type, query)
        self.filtered_entities = [entity for entity, _ in items]
        if not items:
            self._show_empty_entity_list(entity_type)
            return

        for index, (entity, _) in enumerate(items):
            item_id = str(index)
            self._entity_by_item_id[item_id] = entity
            self.entity_tree.insert(
                "",
                "end",
                iid=item_id,
                values=(
                    self.controller.format_entity_display_name(entity, entity_type),
                    getattr(entity, "pointer", "") or "—",
                ),
            )

    def _show_empty_entity_list(self, entity_type):
        self.entity_tree.insert(
            "",
            "end",
            iid="empty",
            values=(self.translator.get("ui.no_entity_type"), "—"),
        )
        self.on_empty(entity_type)

    def get_entity(self, item_id):
        return self._entity_by_item_id.get(item_id)

    def sort_entities(self, column):
        if self._entity_sort_column == column:
            self._entity_sort_reverse = not self._entity_sort_reverse
        else:
            self._entity_sort_column = column
            self._entity_sort_reverse = False

        rows = []
        entity_type = self.entity_type_var.get()
        for item_id in self.entity_tree.get_children():
            if item_id == "empty":
                return
            values = self.entity_tree.item(item_id, "values")
            entity = self._entity_by_item_id[item_id]
            rows.append(
                (
                    item_id,
                    values,
                    entity,
                    self.controller.get_entity_sort_key(entity, entity_type, column),
                )
            )

        rows.sort(key=lambda row: row[3], reverse=self._entity_sort_reverse)
        self.filtered_entities = [entity for _, _, entity, _ in rows]
        self._entity_by_item_id = {item_id: entity for item_id, _, entity, _ in rows}
        for index, (item_id, _, _, _) in enumerate(rows):
            self.entity_tree.move(item_id, "", index)
