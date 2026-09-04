import tkinter as tk
from tkinter import ttk

from ui.themes import COLORS


class EntityListPanel(ttk.Frame):
    """Panneau de recherche et de sélection des entités GEDCOM."""

    def __init__(
        self,
        parent,
        translator,
        on_search,
        on_clear_search,
        on_sort,
        on_select,
        tooltip_factory=None,
    ):
        super().__init__(parent)
        self.translator = translator
        self.on_sort = on_sort
        self.search_var = tk.StringVar()
        self.search_entry = None
        self.clear_search_button = None
        self.entity_tree = None
        self._build(on_search, on_clear_search, on_select, tooltip_factory)

    def _build(self, on_search, on_clear_search, on_select, tooltip_factory):
        tk.Label(self, text=self.translator.get("ui.search")).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        self.search_entry = tk.Entry(
            self,
            textvariable=self.search_var,
            width=30,
            relief="solid",
            highlightthickness=1,
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["selection"],
            bg="#ffffff",
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
        )
        self.search_entry.grid(row=1, column=0, sticky="ew")
        self.search_var.trace_add("write", on_search)

        self.clear_search_button = ttk.Button(
            self,
            text="×",
            command=on_clear_search,
            width=3,
            style="ClearSearch.TButton",
        )
        self.clear_search_button.grid(row=1, column=1, padx=(6, 0))
        if tooltip_factory is not None:
            tooltip_factory(
                self.clear_search_button,
                self.translator.get("ui.clear_search"),
            )

        tk.Label(self, text=self.translator.get("ui.entities")).grid(
            row=2, column=0, sticky="w", pady=(10, 0)
        )
        self.entity_tree = ttk.Treeview(
            self,
            columns=("name", "pointer"),
            show="headings",
            selectmode="browse",
            style="Entity.Treeview",
            padding=(6, 0),
        )
        self.entity_tree.heading(
            "name",
            text=self.translator.get("ui.name"),
            command=lambda: self.on_sort("name"),
        )
        self.entity_tree.heading(
            "pointer",
            text=self.translator.get("ui.identifier"),
            command=lambda: self.on_sort("pointer"),
        )
        self.entity_tree.column("name", width=230, minwidth=140, anchor="w")
        self.entity_tree.column("pointer", width=80, minwidth=70, anchor="e")
        self.entity_tree.grid(row=3, column=0, sticky="nsew")
        self.entity_tree.bind("<<TreeviewSelect>>", on_select)

        entity_scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.entity_tree.yview
        )
        entity_scrollbar.grid(row=3, column=1, sticky="ns")
        self.entity_tree.configure(yscrollcommand=entity_scrollbar.set)

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
