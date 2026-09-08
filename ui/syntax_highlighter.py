import re
import tkinter as tk

from ui.themes import COLORS, FONTS


class GedcomHighlighter:
    def __init__(self, text_widget):
        self.text = text_widget
        self._configure_tags()

    def _configure_tags(self):
        self.text.tag_configure(
            "level", foreground=COLORS["link"], font=FONTS["mono_bold"]
        )
        self.text.tag_configure("tag", foreground="#D14", font=FONTS["mono_bold"])
        self.text.tag_configure("pointer", foreground="#008000")
        self.text.tag_configure("date", foreground="#AA5500")
        self.text.tag_configure("value", foreground=COLORS["text"])

    def highlight(self):
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
