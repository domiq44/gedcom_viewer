import tkinter as tk


class StatusBar(tk.LabelFrame):
    """Barre d’état de l’application, dédiée aux messages de log UI."""

    def __init__(self, parent, translator, status_var):
        super().__init__(
            parent,
            text=translator.get("ui.log_status"),
            padx=6,
            pady=4,
        )
        self.translator = translator
        self.status_var = status_var
        self._build()

    def _build(self):
        self.status_label = tk.Entry(
            self,
            textvariable=self.status_var,
            font=("TkDefaultFont", 9),
            state="readonly",
            readonlybackground=self.cget("background"),
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
        )
        self.status_label.pack(fill="x", expand=True)
