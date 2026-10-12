from gedcom.parser import _parse_line
from gedcom.models.event import Event
from gedcom.models.lazy_list import _LazyList


class Family:
    """
    Représente une famille GEDCOM (FAM) basée sur entity.lines.
    """

    children = _LazyList()
    notes = _LazyList()
    sources = _LazyList()
    events = _LazyList()
    additional_fields = _LazyList()
    marriages = _LazyList()
    divorces = _LazyList()

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
    )

    def __init__(self, entity):
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

        # Analyse des lignes brutes
        self._parse_lines(entity.lines)

    def _parse_lines(self, lines):
        current_section = None
        current_event = None
        current_additional = None
        known_level_one_tags = {
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

        for raw in lines:
            level, pointer, tag, value = _parse_line(raw)

            # Debug optionnel :
            # print("FAM PARSED:", level, pointer, tag, value)

            if level is None:
                continue

            # --- Niveau 1 : sections principales ---
            if level == 1:
                current_section = tag
                current_event = None
                current_additional = None

                if tag == "HUSB":
                    self.husband = value

                elif tag == "WIFE":
                    self.wife = value

                elif tag == "CHIL":
                    self.children.append(value)

                elif tag == "NCHI":
                    try:
                        self.number_of_children = int(value)
                    except (ValueError, TypeError):
                        self.number_of_children = value

                elif tag in {"ENGA", "MARB", "MARC", "MARL", "MARS", "DIVF", "ANUL"}:
                    setattr(
                        self,
                        {
                            "ENGA": "engagement",
                            "MARB": "marriage_banns",
                            "MARC": "marriage_contract",
                            "MARL": "marriage_license",
                            "MARS": "marriage_settlement",
                            "DIVF": "divorce_final",
                            "ANUL": "annulment",
                        }[tag],
                        value or True,
                    )

                elif tag == "NOTE":
                    self.notes.append(value)

                elif tag == "SOUR":
                    self.sources.append(value)

                elif tag == "MARR":
                    current_event = Event("MARR", value)
                    self.marriages.append(current_event)

                elif tag == "DIV":
                    current_event = Event("DIV", value)
                    self.divorces.append(current_event)

                elif tag == "EVEN":
                    current_event = Event("EVEN", value)
                    self.events.append(current_event)

                if tag not in known_level_one_tags:
                    current_additional = {"tag": tag, "value": value, "details": []}
                    self.additional_fields.append(current_additional)

            # --- Niveau 2 : sous-tags (DATE, PLAC…) ---
            elif level == 2:

                if current_event is not None:
                    current_event.add_detail(tag, value)

                if current_section == "NOTE" and self.notes:
                    if tag == "CONT":
                        self.notes[-1] += f"\n{value or ''}"
                    elif tag == "CONC":
                        self.notes[-1] += value or ""

                # Mariage
                if current_section == "MARR":
                    if tag == "DATE":
                        self.marriage_date = value
                    elif tag == "PLAC":
                        self.marriage_place = value

                # Divorce
                elif current_section == "DIV":
                    if tag == "DATE":
                        self.divorce_date = value
                    elif tag == "PLAC":
                        self.divorce_place = value

                if current_additional is not None:
                    current_additional["details"].append((tag, value))

            elif level >= 3:
                if current_event is not None:
                    current_event.add_detail(tag, value)
                if current_additional is not None:
                    current_additional["details"].append((tag, value))
