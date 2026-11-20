"""Vue de détail des notes."""

from ui.views.structured_property_view import StructuredPropertyView


class NotePropertyView(StructuredPropertyView):
    """Vue de lecture structurée pour une note GEDCOM."""

    def __init__(
        self,
        parent,
        on_pointer_click,
        translator=None,
        entity_type="NOTE",
        tooltip_factory=None,
    ):
        """Initialise la vue des notes."""
        super().__init__(
            parent,
            on_pointer_click,
            translator,
            entity_type,
            title_key="view.note",
            tooltip_factory=tooltip_factory,
        )
        self.text_widget = None

    def display(self, note):
        """Affiche une note."""
        self._clear()
        self.text_widget = None
        self.title_label.configure(text=self.translator.get("view.note"))
        if note is None:
            return

        self._display_identity(note)
        self._display_text(note)
        self._display_labelled_section("view.note_details", self._detail_fields(note))
        self._display_sources(note)
        self._display_pointer_lists(
            note,
            (
                ("references", "view.references"),
                ("submitters", "view.submitters"),
            ),
        )
        self._display_additional_fields(note)

    def _display_text(self, note):
        """Affiche le texte de la note."""
        text = getattr(note, "text", None)
        if text not in (None, ""):
            section = self._section(self.translator.get("view.note"))
            self._row(section, 0, self.translator.get("view.text"), text)
            self.text_widget = self.value_widgets[-1]

    def _detail_fields(self, note):
        """Retourne les champs de détail de la note."""
        return (
            ("view.internal_id", getattr(note, "record_id", None)),
            ("view.change_date", getattr(note, "change_date", None)),
            ("view.change_time", getattr(note, "change_time", None)),
        )

    def _display_sources(self, note):
        """Affiche les sources de la note."""
        sources = list(getattr(note, "sources", None) or [])
        source = getattr(note, "source", None)
        if source and source not in sources:
            sources.insert(0, source)
        if not sources:
            return
        section = self._section(self.translator.get("view.sources"))
        for row, value in enumerate(sources):
            pointer = value if self._is_pointer(value) else None
            self._row(section, row, "", value, pointer=pointer)
