"""Modèle d'une note (NOTE)."""

from gedcom.models.lazy_list import _LazyList
from gedcom.models.section_parser import AdditionalLinesMixin
from gedcom.models.tag_values import TagValueCollector


class Note(AdditionalLinesMixin):
    """Modèle d'une note GEDCOM (record NOTE)."""

    sources = _LazyList()
    references = _LazyList()
    submitters = _LazyList()
    additional_fields = _LazyList()

    __slots__ = (
        "entity",
        "pointer",
        "text",
        "source",
        "_sources",
        "_references",
        "record_id",
        "_submitters",
        "change_date",
        "change_time",
        "_additional_fields",
    )

    def __init__(self, entity):
        """Initialise la note et analyse ses lignes."""
        self.entity = entity
        self.pointer = entity.pointer

        self.text = ""
        self.source = None
        self._sources = None
        self._references = None
        self.record_id = None
        self._submitters = None
        self.change_date = None
        self.change_time = None
        self._additional_fields = None

        self._parse_lines(entity.parsed_lines())

    KNOWN_LEVEL_ONE_TAGS = frozenset(
        {"SOUR", "REFN", "RIN", "SUBM", "CHAN", "NOTE", "CONT", "CONC"}
    )

    def _parse_lines(self, lines):
        """Analyse les lignes GEDCOM de la note."""
        self._parse_additional_lines(lines)
        values = TagValueCollector(lines, tags=(("NOTE", None),))
        self.text = "\n".join(values.values("NOTE")).strip("\n")

    def _assign_level_one(self, tag, value):
        """Affecte un champ de niveau 1 de la note."""
        if tag == "SOUR":
            self.source = value
            self.sources.append(value)
        elif tag == "REFN":
            self.references.append(value)
        elif tag == "RIN":
            self.record_id = value
        elif tag == "SUBM":
            self.submitters.append(value)

    def _assign_subsection(self, current_section, level, tag, value):
        """Affecte un champ de sous-section de la note."""
        if current_section != "CHAN" or level < 2:
            return
        if tag == "DATE":
            self.change_date = value
        elif tag == "TIME":
            self.change_time = value
