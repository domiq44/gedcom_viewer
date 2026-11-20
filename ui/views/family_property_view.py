"""Vue de détail des familles."""

from ui.views.structured_property_view import StructuredPropertyView


class FamilyPropertyView(StructuredPropertyView):
    """Vue de lecture structurée pour une famille GEDCOM."""

    def __init__(
        self,
        parent,
        on_pointer_click,
        translator=None,
        entity_type="FAM",
        tooltip_factory=None,
    ):
        """Initialise la vue des familles."""
        super().__init__(
            parent,
            on_pointer_click,
            translator,
            entity_type,
            title_key="view.family",
            tooltip_factory=tooltip_factory,
        )

    def _event_detail_label(self, event_tag, detail_tag):
        """Retourne le libellé du détail d'événement."""
        keys = {
            ("MARR", "DATE"): "view.marriage_date",
            ("MARR", "PLAC"): "view.marriage_place",
            ("DIV", "DATE"): "view.divorce_date",
            ("DIV", "PLAC"): "view.divorce_place",
            ("MARR", "TEXT"): "view.text",
            ("DIV", "TEXT"): "view.text",
            ("MARR", "EVENTEXT"): "view.event_text",
            ("DIV", "EVENTEXT"): "view.event_text",
            ("MARR", "NOTE"): "view.note",
            ("DIV", "NOTE"): "view.note",
        }
        key = keys.get((event_tag, detail_tag))
        return self.translator.get(key) if key else self._tag_label(detail_tag)

    def _display_family_events(self, section, events, event_tag, item_key):
        """Affiche les événements d'une famille."""
        row = 0
        for index, event in enumerate(events, start=1):
            tag, value, details = self._event_parts(event)
            if tag != event_tag:
                continue

            item_label = self.translator.get(item_key, number=index)
            if value not in (None, ""):
                self._row(section, row, item_label, value)
                row += 1
            else:
                self._row(section, row, item_label, "")
                row += 1

            for detail_tag, detail_value in self._join_text_continuations(details):
                if not detail_tag:
                    continue
                pointer = detail_value if self._is_pointer(detail_value) else None
                self._row(
                    section,
                    row,
                    self._event_detail_label(event_tag, detail_tag),
                    detail_value if detail_value not in (None, "") else "—",
                    pointer=pointer,
                    depth=1,
                )
                row += 1
        return row

    def _render_additional_fields(self, section, fields):
        """Affiche les champs additionnels."""
        row = 0
        for field in fields:
            if isinstance(field, dict):
                tag = field.get("tag", "")
                value = field.get("value")
                details = field.get("details") or []
            else:
                tag, value, details = self._event_parts(field)

            self._row(
                section,
                row,
                self._tag_label(tag) if tag else "",
                value if value not in (None, "") else "—",
                pointer=value if self._is_pointer(value) else None,
            )
            row += 1

            for detail in details:
                if isinstance(detail, tuple) and len(detail) == 2:
                    detail_tag, detail_value = detail
                else:
                    detail_tag, detail_value, _children = self._event_parts(detail)
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

    def display(self, family):
        """Affiche une famille."""
        self._clear()
        self.title_label.configure(text=self.translator.get("view.family"))
        if family is None:
            return

        self._display_title(family)
        self._display_identity(family)
        self._display_members(family)
        self._display_children(family)
        self._display_overview(family)
        self._display_marriages(family)
        self._display_divorces(family)
        self._display_events(family)
        self._display_lists(family)
        self._display_additional(family)

    def _display_title(self, family):
        """Affiche les noms des conjoints dans le titre."""
        husband = getattr(family, "husband", None)
        wife = getattr(family, "wife", None)
        member_names = [
            self._display_pointer(pointer) for pointer in (husband, wife) if pointer
        ]
        self.title_label.configure(
            text=" & ".join(member_names) or self.translator.get("view.family")
        )

    def _display_members(self, family):
        """Affiche les conjoints de la famille."""
        rows = [
            (self.translator.get(key), pointer)
            for key, pointer in (
                ("view.husband", getattr(family, "husband", None)),
                ("view.wife", getattr(family, "wife", None)),
            )
            if pointer
        ]
        if not rows:
            return
        section = self._section(self.translator.get("view.family_members"))
        for row, (label, pointer) in enumerate(rows):
            self._row(section, row, label, pointer, pointer=pointer)

    def _display_children(self, family):
        """Affiche les enfants de la famille."""
        children = getattr(family, "children", None) or []
        if not children:
            return
        section = self._section(self.translator.get("view.children"))
        for index, pointer in enumerate(children, start=1):
            self._row(
                section,
                index - 1,
                self.translator.get("view.child_number", number=index),
                pointer,
                pointer=pointer if self._is_pointer(pointer) else None,
            )

    def _display_overview(self, family):
        """Affiche la vue d'ensemble de la famille."""
        fields = self._overview_fields(family)
        if not fields:
            return
        section = self._section(self.translator.get("view.family"))
        for row, (label, value) in enumerate(fields):
            self._row(section, row, label, value)

    def _overview_fields(self, family):
        """Retourne les couples libellé/valeur de la vue d'ensemble."""
        children = getattr(family, "children", None) or []
        children_count = getattr(family, "number_of_children", None)
        if children_count is None and children:
            children_count = len(children)

        fields = []
        for key, value in (
            ("view.children_count", children_count),
            ("view.engagement", getattr(family, "engagement", None)),
            ("view.marriage_banns", getattr(family, "marriage_banns", None)),
            ("view.marriage_contract", getattr(family, "marriage_contract", None)),
            ("view.marriage_license", getattr(family, "marriage_license", None)),
            ("view.marriage_settlement", getattr(family, "marriage_settlement", None)),
            ("view.divorce_final", getattr(family, "divorce_final", None)),
            ("view.annulment", getattr(family, "annulment", None)),
        ):
            if value is None or value == "":
                continue
            if isinstance(value, bool):
                value = self.translator.get("common.yes" if value else "common.no")
            fields.append((self.translator.get(key), value))

        marriages = list(getattr(family, "marriages", None) or [])
        divorces = list(getattr(family, "divorces", None) or [])
        if not marriages:
            fields.extend(
                self._fallback_fields(
                    family,
                    (
                        ("view.marriage_date", "marriage_date"),
                        ("view.marriage_place", "marriage_place"),
                    ),
                )
            )
        if not divorces:
            fields.extend(
                self._fallback_fields(
                    family,
                    (
                        ("view.divorce_date", "divorce_date"),
                        ("view.divorce_place", "divorce_place"),
                    ),
                )
            )
        return fields

    def _fallback_fields(self, family, fields):
        """Retourne les champs de repli présents."""
        present = []
        for key, attribute in fields:
            value = getattr(family, attribute, None)
            if value not in (None, ""):
                present.append((self.translator.get(key), value))
        return present

    def _display_marriages(self, family):
        """Affiche les mariages de la famille."""
        marriages = list(getattr(family, "marriages", None) or [])
        if not marriages:
            return
        section = self._section(self.translator.get("view.marriages"))
        self._display_family_events(section, marriages, "MARR", "view.marriage_number")

    def _display_divorces(self, family):
        """Affiche les divorces de la famille."""
        divorces = list(getattr(family, "divorces", None) or [])
        if not divorces:
            return
        section = self._section(self.translator.get("view.divorces"))
        self._display_family_events(section, divorces, "DIV", "view.divorce_number")

    def _display_events(self, family):
        """Affiche les événements de la famille."""
        events = getattr(family, "events", None) or []
        if not events:
            return
        section = self._section(self.translator.get("view.events"))
        row = 0
        for event in events:
            row = self._render_event(section, row, event)

    def _display_lists(self, family):
        """Affiche les notes et les sources de la famille."""
        for attribute, title_key in (
            ("notes", "view.notes"),
            ("sources", "view.sources"),
        ):
            values = getattr(family, attribute, None) or []
            if not values:
                continue
            section = self._section(self.translator.get(title_key))
            for row, value in enumerate(values):
                pointer = value if self._is_pointer(value) else None
                self._row(section, row, "", value, pointer=pointer)

    def _display_additional(self, family):
        """Affiche les champs GEDCOM additionnels."""
        additional_fields = getattr(family, "additional_fields", None) or []
        if not additional_fields:
            return
        section = self._section(self.translator.get("view.additional_fields"))
        self._render_additional_fields(section, additional_fields)
