"""Info-bulles différées pour les widgets Tkinter de l'interface."""

import tkinter as tk

from ui.themes import COLORS


class Tooltip:
    """Affiche une infobulle au survol prolongé d'un widget."""

    def __init__(self, widget, text):
        """Prépare l'infobulle et arme les événements de survol du widget."""
        self.widget = widget
        self.text = text
        self.window = None
        self.after_id = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _schedule(self, event=None):
        """Reprogramme l'affichage différé de l'infobulle."""
        self._hide()
        try:
            if not self.widget.winfo_exists():
                return
            self.after_id = self.widget.after(450, self._show)
        except tk.TclError:
            self.after_id = None

    def _show(self):
        """Crée la fenêtre d'infobulle si le widget est visible."""
        self.after_id = None
        try:
            if not self.widget.winfo_exists() or not self.widget.winfo_ismapped():
                return
        except tk.TclError:
            return

        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        self.window.wm_geometry(
            f"+{self.widget.winfo_rootx()}"
            f"+{self.widget.winfo_rooty() + self.widget.winfo_height() + 4}"
        )
        tk.Label(
            self.window,
            text=self.text,
            bg=COLORS["tooltip_background"],
            fg=COLORS["tooltip_text"],
            padx=7,
            pady=4,
            font=("TkDefaultFont", 9),
        ).pack()

    def _hide(self, event=None):
        """Annule l'affichage différé et détruit l'infobulle existante."""
        if self.after_id is not None:
            try:
                self.widget.after_cancel(self.after_id)
            except tk.TclError:
                pass
            self.after_id = None
        if self.window is not None:
            self.window.destroy()
            self.window = None
