# ui/views/individual_view.py

import tkinter as tk
from tkinter import ttk


class IndividualView(ttk.Frame):
    """
    Affiche une fiche détaillée d'un individu (modèle Individual).
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.configure(padding=10)

        # Titre
        self.title_label = ttk.Label(self, text="Fiche individu", font=("Segoe UI", 12, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Champs
        self.labels = {}

        fields = [
            ("Nom", "name"),
            ("Sexe", "sex"),
            ("Date de naissance", "birth_date"),
            ("Lieu de naissance", "birth_place"),
            ("Date de décès", "death_date"),
            ("Lieu de décès", "death_place"),
            ("Famille (enfant)", "famc"),
            ("Familles (parent)", "fams"),
        ]

        for i, (label, key) in enumerate(fields, start=1):
            ttk.Label(self, text=label + " :").grid(row=i, column=0, sticky="w")
            value_label = ttk.Label(self, text="", font=("Segoe UI", 10))
            value_label.grid(row=i, column=1, sticky="w", padx=10)
            self.labels[key] = value_label

        # Espacement
        for i in range(10):
            self.grid_rowconfigure(i, pad=4)

    # ---------------------------------------------------------
    # Mise à jour de la fiche
    # ---------------------------------------------------------
    def display(self, individual):
        """
        Remplit la fiche avec un objet Individual ou efface si None.
        """
        if not individual:
            self.title_label.config(text="Fiche individu")
            for widget in self.labels.values():
                widget.config(text="—")
            return

        self.title_label.config(text=f"Fiche : {individual.pointer}")

        for key, widget in self.labels.items():
            value = getattr(individual, key, "")
            widget.config(text=value if value else "—")

