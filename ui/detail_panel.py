import tkinter as tk

from ui.themes import COLORS, FONTS


class DetailPanel(tk.Frame):
    """Panel principal de visualisation du bloc GEDCOM brut et de l’entité sélectionnée."""

    def __init__(self, parent, translator):
        super().__init__(parent, bg=COLORS["background"])
        self.translator = translator
        self._build()

    def _build(self):
        self.split_pane = tk.PanedWindow(
            self,
            orient="horizontal",
            sashrelief="raised",
            sashwidth=6,
            bg=COLORS["background"],
        )
        self.split_pane.pack(fill="both", expand=True)

        self.gedcom_frame = tk.LabelFrame(
            self.split_pane,
            text="GEDCOM",
            padx=8,
            pady=8,
            bg=COLORS["background"],
            bd=1,
            relief="groove",
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["separator"],
        )
        self.split_pane.add(self.gedcom_frame, minsize=200, width=370, stretch="always")

        tk.Label(self.gedcom_frame, text=self.translator.get("ui.raw_content")).pack(
            anchor="w", pady=(0, 5)
        )
        self.text_area = tk.Text(
            self.gedcom_frame,
            width=70,
            height=30,
            font=FONTS["mono"],
            state="disabled",
            relief="solid",
            bd=1,
            bg="#fcfcfd",
            highlightthickness=1,
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["selection"],
        )
        self.text_area.pack(fill="both", expand=True)

        self.entity_detail_frame = tk.LabelFrame(
            self.split_pane,
            text=self.translator.get("ui.entity_view"),
            padx=8,
            pady=8,
            bg=COLORS["background"],
            bd=1,
            relief="groove",
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["separator"],
        )
        self.split_pane.add(
            self.entity_detail_frame, minsize=300, width=370, stretch="always"
        )

        self.entity_detail_container = tk.Frame(
            self.entity_detail_frame, bg=COLORS["surface"], bd=1, relief="solid"
        )
        self.entity_detail_container.pack(fill="both", expand=True)
        self.entity_detail_container.grid_rowconfigure(0, weight=1)
        self.entity_detail_container.grid_columnconfigure(0, weight=1)

        self.entity_detail_frame.grid_columnconfigure(0, weight=1)
        self.entity_detail_frame.grid_rowconfigure(0, weight=1)

    def display_raw(self, content):
        self.text_area.config(state="normal")
        try:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, content)
        finally:
            self.text_area.config(state="disabled")
