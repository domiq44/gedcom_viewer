"""Modèle d'un soumetteur (SUBM)."""

from gedcom.models.lazy_list import _LazyList
from gedcom.models.section_parser import AdditionalLinesMixin
from gedcom.models.tag_values import TagValueCollector


class Submitter(AdditionalLinesMixin):
    """Modèle d'un soumetteur GEDCOM (record SUBM)."""

    phones = _LazyList()
    emails = _LazyList()
    faxes = _LazyList()
    websites = _LazyList()
    languages = _LazyList()
    additional_fields = _LazyList()

    __slots__ = (
        "entity",
        "pointer",
        "name",
        "address",
        "address_line_1",
        "address_line_2",
        "city",
        "state",
        "postal_code",
        "country",
        "phone",
        "email",
        "fax",
        "website",
        "language",
        "registered_number",
        "record_id",
        "restriction",
        "change_date",
        "change_time",
        "_phones",
        "_emails",
        "_faxes",
        "_websites",
        "_languages",
        "_additional_fields",
    )

    def __init__(self, entity):
        """Initialise le soumetteur et analyse ses lignes."""
        self.entity = entity
        self.pointer = entity.pointer

        self.name = None
        self.address = None
        self.address_line_1 = None
        self.address_line_2 = None
        self.city = None
        self.state = None
        self.postal_code = None
        self.country = None
        self.phone = None
        self.email = None
        self.fax = None
        self.website = None
        self.language = None
        self.registered_number = None
        self.record_id = None
        self.restriction = None
        self.change_date = None
        self.change_time = None
        self._phones = None
        self._emails = None
        self._faxes = None
        self._websites = None
        self._languages = None
        self._additional_fields = None

        self._parse_lines(entity.parsed_lines())

    KNOWN_LEVEL_ONE_TAGS = frozenset(
        {
            "NAME",
            "ADDR",
            "PHON",
            "EMAIL",
            "FAX",
            "WWW",
            "LANG",
            "RFN",
            "RIN",
            "RESN",
            "CHAN",
        }
    )

    ADDRESS_FIELDS = {
        "ADR1": "address_line_1",
        "ADR2": "address_line_2",
        "CITY": "city",
        "STAE": "state",
        "POST": "postal_code",
        "CTRY": "country",
    }

    def _parse_lines(self, lines):
        """Analyse les lignes GEDCOM du soumetteur."""
        current_section = None
        current_additional = None
        current_level = None

        for level, _pointer, tag, value in lines:
            if level is None:
                continue

            if level == 1:
                current_section = tag
                current_additional = self._start_section(tag, value)
                current_level = level if current_additional else None
                continue

            current_section, current_additional, current_level = (
                self._parse_submitter_subsection(
                    current_section,
                    current_additional,
                    current_level,
                    level,
                    tag,
                    value,
                )
            )

        self._apply_continuations(lines)

    def _parse_submitter_subsection(
        self, section, additional, additional_level, level, tag, value
    ):
        """Analyse une sous-section du soumetteur."""
        if (
            additional is not None
            and additional_level is not None
            and level > additional_level
        ):
            additional["details"].append((tag, value))
            return section, additional, additional_level

        if section == "ADDR":
            return (section,) + self._parse_address_subsection(level, tag, value)
        if section == "NAME":
            return (section,) + self._new_prefixed_field("NAME", level, tag, value)
        if section == "CHAN":
            return (section,) + self._parse_chan_subsection(level, tag, value)
        return (section,) + self._new_prefixed_field(section, level, tag, value)

    def _parse_address_subsection(self, level, tag, value):
        """Analyse un champ de la section ADDR."""
        attribute = self.ADDRESS_FIELDS.get(tag)
        if attribute:
            setattr(self, attribute, value)
            return None, None
        return self._new_prefixed_field("ADDR", level, tag, value)

    def _parse_chan_subsection(self, level, tag, value):
        """Analyse un champ de la section CHAN."""
        if tag == "DATE":
            self.change_date = value
            return None, None
        if tag == "TIME":
            self.change_time = value
            return None, None
        return self._new_prefixed_field("CHAN", level, tag, value)

    def _new_prefixed_field(self, prefix, level, tag, value):
        """Crée un champ additionnel préfixé et retourne le champ et son niveau."""
        field = self._new_additional_field(f"{prefix}/{tag}", value)
        return field, level

    LEVEL_ONE_FIELDS = {
        "NAME": "name",
        "ADDR": "address",
        "PHON": "phone",
        "EMAIL": "email",
        "FAX": "fax",
        "WWW": "website",
        "LANG": "language",
        "RFN": "registered_number",
        "RIN": "record_id",
        "RESN": "restriction",
    }

    def _assign_level_one(self, tag, value):
        """Affecte un champ de niveau 1 du soumetteur."""
        attribute = self.LEVEL_ONE_FIELDS.get(tag)
        if attribute is not None:
            setattr(self, attribute, value)

    LIST_TAGS = (
        ("_phones", "PHON"),
        ("_emails", "EMAIL"),
        ("_faxes", "FAX"),
        ("_websites", "WWW"),
        ("_languages", "LANG"),
    )
    SCALAR_TAGS = (("name", "NAME"), ("address", "ADDR"))
    ADDRESS_CONTINUATION_FIELDS = (
        ("address_line_1", "ADR1"),
        ("address_line_2", "ADR2"),
        ("city", "CITY"),
        ("state", "STAE"),
        ("postal_code", "POST"),
        ("country", "CTRY"),
    )
    SUBTAG_QUERIES = tuple(("ADDR", tag) for _, tag in ADDRESS_CONTINUATION_FIELDS)

    def _apply_continuations(self, lines):
        """Applique les continuations fusionnées aux champs du soumetteur."""
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

        for attribute, tag in self.ADDRESS_CONTINUATION_FIELDS:
            collected = values.subtag_values("ADDR", tag)
            if collected:
                setattr(self, attribute, collected[-1])
