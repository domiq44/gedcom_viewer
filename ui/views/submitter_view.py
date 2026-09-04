import tkinter as tk
from tkinter import ttk

from ui.views.link_utils import configure_label
from ui.i18n import Translator


class SubmitterView(ttk.Frame):
    """
    Affiche une fiche Submitter (entité SUBM).
    """

    def __init__(self, parent, on_pointer_click, translator=None):
        super().__init__(parent)

        self.on_pointer_click_callback = on_pointer_click
        self.translator = translator or Translator()
        self.reference_resolver = None
        self.configure(padding=10)

        self.title_label = ttk.Label(
            self,
            text=self.translator.get("view.submitter"),
            font=("Segoe UI", 12, "bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.labels = {}
        fields = [
            ("view.name", "name"),
            ("view.address", "address"),
            ("view.phone", "phone"),
            ("view.email", "email"),
        ]

        for i, (label_key, key) in enumerate(fields, start=1):
            ttk.Label(self, text=self.translator.get(label_key) + " :").grid(
                row=i, column=0, sticky="w"
            )
            value_label = ttk.Label(self, text="", font=("Segoe UI", 10))
            value_label.grid(row=i, column=1, sticky="w", padx=10)
            self.labels[key] = value_label

        for i in range(len(fields) + 1):
            self.grid_rowconfigure(i, pad=4)

    def set_reference_resolver(self, resolver):
        self.reference_resolver = resolver

    def display(self, submitter):
        if not submitter:
            self.title_label.config(text=self.translator.get("view.submitter"))
            for widget in self.labels.values():
                configure_label(widget, "")
            return

        self.title_label.config(
            text=self.translator.get(
                "view.submitter_pointer", pointer=submitter.pointer
            )
        )
        for key, widget in self.labels.items():
            values = getattr(submitter, f"{key}s", None)
            value = ", ".join(values) if values else getattr(submitter, key, "")
            configure_label(widget, value)

    def on_pointer_click(self, pointer):
        if callable(self.on_pointer_click_callback):
            self.on_pointer_click_callback(pointer)
