"""Coloration syntaxique GEDCOM dans la vue brute."""

import re
import tkinter as tk

from ui.themes import COLORS, FONTS


class GedcomHighlighter:
    """Coloration syntaxique GEDCOM pour la vue brute."""

    def __init__(self, text_widget):
        """Initialise le highlighter et configure les tags."""
        self.text = text_widget
        self._configure_tags()

    def _configure_tags(self):
        """Configure les tags de coloration syntaxique."""
        self.text.tag_configure(
            "level", foreground=COLORS["link"], font=FONTS["mono_bold"]
        )
        self.text.tag_configure(
            "tag", foreground=COLORS["syntax_tag"], font=FONTS["mono_bold"]
        )
        self.text.tag_configure("pointer", foreground=COLORS["syntax_pointer"])
        self.text.tag_configure("date", foreground=COLORS["syntax_date"])
        self.text.tag_configure("value", foreground=COLORS["text"])

    def apply_theme(self):
        """Re-applique les couleurs de coloration syntaxique au thème courant."""
        self._configure_tags()

    def highlight(self):
        """Ré-applique la coloration au contenu courant."""
        content = self.text.get("1.0", tk.END)

        # Effacer les anciennes couleurs
        for tag in ("level", "tag", "pointer", "date", "value"):
            self.text.tag_remove(tag, "1.0", tk.END)

        # Expressions régulières GEDCOM
        patterns = {
            "level": r"^\s*\d+",
            "pointer": r"@[A-Za-z0-9]+@",
            "tag": r"\b[A-Z]{3,5}\b",
            "date": r"\b\d{1,2} [A-Z]{3} \d{3,4}\b",
        }

        for tag, pattern in patterns.items():
            for match in re.finditer(pattern, content, flags=re.MULTILINE):
                start = f"1.0 + {match.start()} chars"
                end = f"1.0 + {match.end()} chars"
                self.text.tag_add(tag, start, end)
