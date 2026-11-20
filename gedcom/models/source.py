"""Modèle d'une source (SOUR)."""

from gedcom.models.details import new_field
from gedcom.models.lazy_list import _LazyList
from gedcom.models.tag_values import (
    TagValueCollector,
    get_subtag_values,
    get_tag_values,
)


class Source:
    """Modèle d'une source GEDCOM (record SOUR)."""

    additional_fields = _LazyList()

    _KNOWN_LEVEL_ONE_TAGS = frozenset(
        {
            "TITL",
            "AUTH",
            "DATE",
            "TEXT",
            "NOTE",
            "REPO",
            "PUBL",
            "ABBR",
            "SOUR",
            "REFN",
            "RIN",
            "DATA",
        }
    )

    __slots__ = (
        "entity",
        "pointer",
        "title",
        "author",
        "pub_date",
        "text",
        "repository",
        "call_number",
        "media",
        "repo_note",
        "publication",
        "abbreviation",
        "_notes",
        "_reference_lists_loaded",
        "_sources",
        "_references",
        "record_id",
        "_data_events",
        "_data_events_loaded",
        "agency",
        "_additional_fields",
    )

    def __init__(self, entity):
        """Initialise la source et charge ses champs."""
        self.entity = entity
        self.pointer = entity.pointer

        self.title = None
        self.author = None
        self.pub_date = None
        self.text = None
        self.repository = None
        self.call_number = None
        self.media = None
        self.repo_note = None
        self.publication = None
        self.abbreviation = None
        self._notes = None
        self._reference_lists_loaded = False
        self._sources = None
        self._references = None
        self.record_id = None
        self._data_events = None
        self._data_events_loaded = False
        self.agency = None
        self._additional_fields = None

        self._parse_lines(entity.parsed_lines())

    @property
    def notes(self):
        """Retourne les notes (chargement paresseux)."""
        self._load_reference_lists()
        if self._notes is None:
            self._notes = []
        return self._notes

    @notes.setter
    def notes(self, value):
        """Définit les notes."""
        self._load_reference_lists()
        self._notes = value if value else None

    @property
    def sources(self):
        """Retourne les sources (chargement paresseux)."""
        self._load_reference_lists()
        if self._sources is None:
            self._sources = []
        return self._sources

    @sources.setter
    def sources(self, value):
        """Définit les sources."""
        self._load_reference_lists()
        self._sources = value if value else None

    @property
    def references(self):
        """Retourne les références (chargement paresseux)."""
        self._load_reference_lists()
        if self._references is None:
            self._references = []
        return self._references

    @references.setter
    def references(self, value):
        """Définit les références."""
        self._load_reference_lists()
        self._references = value if value else None

    def _load_reference_lists(self):
        """Charge paresseusement les listes de références."""
        if self._reference_lists_loaded:
            return

        self._reference_lists_loaded = True
        self._notes = get_tag_values(self.entity, "NOTE", level=1)
        self._notes.extend(get_subtag_values(self.entity, "DATA", "NOTE"))
        self._sources = get_tag_values(self.entity, "SOUR", level=1)
        self._references = get_tag_values(self.entity, "REFN", level=1)

    @property
    def data_events(self):
        """Retourne les événements DATA (chargement paresseux)."""
        self._load_data_events()
        if self._data_events is None:
            self._data_events = []
        return self._data_events

    @data_events.setter
    def data_events(self, value):
        """Définit les événements DATA."""
        self._load_data_events()
        self._data_events = value if value else None

    def _load_data_events(self):
        """Charge paresseusement les événements DATA/EVEN."""
        if self._data_events_loaded:
            return

        self._data_events_loaded = True
        current_section = None
        current_event = None

        for level, _pointer, tag, value in self.entity.parsed_lines():

            if level == 1:
                current_section = tag
                current_event = None
            elif current_section == "DATA":
                if level == 2:
                    if tag == "EVEN":
                        if self._data_events is None:
                            self._data_events = []
                        current_event = {"value": value, "details": []}
                        self._data_events.append(current_event)
                    else:
                        current_event = None
                elif level == 3 and current_event is not None:
                    current_event["details"].append((tag, value))

    def _parse_lines(self, lines):
        """Analyse les lignes GEDCOM de la source."""
        current_section = None
        current_additional = None

        for level, _pointer, tag, value in lines:

            if level is None:
                continue

            # --- Niveau 1 : sections principales ---
            if level == 1:
                current_section = tag
                current_additional = None

                if tag == "REPO":
                    self.repository = value

                elif tag == "ABBR":
                    self.abbreviation = value

                elif tag == "RIN":
                    self.record_id = value

                if tag not in self._KNOWN_LEVEL_ONE_TAGS:
                    current_additional = new_field(tag, value)
                    self.additional_fields.append(current_additional)

            # --- Niveaux 2 et 3 : sous-sections scalaires ---
            elif level >= 2:
                self._assign_subsection_value(current_section, level, tag, value)
                if current_additional is not None:
                    current_additional["details"].append((tag, value))

        self._apply_continuations(lines)

    def _assign_subsection_value(self, current_section, level, tag, value):
        """Affecte les valeurs des sous-sections scalaires de la source."""
        if level == 2 and current_section == "DATA" and tag == "AGNC":
            self.agency = value
        elif level == 2 and current_section == "REPO" and tag == "CALN":
            self.call_number = value
        elif level == 3 and current_section == "REPO" and tag == "MEDI":
            self.media = value

    TAG_QUERIES = (("TITL", 1), ("AUTH", None), ("PUBL", 1), ("DATE", 1), ("TEXT", 1))
    SUBTAG_QUERIES = (("REPO", "NOTE"), ("DATA", "DATE"), ("DATA", "TEXT"))

    def _apply_continuations(self, lines):
        """Applique les continuations fusionnées aux champs scalaires."""
        values = TagValueCollector(lines, self.TAG_QUERIES, self.SUBTAG_QUERIES)
        self.title = self._last_value(values.values("TITL", level=1))
        self.author = self._last_value(values.values("AUTH"))
        self.publication = self._last_value(values.values("PUBL", level=1))
        self.repo_note = self._last_value(values.subtag_values("REPO", "NOTE"))
        self.pub_date = self._last_value(values.values("DATE", level=1))
        self.text = self._last_value(values.values("TEXT", level=1))

        data_date = values.subtag_values("DATA", "DATE")
        if data_date:
            self.pub_date = data_date[-1]

        data_text = values.subtag_values("DATA", "TEXT")
        if data_text:
            self.text = data_text[-1]

    def _last_value(self, values):
        """Retourne la dernière valeur fusionnée, ou None si la liste est vide."""
        return values[-1] if values else None
