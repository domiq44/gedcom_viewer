"""Vue de détail des citations."""

from ui.views.structured_property_view import StructuredPropertyView


class CitationPropertyView(StructuredPropertyView):
    """Vue de lecture structurée pour une occurrence de citation GEDCOM."""

    def __init__(
        self,
        parent,
        on_pointer_click,
        translator=None,
        entity_type="CITE",
        tooltip_factory=None,
    ):
        """Initialise la vue des citations."""
        super().__init__(
            parent,
            on_pointer_click,
            translator,
            entity_type,
            title_key="view.citation",
            tooltip_factory=tooltip_factory,
        )

    def _detail_label(self, tag_path):
        """Retourne le libellé du détail de citation."""
        return " / ".join(self._tag_label(tag) for tag in tag_path.split("/"))

    def _localized_owner_type(self, owner_type):
        """Retourne le type de propriétaire localisé."""
        if not owner_type:
            return "—"
        key = f"entity.{owner_type}"
        translated = self.translator.get(key)
        return translated if translated != key else owner_type

    def display(self, citation):
        """Affiche une citation."""
        self._clear()
        self.title_label.configure(text=self.translator.get("view.citation"))
        if citation is None:
            return

        self._display_title(citation)
        self._display_identity(citation)
        self._display_information(citation)
        self._display_details(citation)

    def _display_title(self, citation):
        """Affiche le titre de la citation."""
        source_pointer = getattr(citation, "source_pointer", "") or ""
        owner_pointer = getattr(citation, "owner_pointer", "") or ""
        source_name = self._display_pointer(source_pointer) if source_pointer else "—"
        owner_name = self._display_pointer(owner_pointer) if owner_pointer else "—"
        self.title_label.configure(
            text=self.translator.get(
                "view.citation_pointer",
                source=source_name,
                owner=owner_name,
            )
        )

    def _display_identity(self, citation):
        """Affiche les pointeurs de la citation."""
        owner_pointer = getattr(citation, "owner_pointer", "") or ""
        source_pointer = getattr(citation, "source_pointer", "") or ""
        self._display_pointer_label(f"{owner_pointer} · {source_pointer}".strip(" ·"))

    def _display_information(self, citation):
        """Affiche la section d'information de la citation."""
        rows = self._information_rows(citation)
        if not rows:
            return
        section = self._section(self.translator.get("view.citation_information"))
        for row, (label, value, pointer) in enumerate(rows):
            self._row(section, row, label, value, pointer=pointer)

    def _information_rows(self, citation):
        """Retourne les lignes d'information de la citation."""
        rows = []
        source_pointer = getattr(citation, "source_pointer", "") or ""
        owner_pointer = getattr(citation, "owner_pointer", "") or ""
        if source_pointer:
            rows.append(
                (self.translator.get("view.source"), source_pointer, source_pointer)
            )
        if owner_pointer:
            rows.append(
                (
                    self.translator.get("view.citation_owner"),
                    owner_pointer,
                    owner_pointer,
                )
            )
        owner_type = getattr(citation, "owner_type", None)
        if owner_type:
            rows.append(
                (
                    self.translator.get("view.citation_owner_type"),
                    self._localized_owner_type(owner_type),
                    None,
                )
            )
        context = getattr(citation, "context_tag", None)
        if context:
            rows.append(
                (
                    self.translator.get("view.citation_context"),
                    self._tag_label(context),
                    None,
                )
            )
        level = getattr(citation, "level", None)
        if level is not None:
            rows.append((self.translator.get("view.citation_level"), level, None))
        page = getattr(citation, "page", None)
        if page:
            rows.append((self.translator.get("view.page"), page, None))
        return rows

    def _display_details(self, citation):
        """Affiche les détails de la citation."""
        pairs = self._detail_pairs(citation)
        if not pairs:
            return
        section = self._section(self.translator.get("view.citation_details"))
        for row, (tag, value) in enumerate(pairs):
            pointer = value if self._is_pointer(value) else None
            self._row(
                section,
                row,
                self._detail_label(tag) if tag else "",
                value if value not in (None, "") else "—",
                pointer=pointer,
            )

    def _detail_pairs(self, citation):
        """Retourne les couples tag/valeur des détails de la citation."""
        details = list(getattr(citation, "details", None) or [])
        page = getattr(citation, "page", None)
        if page:
            details = [
                detail
                for detail in details
                if not (isinstance(detail, dict) and detail.get("tag") == "PAGE")
            ]
        pairs = []
        for detail in details:
            if isinstance(detail, dict):
                pairs.append((detail.get("tag", ""), detail.get("value", "")))
            elif isinstance(detail, tuple) and len(detail) >= 2:
                pairs.append((detail[0], detail[1]))
            else:
                tag, value, _children = self._event_parts(detail)
                pairs.append((tag, value))
        return pairs
