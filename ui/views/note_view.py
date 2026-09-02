import tkinter as tk
from tkinter import ttk


class NoteView(ttk.Frame):
    """
    Affiche une fiche Note (modèle Note).
    """

    def __init__(self, parent, on_pointer_click):
        super().__init__(parent)

        self.on_pointer_click_callback = on_pointer_click
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

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def display(self, note):
        if not note:
            self.title_label.config(text="Note")
            self.text_widget.config(state="normal")
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert(tk.END, "—")
            self.text_widget.config(state="disabled")
            return

        self.title_label.config(text=f"Note : {note.pointer}")
        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert(tk.END, note.text or "—")
        self.text_widget.config(state="disabled")

    def on_pointer_click(self, pointer):
        if callable(self.on_pointer_click_callback):
            self.on_pointer_click_callback(pointer)
