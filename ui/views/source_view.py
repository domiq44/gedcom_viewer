import logging
import tkinter as tk
from tkinter import ttk

from ui.views.link_utils import configure_label, configure_text_widget
from ui.i18n import Translator


logger = logging.getLogger(__name__)


class SourceView(ttk.Frame):
    """
    Affiche une fiche Source (modèle Source).
    """

    def __init__(self, parent, on_pointer_click, translator=None):
        super().__init__(parent)

        self.on_pointer_click_callback = on_pointer_click
        self.translator = translator or Translator()
        self.reference_resolver = None
        self.configure(padding=10)

        self.title_label = ttk.Label(
            self, text=self.translator.get("view.source"), font=("Segoe UI", 12, "bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.labels = {}
        fields = [
            ("view.title", "title"),
            ("view.abbreviation", "abbreviation"),
            ("view.author", "author"),
            ("view.publication_date", "pub_date"),
            ("view.publication", "publication"),
            ("view.text", "text"),
            ("view.associated_repository", "repository"),
            ("view.call_number", "call_number"),
            ("view.media", "media"),
            ("view.agency", "agency"),
            ("view.notes", "notes"),
            ("view.sources", "sources"),
            ("view.references", "references"),
            ("view.internal_id", "record_id"),
            ("view.repository_note", "repo_note"),
            ("view.data_events", "data_events"),
            ("view.additional_fields", "additional_fields"),
        ]

        for i, (label_key, key) in enumerate(fields, start=1):
            ttk.Label(self, text=self.translator.get(label_key) + " :").grid(
                row=i, column=0, sticky="w"
            )
            if key == "text":
                frame = ttk.Frame(self, padding=(2, 2, 2, 2))
                frame.grid(row=i, column=1, sticky="nsew", padx=10, pady=2)
                scrollbar = ttk.Scrollbar(frame, orient="vertical")
                scrollbar.pack(side="right", fill="y")
                text_widget = tk.Text(
                    frame,
                    width=50,
                    height=6,
                    wrap="word",
                    font=("Segoe UI", 10),
                    yscrollcommand=scrollbar.set,
                    relief="sunken",
                    bd=1,
                    bg="#fafafa",
                    padx=6,
                    pady=6,
                )
                text_widget.pack(side="left", fill="both", expand=True)
                scrollbar.config(command=text_widget.yview)
                text_widget.config(state="disabled")
                self.labels[key] = text_widget
            else:
                value_label = ttk.Label(self, text="", font=("Segoe UI", 10))
                value_label.grid(row=i, column=1, sticky="w", padx=10)
                self.labels[key] = value_label

        for i in range(len(fields) + 1):
            self.grid_rowconfigure(i, pad=4)

    def set_reference_resolver(self, resolver):
        self.reference_resolver = resolver

    def _format_pointer_label(self, pointer):
        if not pointer:
            return "—"

        label = pointer
        if callable(self.reference_resolver):
            try:
                target = self.reference_resolver(pointer)
                if target is not None:
                    name = getattr(target, "name", None)
                    if isinstance(name, str) and name.strip():
                        label = f"{pointer} – {name}"
            except Exception:
                logger.exception("Échec de résolution du dépôt %s", pointer)

        return label

    def display(self, source):
        if not source:
            self.title_label.config(text=self.translator.get("view.source"))
            for key, widget in self.labels.items():
                if isinstance(widget, tk.Text):
                    configure_text_widget(widget, "")
                else:
                    configure_label(widget, "")
            return

        self.title_label.config(
            text=self.translator.get("view.source_pointer", pointer=source.pointer)
        )

        for key, widget in self.labels.items():
            value = getattr(source, key, "")

            if key == "repository":
                resolved_value = self._format_pointer_label(value) if value else "—"
                widget.config(
                    text=resolved_value,
                    foreground="blue" if value else "black",
                    cursor="hand2" if value else "",
                )
                widget.unbind("<Button-1>")
                if value:
                    widget.bind(
                        "<Button-1>", lambda e, ptr=value: self.on_pointer_click(ptr)
                    )
                continue

            if key == "text":
                configure_text_widget(widget, value)
                continue

            if isinstance(value, list):
                value = ", ".join(
                    self._format_additional_field(item)
                    if isinstance(item, dict)
                    else str(item)
                    for item in value
                )

            configure_label(widget, value)

    def on_pointer_click(self, pointer):
        if callable(self.on_pointer_click_callback):
            self.on_pointer_click_callback(pointer)

    @staticmethod
    def _format_additional_field(field):
        if "value" in field:
            text = f"{field.get('tag', '')}: {field.get('value', '')}".rstrip(": ")
            details = ", ".join(
                f"{tag}: {value}" if value else tag
                for tag, value in field.get("details", [])
            )
            return f"{text} ({details})" if details else text
        return str(field)
