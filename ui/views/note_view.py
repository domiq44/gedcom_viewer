import tkinter as tk
from tkinter import ttk


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

        self.text_frame = ttk.Frame(self, padding=(0, 0, 0, 0))
        self.text_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=(0, 4))

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

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def display(self, note):
        if not note:
            self.title_label.config(text="Note")
            self.text_widget.config(state="normal")
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert(tk.END, "—")
            self.text_widget.config(state="disabled")
            self.source_label.config(text="—", foreground="black", cursor="")
            self.source_label.unbind("<Button-1>")
            return

        self.title_label.config(text=f"Note : {note.pointer}")
        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert(tk.END, note.text or "—")
        self.text_widget.config(state="disabled")

        source = getattr(note, "source", None)
        source_label = source or "—"
        if source and callable(self.reference_resolver):
            try:
                target = self.reference_resolver(source)
                title = getattr(target, "title", None) if target else None
                if isinstance(title, str) and title.strip():
                    source_label = f"{source} – {title}"
            except Exception:
                pass

        self.source_label.config(
            text=source_label,
            foreground="blue" if source else "black",
            cursor="hand2" if source else "",
        )
        self.source_label.unbind("<Button-1>")
        if source:
            self.source_label.bind(
                "<Button-1>", lambda e, ptr=source: self.on_pointer_click(ptr)
            )

    def set_reference_resolver(self, resolver):
        self.reference_resolver = resolver

    def on_pointer_click(self, pointer):
        if callable(self.on_pointer_click_callback):
            self.on_pointer_click_callback(pointer)
