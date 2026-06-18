# ui/views/family_view.py

import tkinter as tk
from tkinter import ttk

class FamilyView(ttk.Frame):
    """
    Affiche une fiche famille (mari, femme, enfants, mariage…)
    """

    def __init__(self, parent):
        super().__init__(parent)
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
                widget.config(text="—")
            return

        self.title_label.config(text=f"Famille : {family.pointer}")

        for key, widget in self.labels.items():
            value = getattr(family, key, "")

            if key == "children":
                value = ", ".join(value) if value else "—"

            widget.config(text=value if value else "—")
