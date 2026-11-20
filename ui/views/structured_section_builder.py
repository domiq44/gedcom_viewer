"""Construction des sections et copie du contenu des fiches structurées."""

from tkinter import ttk

from ui.copy_button import CopyButton


class StructuredSectionBuilder:
    """Construit les sections, leurs boutons de copie et suit leurs lignes."""

    SECTION_STYLE = "DetailSection.TLabelframe"

    def __init__(self, content, translator, tooltip_factory_provider, bind_scroll):
        """Initialise le constructeur avec le cadre de contenu et ses fournisseurs."""
        self.content = content
        self.translator = translator
        self._tooltip_factory_provider = tooltip_factory_provider
        self._bind_scroll = bind_scroll
        self.sections = {}
        self.copy_buttons = {}
        self.titles = {}
        self.rows = {}

    def build(self, title):
        """Construit une section et retourne son LabelFrame."""
        section = ttk.LabelFrame(
            self.content,
            text=title,
            padding=(10, 7),
            style=self.SECTION_STYLE,
        )
        section.pack(fill="x", pady=(0, 8))
        section.grid_columnconfigure(0, minsize=140)
        section.grid_columnconfigure(1, weight=1)
        self._bind_scroll(section)
        copy_button = CopyButton(
            section,
            command=lambda target=section: self.copy(target),
            tooltip_factory=self._tooltip_factory_provider(),
            tooltip_text=self.translator.get("ui.copy_section"),
        )
        copy_button.grid(row=0, column=0, columnspan=2, sticky="e", pady=(0, 4))
        self._bind_scroll(copy_button)
        self.sections[title] = section
        self.copy_buttons[section] = copy_button
        self.titles[section] = title
        self.rows[section] = []
        return section

    def copy(self, section):
        """Copie le contenu d'une section dans le presse-papiers."""
        lines = [self.titles[section]]
        for label, value in self.rows[section]:
            lines.append(f"{label}: {value}" if label else value)

        root = section.winfo_toplevel()
        root.clipboard_clear()
        root.clipboard_append("\n".join(lines))
        return True

    def reset(self):
        """Réinitialise les sections et leurs lignes."""
        self.sections.clear()
        self.copy_buttons.clear()
        self.titles.clear()
        self.rows.clear()
