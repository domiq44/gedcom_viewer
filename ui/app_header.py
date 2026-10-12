import tkinter as tk

from ui.themes import COLORS


class AppHeader(tk.Frame):
    """Entête principale de l’application."""

    def __init__(self, parent, translator):
        super().__init__(
            parent,
            bg="#dfeaf5",
            highlightthickness=1,
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["separator"],
            padx=18,
            pady=10,
        )
        self.translator = translator
        self._build()

    def _build(self):
        self.app_title = tk.Label(
            self,
            text=self.translator.get("app.title"),
            font=("Segoe UI", 18, "bold"),
            bg="#dfeaf5",
            fg="#163a57",
        )
        self.app_title.pack(anchor="w")

        self.app_subtitle = tk.Label(
            self,
            text=self.translator.get("app.subtitle"),
            font=("Segoe UI", 9),
            bg="#dfeaf5",
            fg="#44627a",
        )
        self.app_subtitle.pack(anchor="w")
