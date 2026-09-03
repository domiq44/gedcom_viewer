import logging
import tkinter as tk
from tkinter import ttk

from ui.views.link_utils import configure_label


logger = logging.getLogger(__name__)


class RepositoryView(ttk.Frame):
    """
    Affiche une fiche Repository (modèle Repository).
    """

    def __init__(self, parent, on_pointer_click):
        super().__init__(parent)

        self.on_pointer_click_callback = on_pointer_click
        self.reference_resolver = None
        self.configure(padding=10)

        self.title_label = ttk.Label(self, text="Dépôt", font=("Segoe UI", 12, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.labels = {}
        fields = [
            ("Nom", "name"),
            ("Ligne 1", "address"),
            ("Ville", "city"),
            ("État/Pays", "state"),
            ("Code postal", "postal_code"),
            ("Adresse complémentaire 1", "address_line_1"),
            ("Adresse complémentaire 2", "address_line_2"),
            ("Pays", "country"),
            ("Notes", "notes"),
            ("Références", "references"),
            ("Identifiant interne", "record_id"),
            ("Date de modification", "change_date"),
            ("Heure de modification", "change_time"),
            ("Autres informations GEDCOM", "additional_fields"),
        ]

        for i, (label_text, key) in enumerate(fields, start=1):
            ttk.Label(self, text=label_text + " :").grid(row=i, column=0, sticky="w")
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
                logger.exception("Échec de résolution de l'entité %s", pointer)

        return label

    def display(self, repo):
        if not repo:
            self.title_label.config(text="Dépôt")
            for widget in self.labels.values():
                configure_label(widget, "")
            return

        self.title_label.config(text=f"Dépôt : {repo.pointer}")

        for key, widget in self.labels.items():
            value = getattr(repo, key, "")
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
        text = f"{field.get('tag', '')}: {field.get('value', '')}".rstrip(": ")
        details = ", ".join(
            f"{tag}: {value}" if value else tag
            for tag, value in field.get("details", [])
        )
        return f"{text} ({details})" if details else text
