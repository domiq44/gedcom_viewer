"""En-tête applicatif (titre, sous-titre et actions rapides)."""

import tkinter as tk

from ui.themes import COLORS


class AppHeader(tk.Frame):
    """Entête principale de l'application."""

    def __init__(
        self,
        parent,
        translator,
    ):
        """Initialise l'en-tête applicatif."""
        super().__init__(
            parent,
            bg=COLORS["header_background"],
            highlightthickness=1,
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["separator"],
            padx=18,
            pady=10,
        )
        self.translator = translator
        self._build()

    def _build(self):
        """Construit le titre, le sous-titre et les actions rapides."""
        content = tk.Frame(self, bg=COLORS["header_background"])
        content.pack(fill="x")

        self.app_title = tk.Label(
            content,
            text=self.translator.get("app.title"),
            font=("Segoe UI", 18, "bold"),
            bg=COLORS["header_background"],
            fg=COLORS["header_title"],
        )
        self.app_title.pack(side="left", anchor="w")

        self.app_subtitle = tk.Label(
            content,
            text=self.translator.get("app.subtitle"),
            font=("Segoe UI", 9),
            bg=COLORS["header_background"],
            fg=COLORS["header_subtitle"],
        )
        self.app_subtitle.pack(side="left", anchor="w", padx=(12, 0))

    def apply_theme(self):
        """Re-applique les couleurs du thème courant à l'entête."""
        self.configure(bg=COLORS["header_background"])
        self.app_title.configure(
            bg=COLORS["header_background"], fg=COLORS["header_title"]
        )
        self.app_subtitle.configure(
            bg=COLORS["header_background"], fg=COLORS["header_subtitle"]
        )
