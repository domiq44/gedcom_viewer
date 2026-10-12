import re
import tkinter as tk

from ui.themes import COLORS, FONTS


class DetailPanel(tk.Frame):
    """Panel principal de visualisation du bloc GEDCOM brut et de l’entité sélectionnée."""

    def __init__(self, parent, translator):
        super().__init__(parent, bg=COLORS["background"])
        self.translator = translator
        self.highlighter = None
        self._raw_content = ""
        self.indent_var = tk.BooleanVar(value=False)
        self._copy_reset_after_id = None
        self._build()

    def destroy(self):
        if self._copy_reset_after_id is not None:
            try:
                self.after_cancel(self._copy_reset_after_id)
            except Exception:
                pass
            self._copy_reset_after_id = None
        super().destroy()

    @staticmethod
    def _format_gedcom_block(content):
        if not content:
            return ""

        lines = content.splitlines()
        rendered = []
        for raw_line in lines:
            stripped = raw_line.strip()
            if not stripped:
                rendered.append("")
                continue

            match = re.match(r"^(\d+)\s+(.*)$", stripped)
            if not match:
                rendered.append(stripped)
                continue

            level = int(match.group(1))
            remainder = match.group(2)
            prefix = "  " * level
            rendered.append(f"{prefix}{level} {remainder}")

        return "\n".join(rendered)

    def _refresh_display(self):
        self.display_raw(self._raw_content)

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

        toolbar = tk.Frame(self.gedcom_frame, bg=COLORS["background"])
        toolbar.pack(fill="x", pady=(0, 5))
        tk.Label(
            toolbar, text=self.translator.get("ui.raw_content"), bg=COLORS["background"]
        ).pack(anchor="w", side="left")
        tk.Checkbutton(
            toolbar,
            text=self.translator.get("ui.indent"),
            variable=self.indent_var,
            command=self._refresh_display,
            bg=COLORS["background"],
            activebackground=COLORS["background"],
        ).pack(anchor="e", side="right", padx=(0, 8))

        self.copy_button = tk.Button(
            toolbar,
            text=self.translator.get("ui.copy_to_clipboard"),
            command=self.copy_to_clipboard,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            relief="solid",
            bd=1,
            padx=8,
        )
        self.copy_button.pack(anchor="e", side="right")

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
        self._raw_content = content or ""
        rendered = (
            self._format_gedcom_block(self._raw_content)
            if self.indent_var.get()
            else self._raw_content
        )

        self.text_area.config(state="normal")
        try:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, rendered)
        finally:
            self.text_area.config(state="disabled")

        if self.highlighter is not None:
            self.highlighter.highlight()

    def _reset_copy_button_text(self):
        if not self.winfo_exists():
            return
        self.copy_button.config(text=self.translator.get("ui.copy_to_clipboard"))
        self._copy_reset_after_id = None

    def copy_to_clipboard(self):
        text = self.text_area.get("1.0", tk.END).rstrip("\n")
        if not text:
            return

        root = self.winfo_toplevel()
        root.clipboard_clear()
        root.clipboard_append(text)
        self.copy_button.config(text=self.translator.get("ui.copied"))
        if self._copy_reset_after_id is not None:
            try:
                self.after_cancel(self._copy_reset_after_id)
            except Exception:
                pass
        self._copy_reset_after_id = self.after(1200, self._reset_copy_button_text)
