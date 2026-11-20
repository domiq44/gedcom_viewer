"""Vue de détail des sources."""

from ui.views.structured_property_view import StructuredPropertyView


class SourcePropertyView(StructuredPropertyView):
    """Vue de lecture structurée pour une source GEDCOM."""

    def __init__(
        self,
        parent,
        on_pointer_click,
        translator=None,
        entity_type="SOUR",
        tooltip_factory=None,
    ):
        """Initialise la vue des sources."""
        super().__init__(
            parent,
            on_pointer_click,
            translator,
            entity_type,
            title_key="view.source",
            tooltip_factory=tooltip_factory,
        )

    def _display_data_events(self, section, events):
        """Affiche les événements de données d'une source."""
        row = 0
        for index, event in enumerate(events, start=1):
            _tag, value, details = self._event_parts(event)
            self._row(
                section,
                row,
                self.translator.get("view.data_event_number", number=index),
                value if value not in (None, "") else "—",
            )
            row += 1

            for detail_tag, detail_value in self._join_text_continuations(details):
                if not detail_tag:
                    continue
                pointer = detail_value if self._is_pointer(detail_value) else None
                self._row(
                    section,
                    row,
                    self._tag_label(detail_tag, detail_value),
                    detail_value if detail_value not in (None, "") else "—",
                    pointer=pointer,
                    depth=1,
                )
                row += 1

    def display(self, source):
        """Affiche une source."""
        self._clear()
        self.title_label.configure(text=self.translator.get("view.source"))
        if source is None:
            return

        self._display_title(source)
        self._display_identity(source)
        self._display_labelled_section(
            "view.source_bibliography", self._bibliography_fields(source)
        )
        self._display_repository(source)
        self._display_text(source)
        self._display_data_event_section(source)
        self._display_lists(source)
        self._display_additional_fields(source)

    def _display_title(self, source):
        """Affiche le titre de la source."""
        title = getattr(source, "title", None) or getattr(source, "abbreviation", None)
        self.title_label.configure(text=title or self.translator.get("view.source"))

    def _bibliography_fields(self, source):
        """Retourne les champs bibliographiques de la source."""
        return (
            ("view.author", getattr(source, "author", None)),
            ("view.publication_date", getattr(source, "pub_date", None)),
            ("view.publication", getattr(source, "publication", None)),
            ("view.abbreviation", getattr(source, "abbreviation", None)),
            ("view.agency", getattr(source, "agency", None)),
            ("view.internal_id", getattr(source, "record_id", None)),
        )

    def _display_repository(self, source):
        """Affiche le dépôt de la source."""
        rows = self._repository_rows(source)
        if not rows:
            return
        section = self._section(self.translator.get("view.source_repository"))
        for row, (label, value, pointer) in enumerate(rows):
            self._row(section, row, label, value, pointer=pointer)

    def _repository_rows(self, source):
        """Retourne les lignes du dépôt de la source."""
        rows = []
        repository = getattr(source, "repository", None)
        if repository:
            rows.append(
                (self.translator.get("view.repository"), repository, repository)
            )
        for key, attribute in (
            ("view.call_number", "call_number"),
            ("view.media", "media"),
            ("view.repository_note", "repo_note"),
        ):
            value = getattr(source, attribute, None)
            if value not in (None, ""):
                rows.append((self.translator.get(key), value, None))
        return rows

    def _display_text(self, source):
        """Affiche le texte de la source."""
        text = getattr(source, "text", None)
        if text:
            section = self._section(self.translator.get("view.source_content"))
            self._row(section, 0, self.translator.get("view.text"), text)

    def _display_data_event_section(self, source):
        """Affiche la section des événements de données."""
        data_events = getattr(source, "data_events", None) or []
        if not data_events:
            return
        section = self._section(self.translator.get("view.data_events"))
        self._display_data_events(section, data_events)

    def _display_lists(self, source):
        """Affiche les notes, liens de source et références."""
        for attribute, title_key in (
            ("notes", "view.notes"),
            ("sources", "view.source_links"),
            ("references", "view.references"),
        ):
            values = getattr(source, attribute, None) or []
            if not values:
                continue
            section = self._section(self.translator.get(title_key))
            for row, value in enumerate(values):
                pointer = (
                    value
                    if attribute == "sources" and self._is_pointer(value)
                    else None
                )
                self._row(section, row, "", value, pointer=pointer)
