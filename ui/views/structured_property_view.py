"""Base des fiches structurées (texte sélectionnable, liens)."""

import tkinter as tk
from tkinter import ttk

from controllers.detail_formatter import field_parts
from gedcom.continuations import append_continuation
from ui.themes import COLORS, FONTS
from ui.views.entity_view_base import EntityViewBase
from ui.views.structured_link_renderer import StructuredLinkRenderer
from ui.views.structured_row_factory import StructuredRowFactory
from ui.views.structured_section_builder import StructuredSectionBuilder

_CORE_EVENTS = frozenset({"BIRT", "DEAT", "CHR"})
_CONTAINER_TAGS = frozenset({"DATA"})

TAG_LABEL_KEYS = {
    "BIRT": "view.birth_date",
    "DEAT": "view.death_date",
    "CHR": "view.baptism_date",
    "BAPM": "view.baptism",
    "NAME": "view.name",
    "GIVN": "view.given_name",
    "SURN": "view.surname",
    "NPFX": "view.name_prefix",
    "NSFX": "view.name_suffix",
    "SPFX": "view.surname_prefix",
    "SEX": "view.sex",
    "NICK": "view.nickname",
    "FAMC": "view.child_family",
    "FAMS": "view.family_parent_families",
    "HUSB": "view.husband",
    "WIFE": "view.wife",
    "CHIL": "view.children",
    "NCHI": "view.children_count",
    "ADOP": "view.adoption",
    "BURI": "view.burial",
    "CREM": "view.cremation",
    "DSCR": "view.description",
    "GRAD": "view.graduation",
    "RETI": "view.retirement",
    "CENS": "view.census",
    "RESI": "view.residence",
    "EMIG": "view.emigration",
    "IMMI": "view.immigration",
    "FACT": "view.fact",
    "FCOM": "view.first_communion",
    "ADDR": "view.address",
    "ADR1": "view.address_line",
    "CITY": "view.city",
    "CTRY": "view.country",
    "OCCU": "view.occupations",
    "NOTE": "view.notes",
    "EVEN": "view.events",
    "ENGA": "view.engagement",
    "MARB": "view.marriage_banns",
    "MARC": "view.marriage_contract",
    "MARL": "view.marriage_license",
    "MARS": "view.marriage_settlement",
    "DIVF": "view.divorce_final",
    "ANUL": "view.annulment",
    "SOUR": "view.source",
    "DATA": "view.data",
    "DATE": "view.date",
    "TIME": "view.time",
    "PLAC": "view.place",
    "CHAN": "view.change_information",
    "MAP": "view.map_coordinates",
    "LATI": "view.latitude",
    "LONG": "view.longitude",
    "PAGE": "view.page",
    "QUAY": "view.source_quality",
    "ROLE": "view.role",
    "TYPE": "view.type",
    "CAUS": "view.cause",
    "AGNC": "view.agency",
    "RELA": "view.relationship",
    "CONT": "view.continuation",
    "CONC": "view.text_continuation",
    "TEXT": "view.text",
    "EVENTEXT": "view.event_text",
    "OBJE": "view.multimedia",
    "FILE": "view.file",
    "FORM": "view.format",
    "ASSO": "view.association",
    "PEDI": "view.pedigree",
    "MARR": "view.marriages",
    "DIV": "view.divorces",
}


class StructuredPropertyView(EntityViewBase):
    """Base des fiches structurées : contenu sélectionnable, liens et défilement."""

    def __init__(
        self,
        parent,
        on_pointer_click,
        translator,
        entity_type,
        title_key,
        tooltip_factory=None,
    ):
        """Initialise la fiche structurée."""
        super().__init__(parent, on_pointer_click, translator, entity_type)
        self.tooltip_factory = tooltip_factory
        self.title_key = title_key
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.title_label = ttk.Label(
            self,
            text=self.translator.get(title_key),
            font=FONTS["title"],
        )
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.canvas = tk.Canvas(
            self,
            background=COLORS["background"],
            highlightthickness=0,
            borderwidth=0,
        )
        self.canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel, add="+")
        self.canvas.bind("<Button-4>", self._on_mousewheel, add="+")
        self.canvas.bind("<Button-5>", self._on_mousewheel, add="+")

        self.content = ttk.Frame(self.canvas, padding=(4, 4))
        self._bind_scroll_widget(self.content)
        self._content_window = self.canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self.content.bind(
            "<Configure>",
            lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind("<Configure>", self._resize_content)
        self._bind_scroll_widget(self.title_label)

        self.section_builder = StructuredSectionBuilder(
            self.content,
            self.translator,
            lambda: self.tooltip_factory,
            self._bind_scroll_widget,
        )
        self.sections = self.section_builder.sections
        self.section_copy_buttons = self.section_builder.copy_buttons
        self._section_titles = self.section_builder.titles
        self._section_rows = self.section_builder.rows

        self.row_factory = StructuredRowFactory(
            self._bind_scroll_widget,
            self._begin_pointer_activation,
            self._finish_pointer_activation,
        )

        self.links = {}
        self.value_widgets = []
        self.tag_widgets = []

    def _bind_scroll_widget(self, widget):
        """Lie le défilement au widget."""
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_mousewheel, add="+")
        widget.bind("<Button-5>", self._on_mousewheel, add="+")

    def _on_mousewheel(self, event):
        """Gère le défilement à la molette."""
        button = getattr(event, "num", None)
        if button == 4:
            units = -1
        elif button == 5:
            units = 1
        else:
            delta = getattr(event, "delta", 0)
            if abs(delta) >= 120:
                units = int(-delta / 120)
                if units == 0:
                    units = -1 if delta > 0 else 1
            else:
                units = -1 if delta > 0 else 1 if delta < 0 else 0
        if units:
            self.canvas.yview_scroll(units, "units")
        return "break"

    def _resize_content(self, event):
        """Redimensionne le contenu défilant."""
        self.canvas.itemconfigure(self._content_window, width=event.width)

    def apply_theme(self):
        """Re-applique les couleurs du thème courant aux widgets persistants."""
        self.canvas.configure(background=COLORS["background"])
        for widget in self.value_widgets:
            if isinstance(widget, tk.Text):
                widget.configure(
                    background=COLORS["background"],
                    foreground=COLORS["text"],
                    insertbackground=COLORS["text"],
                )

    def _section(self, title):
        """Dessine une section de la fiche."""
        return self.section_builder.build(title)

    def _row(self, section, row, label, value, pointer=None, depth=0):
        """Dessine une ligne de la fiche."""
        text = self._display_pointer(pointer) if pointer else str(value)
        self._section_rows[section].append((label, text))
        tag_widget, value_widget = self.row_factory.create(
            section,
            row,
            label,
            text,
            pointer=pointer,
            depth=depth,
        )
        self.tag_widgets.append(tag_widget)
        self.value_widgets.append(value_widget)
        if pointer:
            self.links.setdefault(pointer, []).append(value_widget)

    @staticmethod
    def _begin_pointer_activation(event, target):
        """Démarre l'activation du pointeur courant."""
        StructuredLinkRenderer.begin(event, target)

    def _finish_pointer_activation(self, event, target):
        """Termine l'activation du pointeur courant."""
        StructuredLinkRenderer.finish(event, target, self._navigate_pointer)

    @staticmethod
    def _event_parts(event):
        """Décompose un événement en parties."""
        if isinstance(event, dict):
            return (
                event.get("tag", ""),
                event.get("value"),
                event.get("children") or event.get("details") or [],
            )
        tag = getattr(event, "tag", None)
        if tag is not None:
            return tag, getattr(event, "value", ""), getattr(event, "details", []) or []
        return None, None, []

    def _join_text_continuations(self, details):
        """Joint les continuations de texte via le résolveur de présentation."""
        items = []
        for detail in details:
            if isinstance(detail, tuple) and len(detail) == 2:
                tag, value = detail
            else:
                tag, value, _children = self._event_parts(detail)
            items.append({"tag": tag, "value": value})
        merged = self._format_details(items)
        return [(item.get("tag", ""), item.get("value")) for item in merged]

    def _tag_label(self, tag, value=None):
        """Retourne le libellé d'un tag."""
        key = TAG_LABEL_KEYS.get(tag)
        if self._is_pointer(value) and (tag == "ASSO" or key is None):
            target_type = self._pointer_entity_type(value)
            if target_type == "INDI":
                key = "view.referenced_individual"
            elif target_type == "OBJE":
                key = "view.multimedia"
        if key:
            return self.translator.get(key)
        if isinstance(tag, str) and tag.startswith("_"):
            return tag
        return self.translator.get("view.other_gedcom_tag", tag=tag)

    def _render_event(
        self, section, row, event, depth=0, root_tag=None, root_label=None
    ):
        """Rend un événement dans la fiche."""
        tag, value, children = self._event_parts(event)
        if not tag:
            return row

        is_root = root_tag is None
        # Pour un node texte (TEXT / EVENTEXT) qui n'est pas la racine, fusionner
        # ses continuations CONT / CONC dans sa valeur et n'afficher qu'une seule
        # ligne. DATA est un conteneur (DATE, TEXT, QUAY...), pas un node texte :
        # on ne l'affiche pas, on laisse _render_children rendre ses enfants.
        if tag in ("TEXT", "EVENTEXT") and not is_root:
            merged_value = value or ""
            other_children = []
            for child in children:
                child_tag, child_value, _ = self._event_parts(child)
                if child_tag in ("CONT", "CONC") and child_value:
                    merged_value = append_continuation(
                        merged_value, child_tag, child_value
                    )
                else:
                    other_children.append(child)
            if merged_value:
                self._row(section, row, "", merged_value, depth=depth)
                row += 1
            return self._render_children(
                section, row, other_children, depth, False, tag
            )

        label = (
            root_label or self._tag_label(tag, value)
            if is_root
            else self._tag_label(tag, value)
        )
        row = self._render_event_row(
            section, row, label, tag, value, children, depth, is_root
        )
        core_event = tag in _CORE_EVENTS and is_root
        return self._render_children(section, row, children, depth, core_event, tag)

    def _render_event_row(
        self, section, row, label, tag, value, children, depth, is_root
    ):
        """Affiche la ligne principale d'un événement."""
        if value not in (None, ""):
            pointer = value if self._is_pointer(value) else None
            self._row(section, row, label, value, pointer=pointer, depth=depth)
            return row + 1
        if tag == "MAP" and children:
            self._row(section, row, label, "", depth=depth)
            return row + 1
        if is_root and tag not in _CORE_EVENTS:
            # Node racine sans valeur propre :
            # - s'il est un conteneur (ex: DATA dans une citation), on ne
            #  n'affiche pas de tiret et on laisse _render_children rendre
            #  ses enfants (DATE, TEXT avec ses continuations, etc.)
            # - sinon on affiche un tiret et on rend aussi les enfants
            if children and tag in _CONTAINER_TAGS:
                return row
            self._row(section, row, label, "—", depth=depth)
            return row + 1
        return row

    def _render_children(self, section, row, children, depth, core_event, parent_tag):
        """Affiche les enfants d'un événement."""
        for child in children:
            child_tag, child_value, child_children = self._event_parts(child)
            if core_event and child_tag == "DATE":
                continue
            if core_event and child_tag == "PLAC" and not child_children:
                continue
            if isinstance(child, tuple) and len(child) == 2:
                child_tag, child_value = child
                child = {"tag": child_tag, "value": child_value, "children": []}
                child_children = []
            if child_tag and not child_children:
                pointer = child_value if self._is_pointer(child_value) else None
                self._row(
                    section,
                    row,
                    self._tag_label(child_tag, child_value),
                    child_value if child_value not in (None, "") else "—",
                    pointer=pointer,
                    depth=depth + 1,
                )
                row += 1
            elif child_tag:
                row = self._render_event(
                    section, row, child, depth + 1, root_tag=parent_tag
                )
        return row

    def _display_labelled_section(self, title_key, fields):
        """Affiche une section de couples libellé/valeur non vides."""
        present = [
            (self.translator.get(key), value)
            for key, value in fields
            if value not in (None, "")
        ]
        if not present:
            return
        section = self._section(self.translator.get(title_key))
        for row, (label, value) in enumerate(present):
            self._row(section, row, label, value)

    def _display_contact_rows(self, entity, attributes):
        """Affiche les coordonnées regroupées d'une entité."""
        rows: list[tuple[str, str]] = []
        for attribute, singular_attribute, label_key in attributes:
            values = list(getattr(entity, attribute, None) or [])
            singular_value = getattr(entity, singular_attribute, None)
            if singular_value and singular_value not in values:
                values.insert(0, singular_value)
            rows.extend(
                (self.translator.get(label_key), value) for value in values if value
            )
        if not rows:
            return
        section = self._section(self.translator.get("view.contact_information"))
        for row, (label, value) in enumerate(rows):
            self._row(section, row, label, value)

    def _display_identity(self, entity):
        """Affiche le pointeur de l'entité."""
        self._display_pointer_label(getattr(entity, "pointer", "") or "")

    def _display_pointer_label(self, text):
        """Affiche un pointeur en texte secondaire sous le titre."""
        label = ttk.Label(
            self.content,
            text=text,
            foreground=COLORS["muted_text"],
        )
        label.pack(anchor="w", padx=4, pady=(0, 10))
        self._bind_scroll_widget(label)

    def _display_pointer_lists(self, entity, attributes):
        """Affiche des listes de pointeurs d'une entité."""
        for attribute, title_key in attributes:
            values = getattr(entity, attribute, None) or []
            if not values:
                continue
            section = self._section(self.translator.get(title_key))
            for row, value in enumerate(values):
                pointer = value if self._is_pointer(value) else None
                self._row(section, row, "", value, pointer=pointer)

    def _display_additional_fields(self, entity):
        """Affiche les champs GEDCOM additionnels d'une entité."""
        additional_fields = getattr(entity, "additional_fields", None) or []
        if not additional_fields:
            return
        section = self._section(self.translator.get("view.additional_fields"))
        row = 0
        for field in additional_fields:
            tag, value, details = field_parts(field)
            self._row(
                section,
                row,
                self._tag_label(tag) if tag else "",
                value if value not in (None, "") else "—",
                pointer=value if self._is_pointer(value) else None,
            )
            row += 1
            for detail_tag, detail_value in self._join_text_continuations(details):
                if not detail_tag:
                    continue
                pointer = detail_value if self._is_pointer(detail_value) else None
                self._row(
                    section,
                    row,
                    self._tag_label(detail_tag, detail_value),
                    detail_value if detail_value not in (None, "") else "—",
                    pointer=pointer,
                    depth=1,
                )
                row += 1

    def _clear(self):
        """Efface le contenu de la fiche."""
        for child in self.content.winfo_children():
            child.destroy()
        self.section_builder.reset()
        self.links = {}
        self.value_widgets = []
        self.tag_widgets = []
        self.canvas.yview_moveto(0)
