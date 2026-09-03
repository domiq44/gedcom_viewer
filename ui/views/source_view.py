import tkinter as tk
from tkinter import ttk


class SourceView(ttk.Frame):
    """
    Affiche une fiche Source (modèle Source).
    """

    def __init__(self, parent, on_pointer_click):
        super().__init__(parent)

        self.on_pointer_click_callback = on_pointer_click
        self.reference_resolver = None
        self.configure(padding=10)

        self.title_label = ttk.Label(self, text="Source", font=("Segoe UI", 12, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.labels = {}
        fields = [
            ("Titre", "title"),
            ("Abréviation", "abbreviation"),
            ("Auteur", "author"),
            ("Date publication", "pub_date"),
            ("Publication", "publication"),
            ("Texte", "text"),
            ("Dépôt associé", "repository"),
            ("Cote", "call_number"),
            ("Support", "media"),
            ("Agence", "agency"),
            ("Notes", "notes"),
            ("Sources", "sources"),
            ("Références", "references"),
            ("Identifiant interne", "record_id"),
            ("Note du dépôt", "repo_note"),
            ("Données / événements", "data_events"),
            ("Autres informations GEDCOM", "additional_fields"),
        ]

        for i, (label_text, key) in enumerate(fields, start=1):
            ttk.Label(self, text=label_text + " :").grid(row=i, column=0, sticky="w")
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
                pass

        return label

    def display(self, source):
        if not source:
            self.title_label.config(text="Source")
            for key, widget in self.labels.items():
                if isinstance(widget, tk.Text):
                    widget.config(state="normal")
                    widget.delete("1.0", tk.END)
                    widget.insert(tk.END, "—")
                    widget.config(state="disabled")
                else:
                    widget.config(text="—", foreground="black", cursor="")
                    widget.unbind("<Button-1>")
            return

        self.title_label.config(text=f"Source : {source.pointer}")

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
                widget.config(state="normal")
                widget.delete("1.0", tk.END)
                widget.insert(tk.END, value if value else "—")
                widget.config(state="disabled")
                continue

            if isinstance(value, list):
                value = ", ".join(
                    self._format_additional_field(item)
                    if isinstance(item, dict)
                    else str(item)
                    for item in value
                )

            widget.config(text=value if value else "—", foreground="black", cursor="")
            widget.unbind("<Button-1>")

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
