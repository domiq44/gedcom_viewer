"""Modèle d'une famille (FAM)."""

from gedcom.models.details import new_field
from gedcom.models.event import Event
from gedcom.models.lazy_list import _LazyList
from gedcom.models.tag_values import TagValueCollector

_EVENT_LISTS = {"MARR": "_marriages", "DIV": "_divorces", "EVEN": "_events"}

_FLAG_FIELDS = {
    "ENGA": "engagement",
    "MARB": "marriage_banns",
    "MARC": "marriage_contract",
    "MARL": "marriage_license",
    "MARS": "marriage_settlement",
    "DIVF": "divorce_final",
    "ANUL": "annulment",
}


class Family:
    """
    Représente une famille GEDCOM (FAM) basée sur les lignes parsées de l'entité.
    """

    _KNOWN_LEVEL_ONE_TAGS = frozenset(
        {
            "HUSB",
            "WIFE",
            "CHIL",
            "MARR",
            "DIV",
            "NCHI",
            "ENGA",
            "MARB",
            "MARC",
            "MARL",
            "MARS",
            "DIVF",
            "ANUL",
            "NOTE",
            "SOUR",
            "EVEN",
        }
    )

    children = _LazyList()
    notes = _LazyList()
    sources = _LazyList()
    additional_fields = _LazyList()

    __slots__ = (
        "entity",
        "pointer",
        "husband",
        "wife",
        "_children",
        "marriage_date",
        "marriage_place",
        "divorce_date",
        "divorce_place",
        "number_of_children",
        "engagement",
        "marriage_banns",
        "marriage_license",
        "marriage_contract",
        "marriage_settlement",
        "divorce_final",
        "annulment",
        "_notes",
        "_sources",
        "_events",
        "_additional_fields",
        "_marriages",
        "_divorces",
        "_event_models_loaded",
    )

    def __init__(self, entity):
        """Initialise la famille et analyse ses lignes GEDCOM."""
        self.entity = entity
        self.pointer = entity.pointer

        # Valeurs par défaut
        self.husband = None
        self.wife = None
        self._children = None
        self.marriage_date = None
        self.marriage_place = None
        self.divorce_date = None
        self.divorce_place = None
        self.number_of_children = None
        self.engagement = None
        self.marriage_banns = None
        self.marriage_license = None
        self.marriage_contract = None
        self.marriage_settlement = None
        self.divorce_final = None
        self.annulment = None
        self._notes = None
        self._sources = None
        self._events = None
        self._additional_fields = None
        self._marriages = None
        self._divorces = None
        self._event_models_loaded = False

        # Analyse des lignes brutes
        self._parse_lines(entity.parsed_lines())

    @property
    def marriages(self):
        """Retourne les mariages (chargement paresseux)."""
        return self._get_event_list("_marriages")

    @marriages.setter
    def marriages(self, value):
        """Définit les mariages."""
        self._set_event_list("_marriages", value)

    @property
    def divorces(self):
        """Retourne les divorces (chargement paresseux)."""
        return self._get_event_list("_divorces")

    @divorces.setter
    def divorces(self, value):
        """Définit les divorces."""
        self._set_event_list("_divorces", value)

    @property
    def events(self):
        """Retourne les événements (chargement paresseux)."""
        return self._get_event_list("_events")

    @events.setter
    def events(self, value):
        """Définit les événements."""
        self._set_event_list("_events", value)

    def _get_event_list(self, attribute):
        """Retourne la liste d'événements du type donné."""
        self._load_event_models()
        values = getattr(self, attribute)
        if values is None:
            values = []
            setattr(self, attribute, values)
        return values

    def _set_event_list(self, attribute, values):
        """Définit la liste d'événements du type donné."""
        self._load_event_models()
        setattr(self, attribute, values if values else None)

    def _load_event_models(self):
        """Construit les modèles d'événements depuis les lignes GEDCOM."""
        if self._event_models_loaded:
            return

        self._event_models_loaded = True
        current_event = None

        for level, _pointer, tag, value in self.entity.parsed_lines():

            if level == 1:
                current_event = self._start_event(tag, value)
            elif level is not None and level >= 2 and current_event is not None:
                current_event.add_detail(tag, value)

    def _start_event(self, tag, value):
        """Crée l'événement du tag donné et l'ajoute à sa liste."""
        attribute = _EVENT_LISTS.get(tag)
        if attribute is None:
            return None

        event = Event(tag, value)
        values = getattr(self, attribute)
        if values is None:
            values = []
            setattr(self, attribute, values)
        values.append(event)
        return event

    def _parse_lines(self, lines):
        """Analyse les lignes GEDCOM de la famille."""
        current_additional = None

        for level, _pointer, tag, value in lines:

            if level is None:
                continue

            if level == 1:
                current_additional = self._start_section(tag, value)
            elif level >= 2 and current_additional is not None:
                current_additional["details"].append((tag, value))

        self._apply_continuations(lines)

    TAG_QUERIES = (("NOTE", 1), ("SOUR", 1))
    SUBTAG_QUERIES = (
        ("MARR", "DATE"),
        ("MARR", "PLAC"),
        ("DIV", "DATE"),
        ("DIV", "PLAC"),
    )

    def _apply_continuations(self, lines):
        """Applique les continuations fusionnées aux champs de la famille."""
        values = TagValueCollector(lines, self.TAG_QUERIES, self.SUBTAG_QUERIES)
        self._notes = values.values("NOTE", level=1) or None
        self._sources = values.values("SOUR", level=1) or None
        self.marriage_date = values.subtag("MARR", "DATE")
        self.marriage_place = values.subtag("MARR", "PLAC")
        self.divorce_date = values.subtag("DIV", "DATE")
        self.divorce_place = values.subtag("DIV", "PLAC")

    def _start_section(self, tag, value):
        """Affecte un tag de niveau 1 et retourne le champ additionnel créé."""
        if tag == "HUSB":
            self.husband = value
        elif tag == "WIFE":
            self.wife = value
        elif tag == "CHIL":
            self.children.append(value)
        elif tag == "NCHI":
            self._set_number_of_children(value)
        elif tag in _FLAG_FIELDS:
            setattr(self, _FLAG_FIELDS[tag], value or True)

        if tag in self._KNOWN_LEVEL_ONE_TAGS:
            return None

        additional = new_field(tag, value)
        self.additional_fields.append(additional)
        return additional

    def _set_number_of_children(self, value):
        """Définit le nombre d'enfants, en texte si la valeur n'est pas un entier."""
        try:
            self.number_of_children = int(value)
        except (ValueError, TypeError):
            self.number_of_children = value
