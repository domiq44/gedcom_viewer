"""Création des lignes tag/valeur des fiches structurées."""

import tkinter as tk
from typing import Callable

from ui.themes import COLORS, FONTS
from ui.views.link_utils import configure_text_urls
from ui.views.structured_link_renderer import StructuredLinkRenderer


class StructuredRowFactory:
    """Fabrique les widgets sélectionnables d'une ligne de fiche."""

    def __init__(
        self,
        bind_scroll: Callable[[tk.Widget], None],
        on_pointer_begin: Callable[..., None],
        on_pointer_end: Callable[..., None],
    ) -> None:
        """Initialise la fabrique avec ses gestionnaires de défilement et de clic."""
        self._bind_scroll = bind_scroll
        self._on_pointer_begin = on_pointer_begin
        self._on_pointer_end = on_pointer_end

    def create(
        self,
        parent: tk.Misc,
        row: int,
        label: str,
        text: str,
        pointer: str | None = None,
        depth: int = 0,
    ) -> tuple[tk.Text, tk.Text]:
        """Crée les widgets tag et valeur d'une ligne et retourne le couple."""
        tag_widget = self._selectable_text(parent, label, COLORS["muted_text"])
        tag_widget.grid(
            row=row + 1,
            column=0,
            sticky="new",
            padx=(depth * 12, 12),
            pady=3,
        )
        value_widget = self._selectable_text(
            parent, text, COLORS["link"] if pointer else COLORS["text"]
        )
        value_widget.grid(row=row + 1, column=1, sticky="ew", pady=3)
        if pointer:
            StructuredLinkRenderer.bind(
                value_widget,
                pointer,
                self._on_pointer_begin,
                self._on_pointer_end,
            )
        return tag_widget, value_widget

    def _selectable_text(self, parent: tk.Misc, text: str, foreground: str) -> tk.Text:
        """Crée un texte sélectionnable avec retour à la ligne automatique."""
        widget = tk.Text(
            parent,
            width=1,
            height=1,
            wrap="word",
            background=COLORS["background"],
            foreground=foreground,
            font=FONTS["ui"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            pady=3,
            cursor="xterm",
            takefocus=True,
        )
        widget.insert("1.0", text)
        # Définir la hauteur sur le nombre de lignes logiques pour que le
        # texte multiligne (DATA/TEXT avec CONT/CONC) soit intégralement
        # visible sans défilement interne.
        logical_lines = max(1, text.count("\n") + 1) if text else 1
        widget.configure(height=logical_lines)
        configure_text_urls(widget)
        widget.bind(
            "<Configure>",
            lambda _event: self._fit_value_height(widget),
            add="+",
        )
        self._bind_scroll(widget)
        widget.configure(state="disabled")
        return widget

    @staticmethod
    def _fit_value_height(widget: tk.Text) -> None:
        """Ajuste la hauteur du texte à son nombre de lignes logiques."""
        try:
            if not widget.winfo_exists() or not widget.winfo_viewable():
                return
            if widget.winfo_width() <= 0 or widget.winfo_height() <= 0:
                return
            if getattr(widget, "_fitting_height", False):
                return
            setattr(widget, "_fitting_height", True)
            try:
                content = widget.get("1.0", "end-1c")
                if isinstance(content, str) and content:
                    count = max(1, content.count("\n") + 1)
                else:
                    # widget est un mock (tests) ou get() n'a pas retourné de str
                    line_count = widget.count("1.0", "end-1c", "displaylines")
                    count = line_count[0] if line_count else 1
                current = widget.cget("height")
                if current != count:
                    widget.configure(height=max(1, count))
            finally:
                setattr(widget, "_fitting_height", False)
        except tk.TclError:
            pass
