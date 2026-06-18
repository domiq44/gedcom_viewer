# ui/views/family_view.py

import tkinter as tk
from tkinter import ttk

class FamilyView(ttk.Frame):
    """
    Affiche une fiche Famille (modèle Family).
    """

    def __init__(self, parent, viewer):
        super().__init__(parent)

        self.viewer = viewer  # 🔥 référence directe au GedcomViewer

        self.configure(padding=10)

        self.title_label = ttk.Label(self, text="Famille", font=("Segoe UI", 12, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.labels = {}

        fields = [
            ("Mari", "husband"),
            ("Femme", "wife"),
            ("Enfants", "children"),
            ("Date mariage", "marriage_date"),
            ("Lieu mariage", "marriage_place"),
            ("Date divorce", "divorce_date"),
            ("Lieu divorce", "divorce_place"),
        ]

        for i, (label, key) in enumerate(fields, start=1):
            ttk.Label(self, text=label + " :").grid(row=i, column=0, sticky="w")
            value_label = ttk.Label(self, text="", font=("Segoe UI", 10))
            value_label.grid(row=i, column=1, sticky="w", padx=10)
            self.labels[key] = value_label

    def display(self, family):
        if not family:
            self.title_label.config(text="Famille")
            for widget in self.labels.values():
                widget.config(text="—", foreground="black", cursor="")
                widget.unbind("<Button-1>")
            return

        self.title_label.config(text=f"Famille : {family.pointer}")

        def make_clickable(widget, pointer):
            widget.config(foreground="blue", cursor="hand2")
            widget.bind("<Button-1>", lambda e, ptr=pointer: self.on_pointer_click(ptr))

        for key, widget in self.labels.items():
            value = getattr(family, key, None)

            widget.unbind("<Button-1>")
            widget.config(cursor="", foreground="black")

            # Enfants = liste
            if key == "children":
                if value:
                    text = ", ".join(value)
                    widget.config(text=text)
                    make_clickable(widget, value[0])
                else:
                    widget.config(text="—")
                continue

            # Mari / Femme = pointeurs simples
            if key in ("husband", "wife"):
                widget.config(text=value if value else "—")
                if value:
                    make_clickable(widget, value)
                continue

            # Champs simples
            widget.config(text=value if value else "—")

    def on_pointer_click(self, pointer):
        self.viewer.navigate_to(pointer)
