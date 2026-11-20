"""Bouton de copie réutilisable avec retour visuel."""

import logging
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)


class CopyButton(ttk.Button):
    """Reusable icon button with matching copy feedback across detail views."""

    ICON = "⧉"
    COPIED_ICON = "✓"
    RESET_DELAY_MS = 1200

    def __init__(
        self,
        parent,
        command,
        tooltip_factory=None,
        tooltip_text=None,
        **kwargs,
    ):
        """Initialise le bouton de copie."""
        self._copy_command = command
        self._reset_after_id = None
        super().__init__(
            parent,
            text=self.ICON,
            width=2,
            padding=(2, 1),
            command=self._copy,
            style="Copy.TButton",
            **kwargs,
        )
        if tooltip_factory is not None and tooltip_text:
            tooltip_factory(self, tooltip_text)

    def destroy(self):
        """Annule le timer et détruit le bouton."""
        if self._reset_after_id is not None:
            try:
                self.after_cancel(self._reset_after_id)
            except Exception:
                logger.debug(
                    "Annulation du réinitialiseur d'icône impossible", exc_info=True
                )
            self._reset_after_id = None
        super().destroy()

    def _copy(self):
        """Copie le contenu et affiche le retour visuel."""
        if self._copy_command() is False:
            return
        try:
            self.configure(text=self.COPIED_ICON)
        except tk.TclError:
            return
        if self._reset_after_id is not None:
            try:
                self.after_cancel(self._reset_after_id)
            except Exception:
                logger.debug(
                    "Annulation du réinitialiseur d'icône impossible", exc_info=True
                )
        try:
            self._reset_after_id = self.after(self.RESET_DELAY_MS, self._reset_icon)
        except tk.TclError:
            self._reset_after_id = None

    def _reset_icon(self):
        """Restaure l'icône par défaut."""
        if not self.winfo_exists():
            return
        self.configure(text=self.ICON)
        self._reset_after_id = None
