# ui/views/individual_view.py

import tkinter as tk
from tkinter import ttk


class IndividualView(ttk.Frame):
    """
    Affiche une fiche détaillée d'un individu (modèle Individual).
    """

    def __init__(self, parent, viewer):
        super().__init__(parent)

        self.viewer = viewer  # 🔥 référence directe au GedcomViewer

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
        # Effacement
        if not individual:
            self.title_label.config(text="Fiche individu")
            for widget in self.labels.values():
                widget.config(text="—", foreground="black", cursor="")
                widget.unbind("<Button-1>")
            return

        self.title_label.config(text=f"Fiche : {individual.pointer}")

        # Fonction utilitaire pour rendre un label cliquable
        def make_clickable(widget, pointer):
            widget.config(foreground="blue", cursor="hand2")
            widget.bind("<Button-1>", lambda e, ptr=pointer: self.on_pointer_click(ptr))

        # Mise à jour des champs
        for key, widget in self.labels.items():
            value = getattr(individual, key, "")

            # Nettoyage des anciens bindings
            widget.unbind("<Button-1>")
            widget.config(cursor="", foreground="black")

            # Champs simples
            if key not in ("famc", "fams"):
                widget.config(text=value if value else "—")
                continue

            # FAMC (famille où l'individu est enfant)
            if key == "famc":
                widget.config(text=value if value else "—")
                if value:
                    make_clickable(widget, value)

            # FAMS (familles où l'individu est parent)
            elif key == "fams":
                if value:
                    text = ", ".join(value)
                    widget.config(text=text)
                    make_clickable(widget, value[0])  # ouvre la première famille
                else:
                    widget.config(text="—")

    # ---------------------------------------------------------
    # Navigation par clic
    # ---------------------------------------------------------
    def on_pointer_click(self, pointer):
        self.viewer.navigate_to(pointer)
