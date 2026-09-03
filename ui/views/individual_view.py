# ui/views/individual_view.py

import tkinter as tk
from tkinter import ttk

from ui.views.link_utils import configure_label, configure_text_widget


class IndividualView(ttk.Frame):
    """
    Affiche une fiche détaillée d'un individu (modèle Individual).
    """

    def __init__(self, parent, on_pointer_click):
        super().__init__(parent)

        self.on_pointer_click_callback = on_pointer_click
        self.family_name_resolver = None
        self.family_member_resolver = None
        self.configure(padding=10)

        # Titre
        self.title_label = ttk.Label(
            self, text="Fiche individu", font=("Segoe UI", 12, "bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Champs
        self.labels = {}

        fields = [
            ("Nom", "name"),
            ("Surnom", "nickname"),
            ("Sexe", "sex"),
            ("Date de naissance", "birth_date"),
            ("Lieu de naissance", "birth_place"),
            ("Date de baptême", "baptism_date"),
            ("Lieu de baptême", "baptism_place"),
            ("Date de décès", "death_date"),
            ("Lieu de décès", "death_place"),
            ("Décès confirmé", "death_confirmed"),
            ("Âge au décès", "age_at_death"),
            ("Nombre de mariages", "marriage_count"),
            ("Famille (enfant)", "famc"),
            ("Familles (parent)", "fams"),
            ("Occupations", "occupations"),
            ("Propriétés", "properties"),
            ("Textes", "texts"),
            ("Notes", "notes"),
        ]

        for i, (label, key) in enumerate(fields, start=1):
            ttk.Label(self, text=label + " :").grid(row=i, column=0, sticky="w")

            if key in ("fams", "occupations", "properties", "texts", "notes"):
                container = ttk.Frame(self)
                container.grid(row=i, column=1, sticky="nw", padx=10, pady=2)
                self.labels[key] = container
            else:
                value_label = ttk.Label(self, text="", font=("Segoe UI", 10))
                value_label.grid(row=i, column=1, sticky="w", padx=10)
                self.labels[key] = value_label

        # Espacement
        for i in range(25):
            self.grid_rowconfigure(i, pad=2)

    def set_family_name_resolver(self, resolver):
        self.family_name_resolver = resolver

    def set_family_member_resolver(self, resolver):
        self.family_member_resolver = resolver

    def _format_family_pointer(self, pointer):
        if not pointer:
            return "—"

        label = pointer
        if callable(self.family_name_resolver):
            try:
                family = self.family_name_resolver(pointer)
                if family is None:
                    return label

                husband_name = None
                wife_name = None

                husband_pointer = getattr(family, "husband", None)
                if husband_pointer:
                    husband = getattr(family, "_resolved_husband", None)
                    member_resolver = getattr(self, "_family_member_resolver", None)
                    if not callable(member_resolver):
                        member_resolver = self.family_member_resolver
                    if husband is None and callable(member_resolver):
                        husband = member_resolver(husband_pointer)
                    if husband is not None:
                        husband_name = getattr(husband, "name", None)

                wife_pointer = getattr(family, "wife", None)
                if wife_pointer:
                    wife = getattr(family, "_resolved_wife", None)
                    member_resolver = getattr(self, "_family_member_resolver", None)
                    if not callable(member_resolver):
                        member_resolver = self.family_member_resolver
                    if wife is None and callable(member_resolver):
                        wife = member_resolver(wife_pointer)
                    if wife is not None:
                        wife_name = getattr(wife, "name", None)

                if husband_name and wife_name:
                    label = f"{pointer} – {husband_name} ∞ {wife_name}"
                elif husband_name:
                    label = f"{pointer} – {husband_name}"
                elif wife_name:
                    label = f"{pointer} – {wife_name}"
            except Exception:
                pass

        return label

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
            for key, widget in self.labels.items():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        child.destroy()
                    label = ttk.Label(widget, text="—", font=("Segoe UI", 10))
                    label.pack(side="left")
                else:
                    configure_label(widget, "")
            return

        self.title_label.config(text=f"Fiche : {individual.pointer}")

        # Fonction utilitaire pour rendre un label cliquable
        def make_clickable(widget, pointer):
            widget.config(foreground="blue", cursor="hand2")
            widget.bind("<Button-1>", lambda e, ptr=pointer: self.on_pointer_click(ptr))

        def clear_container(container):
            for child in container.winfo_children():
                child.destroy()

        def add_clickable_pointer(container, pointer):
            display_text = (
                self._format_family_pointer(pointer)
                if pointer.startswith("@F")
                else pointer
            )
            label = ttk.Label(
                container,
                text=display_text,
                font=("Segoe UI", 10),
                foreground="blue",
                cursor="hand2",
            )
            label.bind("<Button-1>", lambda e, ptr=pointer: self.on_pointer_click(ptr))
            label.pack(side="left")
            return label

        # Mise à jour des champs
        for key, widget in self.labels.items():
            value = getattr(individual, key, "")

            if isinstance(widget, ttk.Frame):
                clear_container(widget)

                # Gestion des pointeurs cliquables (famc, fams)
                if key == "famc":
                    if value:
                        add_clickable_pointer(widget, value)
                    else:
                        label = ttk.Label(widget, text="—", font=("Segoe UI", 10))
                        label.pack(side="left")

                elif key == "fams":
                    if value:
                        for index, pointer in enumerate(value):
                            if index > 0:
                                sep = ttk.Label(
                                    widget, text=", ", font=("Segoe UI", 10)
                                )
                                sep.pack(side="left")
                            add_clickable_pointer(widget, pointer)
                    else:
                        label = ttk.Label(widget, text="—", font=("Segoe UI", 10))
                        label.pack(side="left")

                # Gestion des listes (occupations, properties, notes)
                elif key == "occupations":
                    if value:
                        for idx, occ in enumerate(value):
                            if idx > 0:
                                sep = ttk.Label(
                                    widget, text="\n", font=("Segoe UI", 10)
                                )
                                sep.pack(side="left")
                            occ_text = occ.get("occupation", "")
                            if occ.get("date"):
                                occ_text += f" ({occ['date']})"
                            label = ttk.Label(widget, font=("Segoe UI", 10))
                            configure_label(label, occ_text)
                            label.pack(side="left")
                    else:
                        label = ttk.Label(widget, text="—", font=("Segoe UI", 10))
                        label.pack(side="left")

                elif key == "properties":
                    if value:
                        for idx, prop in enumerate(value):
                            if idx > 0:
                                sep = ttk.Label(
                                    widget, text="\n", font=("Segoe UI", 10)
                                )
                                sep.pack(side="left")
                            label = ttk.Label(widget, font=("Segoe UI", 10))
                            configure_label(label, prop)
                            label.pack(side="left")
                    else:
                        label = ttk.Label(widget, text="—", font=("Segoe UI", 10))
                        label.pack(side="left")

                elif key == "texts":
                    if value:
                        for idx, text_item in enumerate(value):
                            if idx > 0:
                                sep = ttk.Label(widget, text="\n", font=("Segoe UI", 9))
                                sep.pack(side="left")

                            # Créer un frame pour chaque texte avec scrollbar
                            text_frame = ttk.Frame(widget, height=60)
                            text_frame.pack(
                                side="left", fill="both", expand=True, pady=(2, 0)
                            )

                            # Zone de texte scrollable avec hauteur limitée
                            scrollbar = ttk.Scrollbar(text_frame)
                            scrollbar.pack(side="right", fill="y")

                            text_widget = tk.Text(
                                text_frame,
                                height=3,
                                width=50,
                                font=("Segoe UI", 9),
                                foreground="#333333",
                                bg="#f5f5f5",
                                yscrollcommand=scrollbar.set,
                                wrap="word",
                            )
                            text_widget.pack(side="left", fill="both", expand=True)
                            scrollbar.config(command=text_widget.yview)

                            # Insérer le texte et le rendre en lecture seule
                            configure_text_widget(text_widget, text_item)
                    else:
                        label = ttk.Label(widget, text="—", font=("Segoe UI", 10))
                        label.pack(side="left")

                elif key == "notes":
                    if value:
                        for idx, note in enumerate(value):
                            if idx > 0:
                                sep = ttk.Label(widget, text="\n", font=("Segoe UI", 9))
                                sep.pack(side="left")
                            # Limiter la longueur des notes affichées
                            note_text = note[:50] + "..." if len(note) > 50 else note
                            label = ttk.Label(widget, font=("Segoe UI", 9))
                            configure_label(label, f"• {note_text}")
                            label.config(foreground="#555555")
                            label.pack(side="left", anchor="w")
                    else:
                        label = ttk.Label(widget, text="—", font=("Segoe UI", 10))
                        label.pack(side="left")

            else:
                # Champs texte simples
                widget.unbind("<Button-1>")
                widget.config(cursor="", foreground="black")

                if key == "famc":
                    if value:
                        widget.config(
                            text=self._format_family_pointer(value),
                            foreground="blue",
                            cursor="hand2",
                        )
                        widget.bind(
                            "<Button-1>",
                            lambda e, ptr=value: self.on_pointer_click(ptr),
                        )
                    else:
                        configure_label(widget, "")
                    continue

                # Traitement spécial pour death_confirmed
                if key == "death_confirmed":
                    text = "Oui" if value else "Non"
                    configure_label(widget, text)
                else:
                    configure_label(widget, value)

    # ---------------------------------------------------------
    # Navigation par clic
    # ---------------------------------------------------------
    def on_pointer_click(self, pointer):
        if callable(self.on_pointer_click_callback):
            self.on_pointer_click_callback(pointer)
