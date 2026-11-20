"""Modèle d'un dépôt d'archives (REPO)."""

from gedcom.models.lazy_list import _LazyList
from gedcom.models.section_parser import AdditionalLinesMixin
from gedcom.models.tag_values import TagValueCollector


class Repository(AdditionalLinesMixin):
    """Modèle d'un dépôt d'archives (REPO)."""

    notes = _LazyList()
    references = _LazyList()
    phones = _LazyList()
    emails = _LazyList()
    faxes = _LazyList()
    websites = _LazyList()
    additional_fields = _LazyList()

    __slots__ = (
        "entity",
        "pointer",
        "name",
        "address",
        "city",
        "state",
        "postal_code",
        "country",
        "address_line_1",
        "address_line_2",
        "phone",
        "email",
        "fax",
        "website",
        "_notes",
        "_references",
        "_phones",
        "_emails",
        "_faxes",
        "_websites",
        "record_id",
        "change_date",
        "change_time",
        "_additional_fields",
    )

    def __init__(self, entity):
        """Initialise le dépôt et analyse ses lignes."""
        self.entity = entity
        self.pointer = entity.pointer

        self.name = None
        self.address = None
        self.city = None
        self.state = None
        self.postal_code = None
        self.country = None
        self.address_line_1 = None
        self.address_line_2 = None
        self.phone = None
        self.email = None
        self.fax = None
        self.website = None
        self._notes = None
        self._references = None
        self._phones = None
        self._emails = None
        self._faxes = None
        self._websites = None
        self.record_id = None
        self.change_date = None
        self.change_time = None
        self._additional_fields = None

        self._parse_lines(entity.parsed_lines())

    KNOWN_LEVEL_ONE_TAGS = frozenset(
        {
            "NAME",
            "ADDR",
            "NOTE",
            "REFN",
            "PHON",
            "EMAIL",
            "FAX",
            "WWW",
            "RIN",
            "CHAN",
        }
    )

    def _parse_lines(self, lines):
        """Analyse les lignes GEDCOM du dépôt."""
        self._parse_additional_lines(lines)
        self._apply_continuations(lines)

    def _assign_level_one(self, tag, value):
        """Affecte un champ de niveau 1 du dépôt."""
        if tag == "NAME":
            self.name = value
        elif tag == "ADDR":
            self.address = value
        elif tag == "PHON":
            self.phone = value
        elif tag == "EMAIL":
            self.email = value
        elif tag == "FAX":
            self.fax = value
        elif tag == "WWW":
            self.website = value
        elif tag == "RIN":
            self.record_id = value

    def _assign_subsection(self, current_section, level, tag, value):
        """Affecte un champ de sous-section du dépôt."""
        if current_section == "ADDR" and level == 2:
            self._assign_address_field(tag, value)
        elif current_section == "CHAN" and level >= 2:
            if tag == "DATE":
                self.change_date = value
            elif tag == "TIME":
                self.change_time = value

    def _assign_address_field(self, tag, value):
        """Affecte un champ de la section ADDR."""
        if tag == "CITY":
            self.city = value
        elif tag == "ADR1":
            self.address_line_1 = value
        elif tag == "ADR2":
            self.address_line_2 = value
        elif tag == "STAE":
            self.state = value
        elif tag == "POST":
            self.postal_code = value
        elif tag == "CTRY":
            self.country = value

    LIST_TAGS = (
        ("_notes", "NOTE"),
        ("_references", "REFN"),
        ("_phones", "PHON"),
        ("_emails", "EMAIL"),
        ("_faxes", "FAX"),
        ("_websites", "WWW"),
    )
    SCALAR_TAGS = (("name", "NAME"), ("address", "ADDR"))
    ADDRESS_FIELDS = (
        ("city", "CITY"),
        ("address_line_1", "ADR1"),
        ("address_line_2", "ADR2"),
        ("state", "STAE"),
        ("postal_code", "POST"),
        ("country", "CTRY"),
    )
    SUBTAG_QUERIES = tuple(("ADDR", tag) for _, tag in ADDRESS_FIELDS)

    def _apply_continuations(self, lines):
        """Applique les continuations fusionnées aux champs du dépôt."""
        tags = tuple((tag, 1) for _, tag in self.LIST_TAGS + self.SCALAR_TAGS)
        values = TagValueCollector(lines, tags, self.SUBTAG_QUERIES)

        for attribute, tag in self.LIST_TAGS:
            collected = values.values(tag, level=1)
            if collected:
                setattr(self, attribute, collected)

        for attribute, tag in self.SCALAR_TAGS:
            collected = values.values(tag, level=1)
            if collected:
                setattr(self, attribute, collected[-1])

        for attribute, tag in self.ADDRESS_FIELDS:
            collected = values.subtag_values("ADDR", tag)
            if collected:
                setattr(self, attribute, collected[-1])
