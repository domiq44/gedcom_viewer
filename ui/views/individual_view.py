# ui/views/individual_view.py

import logging
import tkinter as tk
from tkinter import ttk

from ui.views.link_utils import configure_label
from ui.themes import FONTS
from ui.i18n import Translator

logger = logging.getLogger(__name__)

# Tags GEDCOM fréquents (niveau 1 ou imbriqués) pour lesquels un libellé traduit existe
GEDCOM_TAG_LABEL_KEYS = {
    "ADDR": "gedcom.tag.addr",
    "ADOP": "gedcom.tag.adop",
    "AGE": "gedcom.tag.age",
    "BAPM": "gedcom.tag.bapm",
    "BARM": "gedcom.tag.barm",
    "BASM": "gedcom.tag.basm",
    "BIRT": "gedcom.tag.birt",
    "BLES": "gedcom.tag.bles",
    "BURI": "gedcom.tag.buri",
    "CAST": "gedcom.tag.cast",
    "CENS": "gedcom.tag.cens",
    "CHAN": "gedcom.tag.chan",
    "CHR": "gedcom.tag.chr",
    "CHRA": "gedcom.tag.chra",
    "CONF": "gedcom.tag.conf",
    "CREM": "gedcom.tag.crem",
    "DATA": "gedcom.tag.data",
    "DATE": "gedcom.tag.date",
    "DEAT": "gedcom.tag.deat",
    "DSCR": "gedcom.tag.dscr",
    "EDUC": "gedcom.tag.educ",
    "EMIG": "gedcom.tag.emig",
    "EVEN": "gedcom.tag.even",
    "FACT": "gedcom.tag.fact",
    "FCOM": "gedcom.tag.fcom",
    "FILE": "gedcom.tag.file",
    "FORM": "gedcom.tag.form",
    "GIVN": "gedcom.tag.givn",
    "GRAD": "gedcom.tag.grad",
    "IDNO": "gedcom.tag.idno",
    "IMMI": "gedcom.tag.immi",
    "LATI": "gedcom.tag.lati",
    "LONG": "gedcom.tag.long",
    "MAP": "gedcom.tag.map",
    "NAME": "gedcom.tag.name",
    "NATI": "gedcom.tag.nati",
    "NATU": "gedcom.tag.natu",
    "NICK": "gedcom.tag.nick",
    "NMR": "gedcom.tag.nmr",
    "NOTE": "gedcom.tag.note",
    "OCCU": "gedcom.tag.occu",
    "ORDN": "gedcom.tag.ordn",
    "PAGE": "gedcom.tag.page",
    "PEDI": "gedcom.tag.pedi",
    "PLAC": "gedcom.tag.plac",
    "PROB": "gedcom.tag.prob",
    "PROP": "gedcom.tag.prop",
    "QUAY": "gedcom.tag.quay",
    "RELI": "gedcom.tag.reli",
    "RESI": "gedcom.tag.resi",
    "RETI": "gedcom.tag.reti",
    "ROLE": "gedcom.tag.role",
    "SOUR": "gedcom.tag.sour",
    "SSN": "gedcom.tag.ssn",
    "SURN": "gedcom.tag.surn",
    "TEXT": "gedcom.tag.text",
    "TIME": "gedcom.tag.time",
    "_TIME": "gedcom.tag.time",
    "TITL": "gedcom.tag.titl",
    "TYPE": "gedcom.tag.type",
    "WILL": "gedcom.tag.will",
}

# Sous-tags fusionnés dans la valeur du nœud parent plutôt qu'affichés en ligne
_CONTINUATION_TAGS = {"CONT", "CONC"}

# Tags "événement/fait" affichés dans la liste tabulaire de l'onglet Événements
# (Type, Description, Date, Lieu, Âge) plutôt que dans la zone générique
_EVENT_TABLE_TAGS = {
    "ADOP",
    "BAPM",
    "BARM",
    "BASM",
    "BLES",
    "BURI",
    "CAST",
    "CENS",
    "CHR",
    "CHRA",
    "CONF",
    "CREM",
    "DEAT",
    "DSCR",
    "EDUC",
    "EMIG",
    "EVEN",
    "FACT",
    "FCOM",
    "GRAD",
    "IDNO",
    "IMMI",
    "NATI",
    "NATU",
    "OCCU",
    "ORDN",
    "PROB",
    "RELI",
    "RESI",
    "RETI",
    "SSN",
    "TITL",
    "WILL",
    "BIRT",
}


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
        self.object_resolver = None
        self.object_display_name_resolver = None
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
            ("view.sex", "sex"),
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

        # Zone dédiée aux événements/faits (NAME, BIRT, BAPM, FCOM, GRAD, FACT,
        # OCCU, etc.), affichée au-dessus des onglets plutôt que dans un onglet.
        events_row = len(fields) + 1
        self._build_events_section(events_row)

        tabs_row = events_row + 1
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(events_row, weight=1)
        self.grid_rowconfigure(tabs_row, weight=1)

        self.tabs = ttk.Notebook(self)
        self.tabs.grid(
            row=tabs_row, column=0, columnspan=2, sticky="nsew", pady=(12, 0)
        )

        self._build_events_table_tab()

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

        gallery_tab = ttk.Frame(self.tabs)
        self.tabs.add(gallery_tab, text=self.translator.get("view.gallery"))
        self.gallery_container = ttk.Frame(gallery_tab, padding=(8, 4))
        self.gallery_container.pack(fill="both", expand=True)
        self.gallery_container.grid_columnconfigure(0, weight=1)
        ttk.Label(
            self.gallery_container,
            text=self.translator.get("view.gallery_name"),
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 4))
        ttk.Label(
            self.gallery_container,
            text=self.translator.get("view.family_identifier"),
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=1, sticky="w", pady=(0, 4))
        self.labels["gallery"] = self.gallery_container

        # Espacement
        for i in range(25):
            self.grid_rowconfigure(i, pad=2)

    def _build_events_table_tab(self):
        """Onglet listant les événements/faits (BIRT, BAPM, FCOM, GRAD, FACT,
        OCCU, etc.) sous forme de tableau : Type, Description, Date, Lieu, Âge.
        """
        events_tab = ttk.Frame(self.tabs)
        self.tabs.add(events_tab, text=self.translator.get("view.events"))
        events_tab.grid_columnconfigure(0, weight=1)
        events_tab.grid_rowconfigure(0, weight=1)

        columns = ("type", "description", "date", "place", "age")
        self.events_tree = ttk.Treeview(
            events_tab, columns=columns, show="headings", height=8
        )
        headings = {
            "type": "view.events_type",
            "description": "view.events_description",
            "date": "view.events_date",
            "place": "view.events_place",
            "age": "view.events_age",
        }
        for column, label_key in headings.items():
            self.events_tree.heading(column, text=self.translator.get(label_key))
            self.events_tree.column(column, anchor="w", stretch=True, width=120)
        self.events_tree.grid(row=0, column=0, sticky="nsew")

        tree_scrollbar = ttk.Scrollbar(
            events_tab, orient="vertical", command=self.events_tree.yview
        )
        tree_scrollbar.grid(row=0, column=1, sticky="ns")
        self.events_tree.configure(yscrollcommand=tree_scrollbar.set)

    def _build_events_section(self, row):
        """Zone regroupant visuellement tous les tags "1 ..." restants
        (NAME, BIRT, BAPM, FCOM, GRAD, FACT, OCCU, etc.) avec leurs sous-tags,
        affichée au-dessus des onglets.
        """
        section = ttk.Frame(self)
        section.grid(row=row, column=0, columnspan=2, sticky="nsew", pady=(4, 0))
        section.grid_columnconfigure(0, weight=1)
        section.grid_rowconfigure(0, weight=1)

        canvas = tk.Canvas(section, highlightthickness=0, bg="#f7f7f7", height=180)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(section, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.events_container = ttk.Frame(canvas)
        canvas_window = canvas.create_window(
            (0, 0), window=self.events_container, anchor="nw"
        )
        self.events_container.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(canvas_window, width=e.width),
        )

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

    def set_object_resolver(self, resolver):
        self.object_resolver = resolver

    def set_object_display_name_resolver(self, resolver):
        self.object_display_name_resolver = resolver

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

    def _format_media_pointer(self, pointer):
        if not pointer:
            return "—"

        if callable(self.object_resolver) and callable(
            self.object_display_name_resolver
        ):
            try:
                media = self.object_resolver(pointer)
                if media is not None:
                    return self.object_display_name_resolver(media, "OBJE")
            except Exception:
                logger.exception(
                    "Échec de résolution de l’objet multimédia %s", pointer
                )

        return pointer

    def _tag_label(self, tag):
        key = GEDCOM_TAG_LABEL_KEYS.get(tag)
        if not key:
            return tag
        text = self.translator.get(key)
        return tag if text == key else text

    @staticmethod
    def _is_pointer(value):
        return (
            isinstance(value, str)
            and value.startswith("@")
            and value.endswith("@")
            and len(value) > 2
        )

    def _format_pointer_value(self, tag, pointer):
        if tag == "OBJE":
            return self._format_media_pointer(pointer)
        if tag == "NOTE":
            text, _ = self._format_note_entry(pointer)
            return text
        if pointer.startswith("@F"):
            return self._format_family_pointer(pointer)
        return pointer

    @staticmethod
    def _resolve_node_value(node):
        """Fusionne les sous-tags CONT/CONC dans la valeur du nœud et renvoie
        les autres enfants à afficher comme sous-lignes."""
        value = node.get("value") or ""
        children = []
        for child in node.get("children", []):
            if child["tag"] in _CONTINUATION_TAGS:
                separator = "\n" if child["tag"] == "CONT" else ""
                value = f"{value}{separator}{child.get('value') or ''}"
            else:
                children.append(child)
        return value, children

    def _clear_events(self):
        for child in self.events_container.winfo_children():
            child.destroy()

    def _render_events(self, events):
        self._clear_events()
        if not events:
            ttk.Label(self.events_container, text="—", font=("Segoe UI", 10)).pack(
                anchor="w", padx=8, pady=8
            )
            return

        for event in events:
            card = tk.Frame(self.events_container, bd=1, relief="solid", padx=8, pady=6)
            card.pack(fill="x", expand=True, padx=6, pady=4, anchor="n")

            value, children = self._resolve_node_value(event)
            header_text = self._tag_label(event["tag"])
            if value:
                header_text += f" : {value}"
            ttk.Label(card, text=header_text, font=("Segoe UI", 10, "bold")).pack(
                anchor="w"
            )

            self._render_event_children(card, children, depth=1)

    def _render_event_children(self, parent_widget, children, depth):
        for child in children:
            value, grandchildren = self._resolve_node_value(child)
            row = ttk.Frame(parent_widget)
            row.pack(anchor="w", padx=(depth * 16, 0), pady=1, fill="x")

            ttk.Label(
                row, text=self._tag_label(child["tag"]) + " :", foreground="#3b4a5a"
            ).pack(side="left")

            is_pointer = self._is_pointer(value)
            display_value = (
                self._format_pointer_value(child["tag"], value)
                if is_pointer
                else (value or "—")
            )
            value_label = ttk.Label(
                row, text=display_value, font=("Segoe UI", 10), justify="left"
            )
            value_label.pack(side="left", padx=(4, 0))
            if is_pointer:
                value_label.config(foreground="blue", cursor="hand2")
                value_label.bind(
                    "<Button-1>", lambda e, ptr=value: self.on_pointer_click(ptr)
                )

            self._render_event_children(parent_widget, grandchildren, depth + 1)

    _GEDCOM_MONTHS = {
        "JAN": 1,
        "FEB": 2,
        "MAR": 3,
        "APR": 4,
        "MAY": 5,
        "JUN": 6,
        "JUL": 7,
        "AUG": 8,
        "SEP": 9,
        "OCT": 10,
        "NOV": 11,
        "DEC": 12,
    }
    _GEDCOM_DATE_QUALIFIERS = {
        "ABT",
        "EST",
        "CAL",
        "AFT",
        "BEF",
        "FROM",
        "TO",
        "BET",
        "AND",
    }

    @classmethod
    def _parse_gedcom_date(cls, value):
        """Extraction approximative (année, mois, jour) d'une date GEDCOM,
        en ignorant les qualificatifs (ABT, AFT, BEF, CAL...)."""
        if not value:
            return None
        tokens = [
            token
            for token in value.strip().upper().split()
            if token not in cls._GEDCOM_DATE_QUALIFIERS
        ]
        year = month = day = None
        for token in tokens:
            if token in cls._GEDCOM_MONTHS:
                month = cls._GEDCOM_MONTHS[token]
            elif token.isdigit():
                if len(token) == 4:
                    year = int(token)
                else:
                    day = int(token)
        return (year, month, day) if year is not None else None

    @classmethod
    def _compute_age(cls, birth_value, event_value):
        birth = cls._parse_gedcom_date(birth_value)
        event = cls._parse_gedcom_date(event_value)
        if not birth or not event:
            return None
        birth_year, birth_month, birth_day = birth
        event_year, event_month, event_day = event
        age = event_year - birth_year
        if birth_month and event_month:
            if (event_month, event_day or 1) < (birth_month, birth_day or 1):
                age -= 1
        return age if age >= 0 else None

    @staticmethod
    def _format_age(value):
        """Force un affichage en années entières (tronque les valeurs
        décimales telles que "45.0" issues de certains fichiers GEDCOM)."""
        try:
            return str(int(float(value)))
        except (TypeError, ValueError):
            return value

    def _event_table_row(self, event, birth_date):
        value, children = self._resolve_node_value(event)
        direct_values = {}
        for child in children:
            child_value, _ = self._resolve_node_value(child)
            direct_values.setdefault(child["tag"], child_value)

        description = value or direct_values.get("TYPE", "")
        raw_date = direct_values.get("DATE", "")
        time = direct_values.get("TIME") or direct_values.get("_TIME")
        date = f"{raw_date} {time}".strip() if time else raw_date
        place = direct_values.get("PLAC", "")

        age = direct_values.get("AGE", "")
        if age:
            age = self._format_age(age)
        else:
            computed_age = self._compute_age(birth_date, raw_date)
            if computed_age is not None:
                age = str(computed_age)

        return (
            self._tag_label(event["tag"]),
            description or "—",
            date or "—",
            place or "—",
            age or "—",
        )

    def _render_events_table(self, events, birth_date=None):
        self.events_tree.delete(*self.events_tree.get_children())
        for event in events:
            self.events_tree.insert(
                "", "end", values=self._event_table_row(event, birth_date)
            )

    def _first_event_date(self, events, tags):
        """Date du premier événement dont le tag figure dans `tags` (ex: BAPM/CHR
        utilisé comme référence pour calculer l'âge quand la naissance est inconnue)."""
        for event in events:
            if event["tag"] not in tags:
                continue
            _, children = self._resolve_node_value(event)
            for child in children:
                if child["tag"] == "DATE":
                    value, _ = self._resolve_node_value(child)
                    if value:
                        return value
        return None

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
            self._render_events([])
            self._render_events_table([])
            for key, widget in self.labels.items():
                if isinstance(widget, ttk.Frame):
                    if key in ("fams", "notes", "gallery"):
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

            for row_widget in self.gallery_container.grid_slaves():
                if int(row_widget.grid_info().get("row", 0)) > 0:
                    row_widget.destroy()
            ttk.Label(self.gallery_container, text="—", font=("Segoe UI", 10)).grid(
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
                if key not in ("fams", "notes", "gallery"):
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

                # Gestion des listes (notes)
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

        for row_widget in self.gallery_container.grid_slaves():
            if int(row_widget.grid_info().get("row", 0)) > 0:
                row_widget.destroy()

        object_pointers = []
        instance_dict = getattr(individual, "__dict__", {})
        for attr_name in ("obje", "obj"):
            candidate = instance_dict.get(attr_name)
            if isinstance(candidate, (list, tuple, set)):
                object_pointers = list(candidate)
                break

            if attr_name in instance_dict:
                continue

            try:
                candidate = getattr(individual, attr_name)
            except Exception:
                candidate = None

            if isinstance(candidate, (list, tuple, set)):
                object_pointers = list(candidate)
                break

        if object_pointers:
            for row_index, pointer in enumerate(object_pointers, start=1):
                resolved_media = None
                if callable(self.object_resolver):
                    try:
                        resolved_media = self.object_resolver(pointer)
                    except Exception:
                        logger.exception("Échec de résolution de l’OBJE %s", pointer)

                name_text = pointer
                if resolved_media is not None and callable(
                    self.object_display_name_resolver
                ):
                    try:
                        name_text = self.object_display_name_resolver(
                            resolved_media, "OBJE"
                        )
                    except Exception:
                        logger.exception(
                            "Échec de formatage du nom de média %s", pointer
                        )
                elif resolved_media is not None:
                    name_text = (
                        getattr(resolved_media, "title", None)
                        or getattr(resolved_media, "file", None)
                        or pointer
                    )

                name_label = ttk.Label(
                    self.gallery_container,
                    text=name_text,
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
                    "<Button-1>", lambda e, ptr=pointer: self.on_pointer_click(ptr)
                )

                pointer_label = ttk.Label(
                    self.gallery_container,
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
            ttk.Label(self.gallery_container, text="—", font=("Segoe UI", 10)).grid(
                row=1, column=0, sticky="w"
            )

        all_events = getattr(individual, "events", None) or []
        table_events = [e for e in all_events if e["tag"] in _EVENT_TABLE_TAGS]
        other_events = [e for e in all_events if e["tag"] not in _EVENT_TABLE_TAGS]
        self._render_events(other_events)
        birth_reference = getattr(
            individual, "birth_date", None
        ) or self._first_event_date(table_events, ("BAPM", "CHR"))
        self._render_events_table(table_events, birth_reference)

    # ---------------------------------------------------------
    # Navigation par clic
    # ---------------------------------------------------------
    def on_pointer_click(self, pointer):
        if callable(self.on_pointer_click_callback):
            self.on_pointer_click_callback(pointer)
