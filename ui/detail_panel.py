"""Panneau de détail (GEDCOM brut et fiche entité)."""

import logging
import re
import tkinter as tk

from ui.copy_button import CopyButton
from ui.themes import COLORS, FONTS

logger = logging.getLogger(__name__)


class DetailPanel(tk.Frame):
    """Panel principal de visualisation du bloc GEDCOM brut et de l’entité sélectionnée."""

    def __init__(
        self, parent, translator, tooltip_factory=None, controller_provider=None
    ):
        """Initialise le panneau de détail."""
        super().__init__(parent, bg=COLORS["background"])
        self.translator = translator
        self.tooltip_factory = tooltip_factory
        self.controller_provider = controller_provider
        self.highlighter = None
        self._raw_content = ""
        self._fact_widgets = []
        self.indent_var = tk.BooleanVar(value=True)
        self.show_gedcom_view_var = tk.BooleanVar(value=False)
        self.show_entity_view_var = tk.BooleanVar(value=True)
        self._header_sync_after_id = None
        self._build()

    @property
    def raw_content(self):
        """Retourne le contenu GEDCOM brut courant."""
        return self._raw_content

    def destroy(self):
        """Annule les callbacks et détruit le panneau."""
        if self._header_sync_after_id is not None:
            try:
                self.after_cancel(self._header_sync_after_id)
            except Exception:
                logger.debug(
                    "Annulation du resynchroniseur d'en-tête impossible",
                    exc_info=True,
                )
            self._header_sync_after_id = None
        super().destroy()

    @staticmethod
    def _format_gedcom_block(content):
        """Formate un bloc GEDCOM pour l'affichage."""
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
        """Rafraîchit l'affichage du GEDCOM brut."""
        self.display_raw(self._raw_content)

    def _build(self):
        """Construit les widgets du panneau de détail."""
        self.view_toolbar = tk.Frame(self, bg=COLORS["background"])
        self.view_toolbar.pack(fill="x", pady=(0, 5))
        self.view_toolbar.grid_columnconfigure(0, weight=1)
        self.view_toolbar.grid_columnconfigure(1, weight=1)

        self.gedcom_header = tk.Frame(self.view_toolbar, bg=COLORS["background"])
        self.gedcom_header.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.gedcom_title = tk.Label(
            self.gedcom_header,
            text="GEDCOM",
            bg=COLORS["background"],
            fg=COLORS["section_title"],
            font=FONTS["title"],
        )
        self.gedcom_title.pack(side="left")
        self.show_gedcom_view_checkbox = tk.Checkbutton(
            self.gedcom_header,
            text=self.translator.get("ui.show_gedcom_view"),
            variable=self.show_gedcom_view_var,
            command=self._toggle_gedcom_view,
            bg=COLORS["background"],
            activebackground=COLORS["background"],
        )
        self.show_gedcom_view_checkbox.pack(side="right", padx=(8, 0))

        self.entity_header = tk.Frame(self.view_toolbar, bg=COLORS["background"])
        self.entity_header.grid(row=0, column=1, sticky="w")
        self.entity_view_title = tk.Label(
            self.entity_header,
            text=self.translator.get("ui.entity_view"),
            bg=COLORS["background"],
            fg=COLORS["section_title"],
            font=FONTS["title"],
        )
        self.entity_view_title.pack(side="left", padx=(12, 4))
        self.show_entity_view_checkbox = tk.Checkbutton(
            self.entity_header,
            text=self.translator.get("ui.show_entity_view"),
            variable=self.show_entity_view_var,
            command=self._toggle_entity_view,
            bg=COLORS["background"],
            activebackground=COLORS["background"],
        )
        self.show_entity_view_checkbox.pack(side="right")

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
            text="",
            padx=8,
            pady=8,
            bg=COLORS["background"],
            bd=1,
            relief="groove",
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["separator"],
        )
        self.split_pane.add(self.gedcom_frame, minsize=200, width=370, stretch="always")

        self.indent_checkbox = tk.Checkbutton(
            self.gedcom_header,
            text=self.translator.get("ui.indent"),
            variable=self.indent_var,
            command=self._refresh_display,
            bg=COLORS["background"],
            activebackground=COLORS["background"],
            state="normal" if self.show_gedcom_view_var.get() else "disabled",
        )
        self.indent_checkbox.pack(side="right", padx=(8, 0))
        self.copy_button = CopyButton(
            self.gedcom_header,
            command=self.copy_to_clipboard,
            tooltip_factory=self.tooltip_factory,
            tooltip_text=self.translator.get("ui.copy_gedcom"),
            state="normal" if self.show_gedcom_view_var.get() else "disabled",
        )
        self.copy_button.pack(side="right", padx=(8, 0))

        self.text_area = tk.Text(
            self.gedcom_frame,
            width=70,
            height=30,
            font=FONTS["mono"],
            state="disabled",
            relief="flat",
            bd=0,
            bg=COLORS["surface"],
            highlightthickness=0,
        )
        self.text_area.pack(fill="both", expand=True)
        self.split_pane.paneconfigure(
            self.gedcom_frame, hide=not self.show_gedcom_view_var.get()
        )

        self.entity_detail_frame = tk.LabelFrame(
            self.split_pane,
            text="",
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
        self.split_pane.paneconfigure(
            self.entity_detail_frame, hide=not self.show_entity_view_var.get()
        )
        self.split_pane.bind("<Configure>", self._schedule_header_sync, add="+")
        self.split_pane.bind("<B1-Motion>", self._schedule_header_sync, add="+")
        self.split_pane.bind("<ButtonRelease-1>", self._schedule_header_sync, add="+")

        self.identity_header = tk.Frame(
            self.entity_detail_frame, bg=COLORS["background"]
        )
        self.identity_header.pack(fill="x", pady=(0, 8))

        self.identity_title = tk.Label(
            self.identity_header,
            text=self.translator.get("ui.no_selection"),
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=FONTS["display_title"],
            anchor="w",
            justify="left",
        )
        self.identity_title.pack(fill="x", anchor="w")

        self.identity_subtitle = tk.Label(
            self.identity_header,
            text="",
            bg=COLORS["background"],
            fg=COLORS["muted_text"],
            font=FONTS["display_subtitle"],
            anchor="w",
            justify="left",
        )
        self.identity_subtitle.pack(fill="x", anchor="w", pady=(2, 0))

        self.identity_facts = tk.Frame(self.identity_header, bg=COLORS["background"])
        self.identity_facts.pack(fill="x", anchor="w", pady=(8, 0))
        self.identity_facts.grid_columnconfigure(1, weight=1)

        self.entity_detail_container = tk.Frame(
            self.entity_detail_frame,
            bg=COLORS["surface"],
            bd=0,
            relief="flat",
        )
        self.entity_detail_container.pack(fill="both", expand=True)
        self.entity_detail_container.grid_rowconfigure(0, weight=1)
        self.entity_detail_container.grid_columnconfigure(0, weight=1)

    def set_context(self, entity_type, entity):
        """Met à jour l'en-tête d'identité de l'entité courante."""
        summary = self._summary(entity_type, entity)
        self.identity_title.configure(
            text=summary["title"] or self._fallback_title(entity_type, entity)
        )
        self.identity_subtitle.configure(text=summary["subtitle"])
        self._render_facts(summary["facts"])

    def _summary(self, entity_type, entity):
        """Retourne le résumé du contrôleur, ou un résumé vide."""
        provider = self.controller_provider
        controller = provider() if provider is not None else None
        if controller is None or entity is None:
            return {"title": "", "subtitle": "", "facts": []}
        return controller.format_entity_summary(entity_type, entity)

    def _fallback_title(self, entity_type, entity):
        """Construit un titre minimal quand aucun résumé n'est disponible."""
        if entity is None:
            return self.translator.get("ui.no_selection")
        pointer = getattr(entity, "pointer", "") or "—"
        return f"{entity_type} · {pointer}" if entity_type else pointer

    def _render_facts(self, facts):
        """Affiche les couples libellé/valeur de l'en-tête."""
        for widgets in self._fact_widgets:
            for widget in widgets:
                widget.destroy()
        self._fact_widgets = []

        for row, (label, value) in enumerate(facts):
            label_widget = tk.Label(
                self.identity_facts,
                text=label,
                bg=COLORS["background"],
                fg=COLORS["muted_text"],
                font=FONTS["fact_label"],
                anchor="w",
            )
            label_widget.grid(row=row, column=0, sticky="w", padx=(0, 8))

            value_widget = tk.Label(
                self.identity_facts,
                text=value,
                bg=COLORS["background"],
                fg=COLORS["text"],
                font=FONTS["ui"],
                anchor="w",
                justify="left",
            )
            value_widget.grid(row=row, column=1, sticky="w")

            self._fact_widgets.append((label_widget, value_widget))

    def apply_theme(self):
        """Re-applique les couleurs du thème courant au panneau de détail."""
        background = COLORS["background"]
        surface = COLORS["surface"]
        separator = COLORS["separator"]
        self.configure(bg=background)
        self.view_toolbar.configure(bg=background)
        self.gedcom_header.configure(bg=background)
        self.gedcom_title.configure(bg=background, fg=COLORS["section_title"])
        self.show_gedcom_view_checkbox.configure(
            bg=background, activebackground=background
        )
        self.entity_header.configure(bg=background)
        self.entity_view_title.configure(bg=background, fg=COLORS["section_title"])
        self.show_entity_view_checkbox.configure(
            bg=background, activebackground=background
        )
        self.split_pane.configure(bg=background)
        self.gedcom_frame.configure(
            bg=background, highlightbackground=separator, highlightcolor=separator
        )
        self.indent_checkbox.configure(bg=background, activebackground=background)
        self.entity_detail_frame.configure(
            bg=background, highlightbackground=separator, highlightcolor=separator
        )
        self.identity_header.configure(bg=background)
        self.identity_title.configure(bg=background, fg=COLORS["text"])
        self.identity_subtitle.configure(bg=background, fg=COLORS["muted_text"])
        self.identity_facts.configure(bg=background)
        for label_widget, value_widget in self._fact_widgets:
            label_widget.configure(bg=background, fg=COLORS["muted_text"])
            value_widget.configure(bg=background, fg=COLORS["text"])
        self.entity_detail_container.configure(bg=surface)
        self.text_area.configure(bg=surface)

    def _toggle_entity_view(self):
        """Active ou désactive la vue entité."""
        if not self.show_entity_view_var.get() and not self.show_gedcom_view_var.get():
            self.show_gedcom_view_var.set(True)
        self._apply_view_visibility()

    def _toggle_gedcom_view(self):
        """Active ou désactive la vue GEDCOM brute."""
        if not self.show_gedcom_view_var.get() and not self.show_entity_view_var.get():
            self.show_entity_view_var.set(True)
        self._apply_view_visibility()

    def set_view_visibility(self, show_gedcom, show_entity):
        """Définit la visibilité des vues."""
        self.show_gedcom_view_var.set(bool(show_gedcom))
        self.show_entity_view_var.set(bool(show_entity))
        if not show_gedcom and not show_entity:
            self.show_entity_view_var.set(True)
        self._apply_view_visibility()

    def _apply_view_visibility(self):
        """Applique la visibilité courante des vues."""
        self.split_pane.paneconfigure(
            self.gedcom_frame, hide=not self.show_gedcom_view_var.get()
        )
        self.copy_button.configure(
            state="normal" if self.show_gedcom_view_var.get() else "disabled"
        )
        self.indent_checkbox.configure(
            state="normal" if self.show_gedcom_view_var.get() else "disabled"
        )
        self.split_pane.paneconfigure(
            self.entity_detail_frame, hide=not self.show_entity_view_var.get()
        )
        self._schedule_header_sync()

    def _schedule_header_sync(self, event=None):
        """Planifie la synchronisation des colonnes."""
        if self._header_sync_after_id is None and self.winfo_exists():
            self._header_sync_after_id = self.after_idle(self._sync_header_columns)

    def _sync_header_columns(self):
        """Synchronise les colonnes des vues."""
        self._header_sync_after_id = None
        if not self.winfo_exists():
            return

        if not (self.show_gedcom_view_var.get() and self.show_entity_view_var.get()):
            self.view_toolbar.grid_columnconfigure(0, minsize=0, weight=1)
            self.view_toolbar.grid_columnconfigure(1, minsize=0, weight=1)
            return

        try:
            sash_x, _ = self.split_pane.sash_coord(0)
        except tk.TclError:
            return

        sash_x = max(1, sash_x)
        self.view_toolbar.grid_columnconfigure(0, minsize=sash_x, weight=0)
        self.view_toolbar.grid_columnconfigure(1, minsize=0, weight=1)

    def display_raw(self, content):
        """Affiche un contenu GEDCOM brut."""
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

    def copy_to_clipboard(self):
        """Copie le contenu courant dans le presse-papiers."""
        text = self.text_area.get("1.0", tk.END).rstrip("\n")
        if not text:
            return False

        root = self.winfo_toplevel()
        root.clipboard_clear()
        root.clipboard_append(text)
        return True
