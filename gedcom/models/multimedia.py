"""Modèle paresseux représentant un objet multimédia GEDCOM (record OBJE)."""

from gedcom.continuations import append_continuation
from gedcom.models.lazy_list import _LazyList
from gedcom.models.section_parser import AdditionalLinesMixin
from gedcom.models.tag_values import TagValueCollector


class MultimediaObject(AdditionalLinesMixin):
    """Objet multimédia GEDCOM (record OBJE)."""

    files = _LazyList()
    file_records = _LazyList()
    titles = _LazyList()
    formats = _LazyList()
    notes = _LazyList()
    additional_fields = _LazyList()

    __slots__ = (
        "entity",
        "pointer",
        "file",
        "title",
        "format",
        "note",
        "_files",
        "_file_records",
        "_titles",
        "_formats",
        "_notes",
        "_additional_fields",
    )

    def __init__(self, entity):
        """Initialise l'objet multimédia et analyse ses lignes."""
        self.entity = entity
        self.pointer = entity.pointer

        self.file = None
        self.title = None
        self.format = None
        self.note = None
        self._files = None
        self._file_records = None
        self._titles = None
        self._formats = None
        self._notes = None
        self._additional_fields = None

        self._parse_lines(entity.parsed_lines())

    KNOWN_LEVEL_ONE_TAGS = frozenset({"FILE", "FORM", "TITL", "NOTE"})

    def _parse_lines(self, lines):
        """Analyse les lignes GEDCOM de l'objet multimédia."""
        self._parse_additional_lines(lines)
        values = TagValueCollector(lines, tags=(("NOTE", 1), ("TITL", 1)))
        self._notes = values.values("NOTE", level=1)
        self._titles = values.values("TITL", level=1)
        if self._notes:
            self.note = self._notes[-1]
        if self._titles:
            self.title = self._titles[-1]

    def _assign_level_one(self, tag, value):
        """Affecte un champ de niveau 1 de l'objet multimédia."""
        if tag == "FILE":
            self.file = value
            self.files.append(value)
            self.file_records.append(
                {"file": value, "format": None, "title": None, "details": []}
            )
        elif tag == "FORM":
            self.format = value
            self.formats.append(value)

    def _assign_subsection(self, current_section, level, tag, value):
        """Affecte un champ de sous-section de l'objet multimédia."""
        if current_section != "FILE" or not self.file_records:
            return
        record = self.file_records[-1]
        if level == 2 and tag == "FORM":
            record["format"] = value
            self.format = value
            self.formats.append(value)
        elif level == 2 and tag == "TITL":
            record["title"] = value
        elif level == 2 and tag in {"CONC", "CONT"} and value:
            merged = append_continuation(record["file"] or "", tag, value)
            record["file"] = merged
            self.files[-1] = merged
            self.file = merged
        else:
            record["details"].append((tag, value))
