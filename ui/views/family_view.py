# ui/views/family_view.py

import logging
import tkinter as tk
from tkinter import ttk

from ui.views.link_utils import configure_label
from ui.themes import FONTS
from ui.i18n import Translator

logger = logging.getLogger(__name__)


class FamilyView(ttk.Frame):
    """
    Affiche une fiche Famille (modèle Family).
    """

    def __init__(self, parent, on_pointer_click, translator=None):
        super().__init__(parent)

        self.on_pointer_click_callback = on_pointer_click
        self.translator = translator or Translator()
        self.name_resolver = None
        self.source_resolver = None
        self.note_resolver = None
        self.display_name_resolver = None
        self.configure(padding=10)

        self.title_label = ttk.Label(
            self, text=self.translator.get("view.family"), font=("Segoe UI", 12, "bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 12))

        self.labels = {}

        fields = [
            ("view.husband", "husband"),
            ("view.wife", "wife"),
            ("view.children_count", "number_of_children"),
            ("view.marriage_date", "marriage_date"),
            ("view.marriage_place", "marriage_place"),
            ("view.marriages", "marriages"),
            ("view.engagement", "engagement"),
            ("view.marriage_banns", "marriage_banns"),
            ("view.marriage_contract", "marriage_contract"),
            ("view.marriage_license", "marriage_license"),
            ("view.marriage_settlement", "marriage_settlement"),
            ("view.divorce_date", "divorce_date"),
            ("view.divorce_place", "divorce_place"),
            ("view.divorce_final", "divorce_final"),
            ("view.annulment", "annulment"),
            ("view.additional_fields", "additional_fields"),
        ]

        for i, (label_key, key) in enumerate(fields, start=1):
            field_label = ttk.Label(
                self,
                text=self.translator.get(label_key) + " :",
                foreground="#3b4a5a",
            )
            field_label.grid(row=i, column=0, sticky="w", padx=(0, 10), pady=3)
            if key in (
                "marriages",
                "additional_fields",
            ):
                container = tk.Frame(
                    self,
                    padx=8,
                    pady=6,
                    bg="#ffffff",
                    bd=1,
                    relief="solid",
                )
                container.grid(row=i, column=1, sticky="nsew", padx=10, pady=2)
                self.labels[key] = container
            else:
                value_label = ttk.Label(self, text="", font=("Segoe UI", 10))
                value_label.grid(row=i, column=1, sticky="w", padx=10, pady=3)
                self.labels[key] = value_label

        tabs_row = len(fields) + 1
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(tabs_row, weight=1)

        self.tabs = ttk.Notebook(self)
        self.tabs.grid(
            row=tabs_row, column=0, columnspan=2, sticky="nsew", pady=(12, 0)
        )

        def build_two_column_tab(tab_title_key):
            tab = tk.Frame(self.tabs, bg="#ffffff")
            self.tabs.add(tab, text=self.translator.get(tab_title_key))
            container = tk.Frame(tab, padx=8, pady=6, bg="#ffffff")
            container.pack(fill="both", expand=True)
            container.grid_columnconfigure(0, weight=1)
            ttk.Label(
                container,
                text=self.translator.get("view.family_name"),
                font=("Segoe UI", 10, "bold"),
            ).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 4))
            ttk.Label(
                container,
                text=self.translator.get("view.family_identifier"),
                font=("Segoe UI", 10, "bold"),
            ).grid(row=0, column=1, sticky="w", pady=(0, 4))
            return container

        def build_single_column_tab(tab_title_key):
            tab = tk.Frame(self.tabs, bg="#ffffff")
            self.tabs.add(tab, text=self.translator.get(tab_title_key))
            container = tk.Frame(tab, padx=8, pady=6, bg="#ffffff")
            container.pack(fill="both", expand=True)
            return container

        self.labels["children"] = build_two_column_tab("view.children")
        self.labels["sources"] = build_two_column_tab("view.sources")
        self.labels["events"] = build_single_column_tab("view.events")
        self.labels["notes"] = build_two_column_tab("view.notes")

    def set_name_resolver(self, resolver):
        self.name_resolver = resolver

    def set_source_resolver(self, resolver):
        self.source_resolver = resolver

    def set_note_resolver(self, resolver):
        self.note_resolver = resolver

    def set_display_name_resolver(self, resolver):
        self.display_name_resolver = resolver

    def _format_pointer_with_name(self, pointer):
        if not pointer:
            return "—"

        label = pointer
        if callable(self.name_resolver):
            try:
                resolved = self.name_resolver(pointer)
                name = getattr(resolved, "name", None)
                if isinstance(name, str) and name.strip():
                    label = f"{pointer} – {name}"
            except Exception:
                logger.exception("Échec de résolution de l'individu %s", pointer)

        return label

    def _format_child_name(self, pointer):
        if not pointer:
            return "—"

        if callable(self.name_resolver) and callable(self.display_name_resolver):
            try:
                resolved = self.name_resolver(pointer)
                if resolved is not None:
                    return self.display_name_resolver(resolved, "INDI")
            except Exception:
                logger.exception("Échec de résolution de l'individu %s", pointer)

        return pointer

    def _format_source_title(self, pointer):
        if not pointer:
            return "—"

        if callable(self.source_resolver) and callable(self.display_name_resolver):
            try:
                resolved = self.source_resolver(pointer)
                if resolved is not None:
                    return self.display_name_resolver(resolved, "SOUR")
            except Exception:
                logger.exception("Échec de résolution de la source %s", pointer)

        return pointer

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

        if callable(self.note_resolver) and callable(self.display_name_resolver):
            try:
                resolved = self.note_resolver(entry)
                if resolved is not None:
                    return self.display_name_resolver(resolved, "NOTE"), entry
            except Exception:
                logger.exception("Échec de résolution de la note %s", entry)

        return entry, entry

    def display(self, family):
        if not family:
            self.title_label.config(text=self.translator.get("view.family"))
            for key, widget in self.labels.items():
                if key in ("children", "sources", "notes"):
                    for row_widget in widget.grid_slaves():
                        if int(row_widget.grid_info().get("row", 0)) > 0:
                            row_widget.destroy()
                    ttk.Label(widget, text="—", font=("Segoe UI", 10)).grid(
                        row=1, column=0, sticky="w"
                    )
                elif key in ("events", "marriages", "additional_fields"):
                    for child in widget.winfo_children():
                        child.destroy()
                    label = ttk.Label(widget, text="—", font=("Segoe UI", 10))
                    label.pack(side="left")
                else:
                    widget.config(text="—", foreground="black", cursor="")
                    widget.unbind("<Button-1>")
            return

        self.title_label.config(
            text=self.translator.get("view.family_pointer", pointer=family.pointer)
        )

        def make_clickable(widget, pointer):
            widget.config(foreground="blue", cursor="hand2")
            widget.bind("<Button-1>", lambda e, ptr=pointer: self.on_pointer_click(ptr))

        for key, widget in self.labels.items():
            value = getattr(family, key, None)

            if key == "children":
                for row_widget in widget.grid_slaves():
                    if int(row_widget.grid_info().get("row", 0)) > 0:
                        row_widget.destroy()

                if value:
                    for row_index, pointer in enumerate(value, start=1):
                        name_label = ttk.Label(
                            widget,
                            text=self._format_child_name(pointer),
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
                continue

            if key == "sources":
                for row_widget in widget.grid_slaves():
                    if int(row_widget.grid_info().get("row", 0)) > 0:
                        row_widget.destroy()

                if value:
                    for row_index, pointer in enumerate(value, start=1):
                        title_label = ttk.Label(
                            widget,
                            text=self._format_source_title(pointer),
                            font=("Segoe UI", 10),
                            foreground="blue",
                            cursor="hand2",
                            justify="left",
                        )
                        title_label.grid(
                            row=row_index, column=0, sticky="w", padx=(0, 10), pady=2
                        )
                        title_label.bind(
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
                continue

            if key == "notes":
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
                            row=row_index, column=0, sticky="w", padx=(0, 10), pady=2
                        )

                        pointer_label = ttk.Label(
                            widget,
                            text=pointer or "—",
                            font=("Segoe UI", 10),
                        )
                        pointer_label.grid(row=row_index, column=1, sticky="w", pady=2)

                        if pointer:
                            for label in (text_label, pointer_label):
                                label.config(foreground="blue", cursor="hand2")
                                label.bind(
                                    "<Button-1>",
                                    lambda e, ptr=pointer: self.on_pointer_click(ptr),
                                )
                else:
                    ttk.Label(widget, text="—", font=("Segoe UI", 10)).grid(
                        row=1, column=0, sticky="w"
                    )
                continue

            if key in (
                "events",
                "marriages",
                "additional_fields",
            ):
                for child in widget.winfo_children():
                    child.destroy()

                if value:
                    if key == "events":
                        entries = [self._format_event(event) for event in value]
                    elif key == "marriages":
                        entries = [self._format_event(event) for event in value]
                    else:
                        entries = [
                            self._format_additional_field(field) for field in value
                        ]
                    for entry in entries:
                        label = ttk.Label(
                            widget,
                            font=("Segoe UI", 10),
                            justify="left",
                        )
                        configure_label(label, entry)
                        label.pack(anchor="w", pady=1)
                else:
                    label = ttk.Label(widget, text="—", font=("Segoe UI", 10))
                    label.pack(anchor="w")
                continue

            widget.unbind("<Button-1>")
            widget.config(cursor="", foreground="black")

            if key in ("husband", "wife"):
                widget.config(
                    text=self._format_pointer_with_name(value) if value else "—"
                )
                if value:
                    make_clickable(widget, value)
                continue

            configure_label(widget, value)

    def on_pointer_click(self, pointer):
        if callable(self.on_pointer_click_callback):
            self.on_pointer_click_callback(pointer)

    @staticmethod
    def _format_event(event):
        parts = [event.get("value", "")]
        parts.extend(
            f"{tag}: {value}" if value else tag
            for tag, value in event.get("details", [])
        )
        return " | ".join(part for part in parts if part)

    @staticmethod
    def _format_additional_field(field):
        parts = [f"{field.get('tag', '')}: {field.get('value', '')}".rstrip(": ")]
        parts.extend(
            f"{tag}: {value}" if value else tag
            for tag, value in field.get("details", [])
        )
        return " | ".join(part for part in parts if part)
