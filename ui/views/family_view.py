# ui/views/family_view.py

import tkinter as tk
from tkinter import ttk


class FamilyView(ttk.Frame):
    """
    Affiche une fiche Famille (modèle Family).
    """

    def __init__(self, parent, on_pointer_click):
        super().__init__(parent)

        self.on_pointer_click_callback = on_pointer_click
        self.name_resolver = None
        self.source_resolver = None
        self.configure(padding=10)

        self.title_label = ttk.Label(
            self, text="Famille", font=("Segoe UI", 12, "bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.labels = {}

        fields = [
            ("Mari", "husband"),
            ("Femme", "wife"),
            ("Enfants", "children"),
            ("Nombre d'enfants", "number_of_children"),
            ("Date mariage", "marriage_date"),
            ("Lieu mariage", "marriage_place"),
            ("Engagement", "engagement"),
            ("Bans", "marriage_banns"),
            ("Contrat de mariage", "marriage_contract"),
            ("Licence de mariage", "marriage_license"),
            ("Régime matrimonial", "marriage_settlement"),
            ("Date divorce", "divorce_date"),
            ("Lieu divorce", "divorce_place"),
            ("Divorce prononcé", "divorce_final"),
            ("Annulation", "annulment"),
            ("Notes", "notes"),
            ("Sources", "sources"),
            ("Événements", "events"),
            ("Autres informations GEDCOM", "additional_fields"),
        ]

        for i, (label, key) in enumerate(fields, start=1):
            ttk.Label(self, text=label + " :").grid(row=i, column=0, sticky="w")
            if key in ("children", "notes", "sources", "events", "additional_fields"):
                container = tk.Frame(
                    self,
                    padx=8,
                    pady=6,
                    bg="#ffffff",
                    bd=1,
                    relief="solid",
                )
                container.grid(row=i, column=1, sticky="nsew", padx=10)
                self.labels[key] = container
            else:
                value_label = ttk.Label(self, text="", font=("Segoe UI", 10))
                value_label.grid(row=i, column=1, sticky="w", padx=10)
                self.labels[key] = value_label

    def set_name_resolver(self, resolver):
        self.name_resolver = resolver

    def set_source_resolver(self, resolver):
        self.source_resolver = resolver

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
                pass

        return label

    def display(self, family):
        if not family:
            self.title_label.config(text="Famille")
            for key, widget in self.labels.items():
                if key in ("children", "notes", "sources", "events", "additional_fields"):
                    for child in widget.winfo_children():
                        child.destroy()
                    label = ttk.Label(widget, text="—", font=("Segoe UI", 10))
                    label.pack(side="left")
                else:
                    widget.config(text="—", foreground="black", cursor="")
                    widget.unbind("<Button-1>")
            return

        self.title_label.config(text=f"Famille : {family.pointer}")

        def make_clickable(widget, pointer):
            widget.config(foreground="blue", cursor="hand2")
            widget.bind("<Button-1>", lambda e, ptr=pointer: self.on_pointer_click(ptr))

        for key, widget in self.labels.items():
            value = getattr(family, key, None)

            if key == "children":
                for child in widget.winfo_children():
                    child.destroy()

                if value:
                    for pointer in value:
                        child_label = ttk.Label(
                            widget,
                            text=self._format_pointer_with_name(pointer),
                            font=("Segoe UI", 10),
                            foreground="blue",
                            cursor="hand2",
                            justify="left",
                        )
                        child_label.pack(fill="x", pady=2)
                        child_label.bind(
                            "<Button-1>",
                            lambda e, ptr=pointer: self.on_pointer_click(ptr),
                        )
                else:
                    label = ttk.Label(widget, text="—", font=("Segoe UI", 10))
                    label.pack(fill="x")
                continue

            if key in ("notes", "sources", "events", "additional_fields"):
                for child in widget.winfo_children():
                    child.destroy()

                if value:
                    if key == "sources":
                        entries = [self._format_source(source) for source in value]
                    elif key == "notes":
                        entries = value
                    elif key == "events":
                        entries = [self._format_event(event) for event in value]
                    else:
                        entries = [self._format_additional_field(field) for field in value]
                    for index, entry in enumerate(entries):
                        pointer = value[index] if key == "sources" else None
                        label = ttk.Label(
                            widget,
                            text=entry,
                            font=("Segoe UI", 10),
                            justify="left",
                            foreground="blue" if pointer else "black",
                            cursor="hand2" if pointer else "",
                        )
                        label.pack(anchor="w", pady=1)
                        if pointer:
                            label.bind(
                                "<Button-1>",
                                lambda event, ptr=pointer: self.on_pointer_click(ptr),
                            )
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

            widget.config(text=value if value else "—")

    def on_pointer_click(self, pointer):
        if callable(self.on_pointer_click_callback):
            self.on_pointer_click_callback(pointer)

    def _format_source(self, pointer):
        if not pointer:
            return "—"
        if callable(self.source_resolver):
            try:
                source = self.source_resolver(pointer)
                title = getattr(source, "title", None) if source else None
                if isinstance(title, str) and title.strip():
                    return f"{pointer} – {title}"
            except Exception:
                pass
        return pointer

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
