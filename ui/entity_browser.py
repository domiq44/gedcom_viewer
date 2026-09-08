import tkinter as tk
from tkinter import ttk


class EntityBrowser(ttk.Frame):
    """Explorateur des entités GEDCOM, regroupant la recherche et la liste."""

    def __init__(
        self,
        parent,
        translator,
        controller,
        entity_type_var,
        on_search,
        on_clear_search,
        on_sort,
        on_select,
        tooltip_factory=None,
    ):
        super().__init__(parent)
        self.translator = translator
        self.controller = controller
        self.entity_type_var = entity_type_var
        self.panel = None
        self.search_var = tk.StringVar()
        self.search_entry = None
        self.clear_search_button = None
        self.entity_tree = None
        self._build(on_search, on_clear_search, on_sort, on_select, tooltip_factory)

    def _build(self, on_search, on_clear_search, on_sort, on_select, tooltip_factory):
        from ui.entity_list_panel import EntityListPanel

        self.panel = EntityListPanel(
            self,
            self.translator,
            on_search=on_search,
            on_clear_search=on_clear_search,
            on_sort=on_sort,
            on_select=on_select,
            tooltip_factory=tooltip_factory,
        )
        self.panel.pack(fill="both", expand=True)

        self.search_var = self.panel.search_var
        self.search_entry = self.panel.search_entry
        self.clear_search_button = self.panel.clear_search_button
        self.entity_tree = self.panel.entity_tree
