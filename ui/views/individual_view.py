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
        self.note_resolver = None
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
        ]

        for i, (label_key, key) in enumerate(fields, start=1):
            field_label = ttk.Label(
                self,
                text=self.translator.get(label_key) + " :",
                foreground="#3b4a5a",
            )
            field_label.grid(row=i, column=0, sticky="w", padx=(0, 10), pady=3)

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
            fams_container,
            text=self.translator.get("view.family_name"),
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 4))
        ttk.Label(
            fams_container,
            text=self.translator.get("view.family_identifier"),
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=1, sticky="w", pady=(0, 4))
        self.labels["fams"] = fams_container

        children_tab = ttk.Frame(self.tabs)
        self.tabs.add(children_tab, text=self.translator.get("view.children"))
        self.children_container = ttk.Frame(children_tab, padding=(8, 4))
        self.children_container.pack(fill="both", expand=True)
        self.children_container.grid_columnconfigure(0, weight=1)
        ttk.Label(
            self.children_container,
            text=self.translator.get("view.family_name"),
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 4))
        ttk.Label(
            self.children_container,
            text=self.translator.get("view.family_identifier"),
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=1, sticky="w", pady=(0, 4))

        for tab_title_key, key in (
            ("view.texts", "texts"),
            ("view.properties", "properties"),
            ("view.occupations", "occupations"),
        ):
            tab = ttk.Frame(self.tabs)
            self.tabs.add(tab, text=self.translator.get(tab_title_key))
            container = ttk.Frame(tab, padding=(8, 4))
            container.pack(fill="both", expand=True)
            self.labels[key] = container

        notes_tab = ttk.Frame(self.tabs)
        self.tabs.add(notes_tab, text=self.translator.get("view.notes"))
        notes_container = ttk.Frame(notes_tab, padding=(8, 4))
        notes_container.pack(fill="both", expand=True)
        notes_container.grid_columnconfigure(0, weight=1)
        ttk.Label(
            notes_container,
            text=self.translator.get("view.family_name"),
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 4))
        ttk.Label(
            notes_container,
            text=self.translator.get("view.family_identifier"),
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=1, sticky="w", pady=(0, 4))
        self.labels["notes"] = notes_container

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

    def set_note_resolver(self, resolver):
        self.note_resolver = resolver

    @staticmethod
    def _is_note_pointer(value):
        return (
            isinstance(value, str)
            and value.startswith("@")
            and value.endswith("@")
            and len(value) > 2
        )

    def _format_note_entry(self, entry):
        if not self._is_note_pointer(entry):
            return entry, None

        if callable(self.note_resolver) and callable(self.family_display_name_resolver):
            try:
                resolved = self.note_resolver(entry)
                if resolved is not None:
                    return self.family_display_name_resolver(resolved, "NOTE"), entry
            except Exception:
                logger.exception("Échec de résolution de la note %s", entry)

        return entry, entry

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
                    if key in ("fams", "notes"):
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
            for row_widget in self.children_container.grid_slaves():
                if int(row_widget.grid_info().get("row", 0)) > 0:
                    row_widget.destroy()
            ttk.Label(self.children_container, text="—", font=("Segoe UI", 10)).grid(
                row=1, column=0, sticky="w"
            )
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
                if key not in ("fams", "notes"):
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
                                row=row_index,
                                column=0,
                                sticky="w",
                                padx=(0, 10),
                                pady=2,
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
                            pointer_label.grid(
                                row=row_index, column=1, sticky="w", pady=2
                            )
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
                    for row_widget in widget.grid_slaves():
                        if int(row_widget.grid_info().get("row", 0)) > 0:
                            row_widget.destroy()

                    if value:
                        for row_index, entry in enumerate(value, start=1):
                            text, pointer = self._format_note_entry(entry)
                            text_label = ttk.Label(
                                widget,
                                font=("Segoe UI", 10),
                                justify="left",
                            )
                            configure_label(text_label, text)
                            text_label.grid(
                                row=row_index,
                                column=0,
                                sticky="w",
                                padx=(0, 10),
                                pady=2,
                            )

                            pointer_label = ttk.Label(
                                widget,
                                text=pointer or "—",
                                font=("Segoe UI", 10),
                            )
                            pointer_label.grid(
                                row=row_index, column=1, sticky="w", pady=2
                            )

                            if pointer:
                                for label in (text_label, pointer_label):
                                    label.config(foreground="blue", cursor="hand2")
                                    label.bind(
                                        "<Button-1>",
                                        lambda e, ptr=pointer: self.on_pointer_click(
                                            ptr
                                        ),
                                    )
                    else:
                        ttk.Label(widget, text="—", font=("Segoe UI", 10)).grid(
                            row=1, column=0, sticky="w"
                        )

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

        for row_widget in self.children_container.grid_slaves():
            if int(row_widget.grid_info().get("row", 0)) > 0:
                row_widget.destroy()

        children_pointers = []
        fams = getattr(individual, "fams", None) or []
        if callable(self.family_name_resolver):
            for family_pointer in fams:
                family = self.family_name_resolver(family_pointer)
                for child_pointer in getattr(family, "children", None) or []:
                    if child_pointer and child_pointer not in children_pointers:
                        children_pointers.append(child_pointer)

        if children_pointers:
            for row_index, pointer in enumerate(children_pointers, start=1):
                child = None
                if callable(self.family_member_resolver):
                    child = self.family_member_resolver(pointer)
                if child is not None and callable(self.family_display_name_resolver):
                    name_text = self.family_display_name_resolver(child, "INDI")
                elif child is not None:
                    name_text = getattr(child, "name", None) or pointer
                else:
                    name_text = pointer

                name_label = ttk.Label(
                    self.children_container,
                    text=name_text,
                    font=("Segoe UI", 10),
                    foreground="blue",
                    cursor="hand2",
                    justify="left",
                )
                name_label.grid(
                    row=row_index, column=0, sticky="w", padx=(0, 10), pady=2
                )
                name_label.bind(
                    "<Button-1>", lambda e, ptr=pointer: self.on_pointer_click(ptr)
                )

                pointer_label = ttk.Label(
                    self.children_container,
                    text=pointer,
                    font=("Segoe UI", 10),
                    foreground="blue",
                    cursor="hand2",
                )
                pointer_label.grid(row=row_index, column=1, sticky="w", pady=2)
                pointer_label.bind(
                    "<Button-1>", lambda e, ptr=pointer: self.on_pointer_click(ptr)
                )
        else:
            ttk.Label(self.children_container, text="—", font=("Segoe UI", 10)).grid(
                row=1, column=0, sticky="w"
            )

    # ---------------------------------------------------------
    # Navigation par clic
    # ---------------------------------------------------------
    def on_pointer_click(self, pointer):
        if callable(self.on_pointer_click_callback):
            self.on_pointer_click_callback(pointer)
