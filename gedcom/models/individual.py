"""Modèle d'un individu (INDI)."""

from gedcom.continuations import CONTINUATION_TAGS, append_continuation
from gedcom.models.lazy_list import _LazyList
from gedcom.models.tag_values import (
    TagValueCollector,
    get_subtag_values,
    get_tag_values,
)


class Individual:
    """Modèle d'un individu (INDI) et de ses relations."""

    famc_links = _LazyList()

    __slots__ = (
        "entity",
        "pointer",
        "name",
        "_names",
        "sex",
        "birth_date",
        "birth_place",
        "death_date",
        "death_place",
        "death_confirmed",
        "age_at_death",
        "nickname",
        "_occupations",
        "_occupations_loaded",
        "_notes",
        "_notes_loaded",
        "_text_tags_loaded",
        "baptism_date",
        "baptism_place",
        "marriage_count",
        "_properties",
        "_properties_loaded",
        "_texts",
        "_obje",
        "_obje_loaded",
        "_famc_links",
        "_fams",
        "_fams_loaded",
        "_events",
    )

    def __init__(self, entity):
        """Initialise l'individu et charge ses champs principaux."""
        self.entity = entity
        self.pointer = entity.pointer

        self.name = None
        self._names = None
        self.sex = None
        self.birth_date = None
        self.birth_place = None
        self.death_date = None
        self.death_place = None
        self.death_confirmed = False  # DEAT Y = death confirmed
        self.age_at_death = None  # AGE tag
        self.nickname = None  # NICK tag
        self._occupations = None
        self._occupations_loaded = False
        self._notes = None
        self._notes_loaded = False
        self._text_tags_loaded = False
        self.baptism_date = None  # CHR/DATE
        self.baptism_place = None  # CHR/PLAC
        self.marriage_count = None  # NMR (nombre de mariages)
        self._properties = None
        self._properties_loaded = False
        self._texts = None
        self._obje = None
        self._obje_loaded = False

        self._famc_links = None
        self._fams = None
        self._fams_loaded = False
        self._events = None

        parsed_lines = entity.parsed_lines()
        self._parse_lines(parsed_lines)
        self._load_scalar_fields(parsed_lines)

    @property
    def names(self):
        """Retourne tous les noms GEDCOM de l'individu."""
        if self._names is None:
            self._names = get_tag_values(self.entity, "NAME", level=1)
        return self._names

    @property
    def notes(self):
        """Retourne les notes (chargement paresseux)."""
        if not self._notes_loaded:
            self._load_notes()
        if self._notes is None:
            self._notes = []
        return self._notes

    @notes.setter
    def notes(self, value):
        """Définit les notes."""
        self._notes = value if value else None
        self._notes_loaded = True

    @property
    def texts(self):
        """Retourne les textes TEXT (chargement paresseux)."""
        if not self._text_tags_loaded:
            self._load_text_tags()
        if self._texts is None:
            self._texts = []
        return self._texts

    @texts.setter
    def texts(self, value):
        """Définit les textes."""
        self._texts = value if value else None
        self._text_tags_loaded = True

    @property
    def occupations(self):
        """Retourne les professions (chargement paresseux)."""
        if not self._occupations_loaded:
            self._load_occupations()
        if self._occupations is None:
            self._occupations = []
        return self._occupations

    @occupations.setter
    def occupations(self, value):
        """Définit les professions."""
        self._occupations = value if value else None
        self._occupations_loaded = True

    @property
    def properties(self):
        """Retourne les propriétés (chargement paresseux)."""
        if not self._properties_loaded:
            self._load_properties()
        if self._properties is None:
            self._properties = []
        return self._properties

    @properties.setter
    def properties(self, value):
        """Définit les propriétés."""
        self._properties = value if value else None
        self._properties_loaded = True

    @property
    def famc(self):
        """Retourne le pointeur de la famille parent (premier FAMC)."""
        return self.famc_links[0]["pointer"] if self.famc_links else None

    @property
    def fams(self):
        """Retourne les familles FAMS (chargement paresseux)."""
        if not self._fams_loaded:
            self._load_fams()
        if self._fams is None:
            self._fams = []
        return self._fams

    @fams.setter
    def fams(self, value):
        """Définit les familles FAMS."""
        self._fams = value if value else None
        self._fams_loaded = True

    @property
    def obje(self):
        """Retourne les objets multimédia (chargement paresseux)."""
        if not self._obje_loaded:
            self._load_obje()
        if self._obje is None:
            self._obje = []
        return self._obje

    @obje.setter
    def obje(self, value):
        """Définit les objets multimédia."""
        self._obje = value if value else None
        self._obje_loaded = True

    def _load_fams(self):
        """Charge les pointeurs de familles FAMS."""
        self._fams_loaded = True
        self._fams = get_tag_values(self.entity, "FAMS", level=1)

    def _load_obje(self):
        """Charge les objets multimédia OBJE et leurs fichiers inline."""
        self._obje_loaded = True
        self._obje = [
            value.strip()
            for value in get_tag_values(self.entity, "OBJE", level=1)
            if value and value.strip() != "*"
        ]
        self._obje.extend(
            value.strip()
            for value in get_subtag_values(self.entity, "OBJE", "FILE")
            if value and value.strip()
        )

    def _load_occupations(self):
        """Charge les professions OCCU."""
        self._occupations_loaded = True
        self._occupations = []
        current_occupation = None

        for level, _pointer, tag, value in self.entity.parsed_lines():
            if level == 1:
                current_occupation = None
                if tag == "OCCU":
                    current_occupation = {"occupation": value, "date": None}
                    self._occupations.append(current_occupation)
            elif level == 2 and current_occupation is not None and tag == "DATE":
                current_occupation["date"] = value

    def _load_properties(self):
        """Charge les propriétés additionnelles."""
        self._properties_loaded = True
        self._properties = get_tag_values(self.entity, "PROP", level=1)

    def _load_notes(self):
        """Charge les notes NOTE."""
        self._notes_loaded = True
        self._notes = get_tag_values(self.entity, "NOTE", level=1)

    @property
    def events(self):
        """Retourne les événements (chargement paresseux)."""
        if self._events is None:
            self._events = self._build_event_tree(self.entity.parsed_lines())
        return self._events

    @events.setter
    def events(self, value):
        """Définit les événements."""
        self._events = value

    # Tags gérés par un affichage dédié (exclus de l'arbre générique d'événements)
    _EXCLUDED_EVENT_TAGS = {
        "FAMC",
        "FAMS",
        "NAME",
        "NOTE",
        "OBJE",
        "OCCU",
        "PROP",
        "SEX",
        "TEXT",
    }

    @classmethod
    def _build_event_tree(cls, lines):
        """Build a generic tag tree for every level 1 GEDCOM tag (except the
        ones already covered by a dedicated field/tab), preserving the full
        sub-tag hierarchy (PLAC/MAP/LATI, SOUR/DATA/TEXT/CONT, etc.).
        """
        events = []
        last_node_at_level: dict[int, dict | None] = {}

        for level, _pointer, tag, value in lines:
            if level is None or level == 0:
                continue

            if tag in CONTINUATION_TAGS:
                parent = last_node_at_level.get(level - 1)
                if parent is not None:
                    parent["value"] = append_continuation(
                        parent["value"], tag, value or ""
                    )
                for lvl in [lvl for lvl in last_node_at_level if lvl >= level]:
                    del last_node_at_level[lvl]
                continue

            node = {"tag": tag, "value": value, "children": []}

            if level == 1:
                if tag in cls._EXCLUDED_EVENT_TAGS:
                    last_node_at_level[1] = None
                else:
                    events.append(node)
                    last_node_at_level[1] = node
            else:
                parent = last_node_at_level.get(level - 1)
                if parent is not None:
                    parent["children"].append(node)
                last_node_at_level[level] = node

            for lvl in [lvl for lvl in last_node_at_level if lvl > level]:
                del last_node_at_level[lvl]

        return events

    TAG_QUERIES = (("NAME", 1), ("SEX", 1), ("NICK", None), ("NMR", 1))
    SUBTAG_QUERIES = (
        ("BIRT", "DATE"),
        ("BIRT", "PLAC"),
        ("DEAT", "DATE"),
        ("DEAT", "PLAC"),
        ("DEAT", "AGE"),
        ("CHR", "DATE"),
        ("CHR", "PLAC"),
    )

    def _load_scalar_fields(self, parsed_lines):
        """Charge les champs scalaires avec les continuations fusionnées."""
        values = TagValueCollector(parsed_lines, self.TAG_QUERIES, self.SUBTAG_QUERIES)
        self._names = values.values("NAME", level=1)
        self.name = self._names[0] if self._names else None

        sex_values = values.values("SEX", level=1)
        self.sex = sex_values[-1] if sex_values else None

        nicknames = values.values("NICK")
        self.nickname = nicknames[-1] if nicknames else None

        number_values = values.values("NMR", level=1)
        for value in reversed(number_values):
            try:
                self.marriage_count = int(value)
                break
            except (ValueError, TypeError):
                continue

        self.birth_date = values.subtag("BIRT", "DATE")
        self.birth_place = values.subtag("BIRT", "PLAC")
        self.death_date = values.subtag("DEAT", "DATE")
        self.death_place = values.subtag("DEAT", "PLAC")
        self.age_at_death = values.subtag("DEAT", "AGE")
        self.baptism_date = values.subtag("CHR", "DATE")
        self.baptism_place = values.subtag("CHR", "PLAC")

    def _parse_lines(self, lines):
        """Analyse les liens familiaux et les indicateurs de décès."""
        current_section = None
        current_famc = None

        for level, _pointer, tag, value in lines:
            if level is None:
                continue

            if level == 1:
                current_section = tag
                current_famc = None
                if tag == "FAMC":
                    current_famc = {"pointer": value, "details": []}
                    self.famc_links.append(current_famc)
                elif tag == "DEAT":
                    self.death_confirmed = (value or "").strip().upper() == "Y"
                continue

            if level == 2 and current_section == "FAMC" and current_famc is not None:
                current_famc["details"].append((tag, value))
            elif level == 2 and current_section == "DEAT" and tag == "Y":
                self.death_confirmed = True

    def _load_text_tags(self):
        """Charge les textes TEXT avec continuations fusionnées."""
        self.texts = get_tag_values(self.entity, "TEXT", level=1)
