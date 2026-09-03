import logging
import tkinter as tk
from tkinter import ttk

from ui.views.link_utils import configure_label, configure_text_widget


logger = logging.getLogger(__name__)


class NoteView(ttk.Frame):
    """
    Affiche une fiche Note (modèle Note).
    """

    def __init__(self, parent, on_pointer_click):
        super().__init__(parent)

        self.on_pointer_click_callback = on_pointer_click
        self.reference_resolver = None
        self.configure(padding=10)

        self.title_label = ttk.Label(self, text="Note", font=("Segoe UI", 12, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        ttk.Label(self, text="Texte :").grid(row=1, column=0, sticky="nw")
        self.text_frame = ttk.Frame(self, padding=(0, 0, 0, 0))
        self.text_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 2), pady=(0, 4))

        self.scrollbar = ttk.Scrollbar(self.text_frame, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")

        self.text_widget = tk.Text(
            self.text_frame,
            width=70,
            height=12,
            wrap="word",
            font=("Segoe UI", 10),
            yscrollcommand=self.scrollbar.set,
            relief="sunken",
            bd=1,
            bg="#fafafa",
            padx=6,
            pady=6,
        )
        self.text_widget.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.text_widget.yview)
        self.text_widget.config(state="disabled")

        ttk.Label(self, text="Source :").grid(row=2, column=0, sticky="w")
        self.source_label = ttk.Label(self, text="—", font=("Segoe UI", 10))
        self.source_label.grid(row=2, column=1, sticky="w", padx=10)

        self.info_labels = {}
        fields = [
            ("Références", "references"),
            ("Identifiant interne", "record_id"),
            ("Submitters", "submitters"),
            ("Date de modification", "change_date"),
            ("Heure de modification", "change_time"),
            ("Autres informations GEDCOM", "additional_fields"),
        ]
        for row, (label_text, key) in enumerate(fields, start=3):
            ttk.Label(self, text=label_text + " :").grid(row=row, column=0, sticky="w")
            value_label = ttk.Label(self, text="—", font=("Segoe UI", 10))
            value_label.grid(row=row, column=1, sticky="w", padx=10)
            self.info_labels[key] = value_label

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def display(self, note):
        if not note:
            self.title_label.config(text="Note")
            configure_text_widget(self.text_widget, "")
            self.source_label.config(text="—", foreground="black", cursor="")
            self.source_label.unbind("<Button-1>")
            for widget in self.info_labels.values():
                widget.config(text="—", foreground="black", cursor="")
            return

        self.title_label.config(text=f"Note : {note.pointer}")
        configure_text_widget(self.text_widget, note.text)

        source = getattr(note, "source", None)
        source_label = source or "—"
        if source and callable(self.reference_resolver):
            try:
                target = self.reference_resolver(source)
                title = getattr(target, "title", None) if target else None
                if isinstance(title, str) and title.strip():
                    source_label = f"{source} – {title}"
            except Exception:
                logger.exception("Échec de résolution de la source %s", source)
                pass

        configure_label(self.source_label, source_label)
        if source:
            self.source_label.bind(
                "<Button-1>", lambda e, ptr=source: self.on_pointer_click(ptr)
            )

        for key, widget in self.info_labels.items():
            value = getattr(note, key, None)
            if key == "additional_fields":
                value = self._format_additional_fields(value)
            elif isinstance(value, list):
                value = ", ".join(str(item) for item in value)
            widget.config(text=value if value else "—")

    @staticmethod
    def _format_additional_fields(fields):
        formatted = []
        for field in fields or []:
            text = f"{field.get('tag', '')}: {field.get('value', '')}".rstrip(": ")
            details = ", ".join(
                f"{tag}: {value}" if value else tag
                for tag, value in field.get("details", [])
            )
            formatted.append(f"{text} ({details})" if details else text)
        return " | ".join(formatted)

    def set_reference_resolver(self, resolver):
        self.reference_resolver = resolver

    def on_pointer_click(self, pointer):
        if callable(self.on_pointer_click_callback):
            self.on_pointer_click_callback(pointer)
