"""Vue de détail des individus."""

from ui.views.structured_property_view import StructuredPropertyView


class IndividualPropertyView(StructuredPropertyView):
    """Vue de lecture structurée pour une personne GEDCOM."""

    def __init__(
        self,
        parent,
        on_pointer_click,
        translator=None,
        entity_type="INDI",
        tooltip_factory=None,
    ):
        """Initialise la vue des individus."""
        super().__init__(
            parent,
            on_pointer_click,
            translator,
            entity_type,
            title_key="view.individual",
            tooltip_factory=tooltip_factory,
        )

    def display(self, entity):
        """Affiche un individu."""
        self._clear()
        self.title_label.configure(text=self.translator.get("view.individual"))
        if entity is None:
            return

        self._display_title(entity)
        self._display_identity(entity)
        self._display_overview(entity)
        self._display_family_links(entity)
        self._display_events(entity)
        self._display_lists(entity)
        self._display_media(entity)

    def _display_title(self, entity):
        """Affiche le nom de l'individu dans le titre."""
        self.title_label.configure(text=self._entity_name(entity))

    def _entity_name(self, entity):
        """Retourne le nom affichable de l'individu."""
        if callable(self.display_name_resolver):
            return self.display_name_resolver(entity, "INDI")
        name = " ".join(
            str(getattr(entity, "name", None) or "").replace("/", " ").split()
        )
        return name or self.translator.get("view.individual")

    def _display_overview(self, entity):
        """Affiche la vue d'ensemble de l'individu."""
        fields = [
            (self.translator.get(key), value)
            for key, value in self._overview_fields(entity)
            if value is not None and value != ""
        ]
        if not fields:
            return
        section = self._section(self.translator.get("view.individual_overview"))
        for row, (label, value) in enumerate(fields):
            self._row(section, row, label, value)

    def _overview_fields(self, entity):
        """Retourne les couples libellé/valeur de la vue d'ensemble."""
        return (
            ("view.birth_date", getattr(entity, "birth_date", None)),
            ("view.birth_place", getattr(entity, "birth_place", None)),
            ("view.baptism_date", getattr(entity, "baptism_date", None)),
            ("view.baptism_place", getattr(entity, "baptism_place", None)),
            ("view.death_date", getattr(entity, "death_date", None)),
            ("view.death_place", getattr(entity, "death_place", None)),
            ("view.sex", getattr(entity, "sex", None)),
            ("view.nickname", getattr(entity, "nickname", None)),
            ("view.age_at_death", getattr(entity, "age_at_death", None)),
            (
                "view.death_confirmed",
                self.translator.get(
                    "common.yes"
                    if getattr(entity, "death_confirmed", False)
                    else "common.no"
                ),
            ),
            ("view.marriage_count", getattr(entity, "marriage_count", None)),
        )

    def _display_family_links(self, entity):
        """Affiche les liens familiaux de l'individu."""
        links = self._family_links(entity)
        if not links:
            return
        section = self._section(self.translator.get("view.individual_family_links"))
        row = 0
        for label, pointer, details in links:
            self._row(section, row, label, pointer, pointer=pointer)
            row += 1
            for detail_tag, detail_value in details:
                self._row(
                    section,
                    row,
                    self._tag_label(detail_tag, detail_value),
                    detail_value if detail_value not in (None, "") else "—",
                    depth=1,
                )
                row += 1

    def _family_links(self, entity):
        """Retourne les liens familiaux à afficher."""
        links: list[tuple[str, str, list]] = []
        parent_family_links = getattr(entity, "famc_links", None)
        if not isinstance(parent_family_links, (list, tuple)):
            parent_family_links = []
        parent_family = getattr(entity, "famc", None)
        if parent_family_links:
            links.extend(
                (
                    self.translator.get("view.child_family"),
                    link.get("pointer"),
                    link.get("details") or [],
                )
                for link in parent_family_links
                if link.get("pointer")
            )
        elif parent_family:
            links.append((self.translator.get("view.child_family"), parent_family, []))
        links.extend(
            (self.translator.get("view.family_parent_families"), pointer, [])
            for pointer in getattr(entity, "fams", None) or []
            if pointer
        )
        return links

    def _display_events(self, entity):
        """Affiche les événements de l'individu."""
        events = self._visible_events(entity)
        if not events:
            return
        section = self._section(self.translator.get("view.events"))
        row = 0
        for event in events:
            row = self._render_event(section, row, event)

    def _visible_events(self, entity):
        """Retourne les événements à afficher."""
        visible = []
        for event in getattr(entity, "events", None) or []:
            tag, _value, children = self._event_parts(event)
            if tag in {"SEX", "NICK"}:
                continue
            if tag in {"BIRT", "DEAT", "CHR"} and not self._has_extra_event_details(
                children
            ):
                continue
            visible.append(event)
        return visible

    def _display_lists(self, entity):
        """Affiche les occupations, propriétés, notes et textes."""
        for attribute, title_key in (
            ("occupations", "view.occupations"),
            ("properties", "view.properties"),
            ("notes", "view.notes"),
            ("texts", "view.texts"),
        ):
            values = getattr(entity, attribute, None) or []
            if not values:
                continue
            section = self._section(self.translator.get(title_key))
            for row, value in enumerate(values):
                self._row(section, row, "", self._list_value_text(value))

    def _list_value_text(self, value):
        """Retourne le texte affichable d'une valeur de liste."""
        if not isinstance(value, dict):
            return str(value)
        text = value.get("occupation") or value.get("value") or "—"
        date = value.get("date")
        if date:
            return f"{text} · {date}"
        return text

    def _display_media(self, entity):
        """Affiche la galerie multimédia."""
        media = getattr(entity, "obje", None) or []
        if not media:
            return
        section = self._section(self.translator.get("view.gallery"))
        for row, pointer in enumerate(media):
            if pointer:
                self._row(section, row, "", pointer, pointer=pointer)

    def _has_extra_event_details(self, children):
        """Indique si des détails d'événement sont présents."""
        for child in children:
            tag, _value, descendants = self._event_parts(child)
            if tag not in {"DATE", "PLAC"}:
                return True
            if self._has_extra_event_details(descendants):
                return True
        return False
