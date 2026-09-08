import tkinter as tk
from tkinter import ttk

from ui.themes import COLORS, FONTS


class NavigationBar(tk.Frame):
    """Barre de navigation et état de l’historique."""

    def __init__(self, parent, translator, on_back, on_forward, tooltip_factory=None):
        super().__init__(parent, bg=COLORS["background"], padx=0, pady=2)
        self.translator = translator
        self._build(on_back, on_forward, tooltip_factory)

    def _build(self, on_back, on_forward, tooltip_factory):
        navigation_group = tk.Frame(
            self,
            bg=COLORS["surface"],
            highlightthickness=1,
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["separator"],
        )
        navigation_group.pack(side="left")

        self.back_button = ttk.Button(
            navigation_group,
            text="←",
            command=on_back,
            style="Nav.TButton",
            width=3,
        )
        self.back_button.pack(side="left")

        self.forward_button = ttk.Button(
            navigation_group,
            text="→",
            command=on_forward,
            style="Nav.TButton",
            width=3,
        )
        self.forward_button.pack(side="left")

        if tooltip_factory is not None:
            tooltip_factory(
                self.back_button,
                self.translator.get("tooltip.previous"),
            )
            tooltip_factory(
                self.forward_button,
                self.translator.get("tooltip.next"),
            )

        self.history_status = tk.Label(
            self,
            text=self.translator.get("ui.history", current=0, total=0),
            bg=COLORS["background"],
            foreground=COLORS["muted_text"],
            font=FONTS["ui"],
        )
        self.history_status.pack(side="right", padx=(12, 4))

    def update_state(self, can_go_back, can_go_forward, current, total):
        self.back_button.state(("!disabled",) if can_go_back else ("disabled",))
        self.forward_button.state(("!disabled",) if can_go_forward else ("disabled",))
        self.history_status.config(
            text=self.translator.get("ui.history", current=current, total=total)
        )
