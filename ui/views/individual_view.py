# ui/views/individual_view.py

import logging
import tkinter as tk
from tkinter import ttk

from ui.views.link_utils import configure_label, configure_text_widget
from ui.themes import FONTS
from ui.i18n import Translator

logger = logging.getLogger(__name__)


class IndividualView(ttk.Frame):
    """
    Affiche une fiche détaillée d'un individu (modèle Individual).
    """

    def __init__(self, parent, on_pointer_click, translator=None):
        super().__init__(parent)

        self.on_pointer_click_callback = on_pointer_click
        self.translator = translator or Translator()
        self.family_name_resolver = None
        self.family_member_resolver = None
        self.family_label_resolver = None
        self.family_display_name_resolver = None
        self.configure(padding=10)

        # Titre
        self.title_label = ttk.Label(
            self,
            text=self.translator.get("view.individual"),
            font=("Segoe UI", 12, "bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 12))

        # Champs
        self.labels = {}

        fields = [
            ("view.name", "name"),
            ("view.nickname", "nickname"),
            ("view.sex", "sex"),
            ("view.birth_date", "birth_date"),
            ("view.birth_place", "birth_place"),
            ("view.baptism_date", "baptism_date"),
            ("view.baptism_place", "baptism_place"),
            ("view.death_date", "death_date"),
            ("view.death_place", "death_place"),
            ("view.death_confirmed", "death_confirmed"),
            ("view.age_at_death", "age_at_death"),
            ("view.marriage_count", "marriage_count"),
            ("view.child_family", "famc"),
            ("view.occupations", "occupations"),
            ("view.properties", "properties"),
            ("view.texts", "texts"),
            ("view.notes", "notes"),
        ]

        for i, (label_key, key) in enumerate(fields, start=1):
            field_label = ttk.Label(
                self,
                text=self.translator.get(label_key) + " :",
                foreground="#3b4a5a",
            )
            field_label.grid(row=i, column=0, sticky="w", padx=(0, 10), pady=3)

            if key in ("occupations", "properties", "texts", "notes"):
                container = ttk.Frame(
                    self, padding=(8, 4), relief="solid", borderwidth=1
                )
                container.grid(row=i, column=1, sticky="nw", padx=10, pady=2)
                self.labels[key] = container
            else:
                value_label = ttk.Label(self, text="", font=FONTS["ui"])
                value_label.grid(row=i, column=1, sticky="w", padx=10, pady=3)
                self.labels[key] = value_label

        tabs_row = len(fields) + 1
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(tabs_row, weight=1)

        self.tabs = ttk.Notebook(self)
        self.tabs.grid(
            row=tabs_row, column=0, columnspan=2, sticky="nsew", pady=(12, 0)
        )

        parent_families_tab = ttk.Frame(self.tabs)
        self.tabs.add(
            parent_families_tab, text=self.translator.get("view.family_parent_families")
        )
        fams_container = ttk.Frame(parent_families_tab, padding=(8, 4))
        fams_container.pack(fill="both", expand=True)
        fams_container.grid_columnconfigure(0, weight=1)
        ttk.Label(
            fams_container, text=self.translator.get("view.family_name"), font=("Segoe UI", 10, "bold")
        ).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 4))
        ttk.Label(
            fams_container, text=self.translator.get("view.family_identifier"), font=("Segoe UI", 10, "bold")
        ).grid(row=0, column=1, sticky="w", pady=(0, 4))
        self.labels["fams"] = fams_container

        children_tab = ttk.Frame(self.tabs)
        self.tabs.add(children_tab, text=self.translator.get("view.children"))
        self.children_container = ttk.Frame(children_tab, padding=(8, 4))
        self.children_container.pack(fill="both", expand=True)

        # Espacement
        for i in range(25):
            self.grid_rowconfigure(i, pad=2)

    def set_family_name_resolver(self, resolver):
        self.family_name_resolver = resolver

    def set_family_member_resolver(self, resolver):
        self.family_member_resolver = resolver

    def set_family_label_resolver(self, resolver):
        self.family_label_resolver = resolver

    def set_family_display_name_resolver(self, resolver):
        self.family_display_name_resolver = resolver

    def _format_family_name(self, pointer):
        if not pointer:
            return "—"

        if callable(self.family_name_resolver) and callable(
            self.family_display_name_resolver
        ):
            try:
                family = self.family_name_resolver(pointer)
                if family is not None:
                    return self.family_display_name_resolver(family, "FAM")
            except Exception:
                logger.exception("Échec de résolution de la famille %s", pointer)

        return pointer

    def _format_family_pointer(self, pointer):
        if not pointer:
            return "—"

        if callable(self.family_name_resolver) and callable(self.family_label_resolver):
            try:
                family = self.family_name_resolver(pointer)
                if family is not None:
                    return self.family_label_resolver(family, "FAM")
            except Exception:
                logger.exception("Échec de résolution de la famille %s", pointer)

        return pointer

    # ---------------------------------------------------------
    # Mise à jour de la fiche
    # ---------------------------------------------------------
    def display(self, individual):
        """
        Remplit la fiche avec un objet Individual ou efface si None.
        """
        # Effacement
        if not individual:
            self.title_label.config(text=self.translator.get("view.individual"))
            for key, widget in self.labels.items():
                if isinstance(widget, ttk.Frame):
                    if key == "fams":
                        for row_widget in widget.grid_slaves():
                            if int(row_widget.grid_info().get("row", 0)) > 0:
                                row_widget.destroy()
                        ttk.Label(widget, text="—", font=("Segoe UI", 10)).grid(
                            row=1, column=0, sticky="w"
                        )
                        continue
                    for child in widget.winfo_children():
                        child.destroy()
                    label = ttk.Label(widget, text="—", font=("Segoe UI", 10))
                    label.pack(side="left")
                else:
                    configure_label(widget, "")
            for child in self.children_container.winfo_children():
                child.destroy()
            label = ttk.Label(self.children_container, text="—", font=("Segoe UI", 10))
            label.pack(side="left")
            return

        self.title_label.config(
            text=self.translator.get(
                "view.individual_pointer", pointer=individual.pointer
            )
        )

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
                if key != "fams":
                    clear_container(widget)

                # Gestion des pointeurs cliquables (famc, fams)
                if key == "famc":
                    if value:
                        add_clickable_pointer(widget, value)
                    else:
                        label = ttk.Label(widget, text="—", font=("Segoe UI", 10))
                        label.pack(side="left")

                elif key == "fams":
                    for row_widget in widget.grid_slaves():
                        if int(row_widget.grid_info().get("row", 0)) > 0:
                            row_widget.destroy()

                    if value:
                        for row_index, pointer in enumerate(value, start=1):
                            name_label = ttk.Label(
                                widget,
                                text=self._format_family_name(pointer),
                                font=("Segoe UI", 10),
                                foreground="blue",
                                cursor="hand2",
                                justify="left",
                            )
                            name_label.grid(
                                row=row_index, column=0, sticky="w", padx=(0, 10), pady=2
                            )
                            name_label.bind(
                                "<Button-1>",
                                lambda e, ptr=pointer: self.on_pointer_click(ptr),
                            )

                            pointer_label = ttk.Label(
                                widget,
                                text=pointer,
                                font=("Segoe UI", 10),
                                foreground="blue",
                                cursor="hand2",
                            )
                            pointer_label.grid(row=row_index, column=1, sticky="w", pady=2)
                            pointer_label.bind(
                                "<Button-1>",
                                lambda e, ptr=pointer: self.on_pointer_click(ptr),
                            )
                    else:
                        ttk.Label(widget, text="—", font=("Segoe UI", 10)).grid(
                            row=1, column=0, sticky="w"
                        )

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
                    text = self.translator.get("common.yes" if value else "common.no")
                    configure_label(widget, text)
                else:
                    configure_label(widget, value)

        clear_container(self.children_container)

        children_pointers = []
        fams = getattr(individual, "fams", None) or []
        if callable(self.family_name_resolver):
            for family_pointer in fams:
                family = self.family_name_resolver(family_pointer)
                for child_pointer in getattr(family, "children", None) or []:
                    if child_pointer and child_pointer not in children_pointers:
                        children_pointers.append(child_pointer)

        if children_pointers:
            for index, pointer in enumerate(children_pointers):
                if index > 0:
                    sep = ttk.Label(
                        self.children_container, text=", ", font=("Segoe UI", 10)
                    )
                    sep.pack(side="left")
                child_name = None
                if callable(self.family_member_resolver):
                    resolved_child = self.family_member_resolver(pointer)
                    child_name = (
                        getattr(resolved_child, "name", None)
                        if resolved_child
                        else None
                    )
                display_text = f"{pointer} – {child_name}" if child_name else pointer
                label = ttk.Label(
                    self.children_container,
                    text=display_text,
                    font=("Segoe UI", 10),
                    foreground="blue",
                    cursor="hand2",
                )
                label.bind(
                    "<Button-1>", lambda e, ptr=pointer: self.on_pointer_click(ptr)
                )
                label.pack(side="left")
        else:
            label = ttk.Label(self.children_container, text="—", font=("Segoe UI", 10))
            label.pack(side="left")

    # ---------------------------------------------------------
    # Navigation par clic
    # ---------------------------------------------------------
    def on_pointer_click(self, pointer):
        if callable(self.on_pointer_click_callback):
            self.on_pointer_click_callback(pointer)
