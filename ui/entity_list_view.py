"""Vue de liste des entités avec recherche."""

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

from ui.themes import COLORS, FONTS


class EntityListView(ttk.Frame):
    """Panneau de recherche et de sélection des entités GEDCOM."""

    def __init__(
        self,
        parent: tk.Misc,
        translator: Any,
        on_search: Callable[..., None],
        on_clear_search: Callable[..., None],
        on_sort: Callable[[str], None],
        on_select: Callable[[Any], None],
        tooltip_factory: Callable[[tk.Widget, str], None] | None = None,
    ) -> None:
        """Initialise la vue de liste des entités."""
        super().__init__(parent)
        self.translator = translator
        self.on_sort = on_sort
        self.search_var = tk.StringVar()
        self.search_entry: tk.Entry | None = None
        self.clear_search_button: ttk.Button | None = None
        self.entity_tree: ttk.Treeview | None = None
        self._build(on_search, on_clear_search, on_select, tooltip_factory)

    def _build(
        self,
        on_search: Callable,
        on_clear_search: Callable[..., None],
        on_select: Callable[[Any], None],
        tooltip_factory: Callable[[tk.Widget, str], None] | None,
    ) -> None:
        """Construit les widgets de la liste."""
        self.title_label = tk.Label(
            self,
            text=self.translator.get("ui.entities"),
            bg=COLORS["background"],
            fg=COLORS["section_title"],
            font=FONTS["title"],
        )
        self.title_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self.search_label = tk.Label(
            self,
            text=self.translator.get("ui.search"),
            bg=COLORS["background"],
            fg=COLORS["muted_text"],
            font=FONTS["ui"],
        )
        self.search_label.grid(row=1, column=0, sticky="w", padx=(0, 6), pady=(0, 8))
        self.search_entry = tk.Entry(
            self,
            textvariable=self.search_var,
            width=20,
            relief="solid",
            highlightthickness=1,
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["selection"],
            bg=COLORS["surface"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
        )
        self.search_entry.grid(row=1, column=1, sticky="ew", pady=(0, 8))
        self.search_var.trace_add("write", on_search)

        self.clear_search_button = ttk.Button(
            self,
            text="×",
            command=on_clear_search,
            width=3,
            style="ClearSearch.TButton",
        )
        self.clear_search_button.grid(row=1, column=2, padx=(6, 0), pady=(0, 8))
        if tooltip_factory is not None:
            tooltip_factory(
                self.clear_search_button,
                self.translator.get("ui.clear_search"),
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
        self.entity_tree.grid(row=2, column=0, columnspan=3, sticky="nsew")
        self.entity_tree.bind("<<TreeviewSelect>>", on_select)

        entity_scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.entity_tree.yview
        )
        entity_scrollbar.grid(row=2, column=3, sticky="ns")
        self.entity_tree.configure(yscrollcommand=entity_scrollbar.set)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def apply_theme(self) -> None:
        """Re-applique les couleurs du thème courant au panneau de liste."""
        self.title_label.configure(bg=COLORS["background"], fg=COLORS["section_title"])
        self.search_label.configure(bg=COLORS["background"], fg=COLORS["muted_text"])
        assert self.search_entry is not None
        self.search_entry.configure(
            bg=COLORS["surface"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
        )
