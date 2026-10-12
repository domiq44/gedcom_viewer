from gedcom.parser import _parse_line
from gedcom.models.lazy_list import _LazyList


class Repository:
    notes = _LazyList()
    references = _LazyList()
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
        "_notes",
        "_references",
        "record_id",
        "change_date",
        "change_time",
        "_additional_fields",
    )

    def __init__(self, entity):
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
        self._notes = None
        self._references = None
        self.record_id = None
        self.change_date = None
        self.change_time = None
        self._additional_fields = None

        self._parse_lines(entity.lines)

    def _parse_lines(self, lines):
        current_section = None
        current_additional = None

        for raw in lines:
            level, pointer, tag, value = _parse_line(raw)

            # Debug optionnel :
            # print("REPO PARSED:", level, pointer, tag, value)

            if level is None:
                continue

            # --- Niveau 1 : champs principaux ---
            if level == 1:
                current_section = tag
                current_additional = None

                if tag == "NAME":
                    self.name = value

                elif tag == "ADDR":
                    self.address = value

                elif tag == "NOTE":
                    self.notes.append(value)

                elif tag == "REFN":
                    self.references.append(value)

                elif tag == "RIN":
                    self.record_id = value

                elif tag == "CHAN":
                    current_section = "CHAN"

                elif tag not in {"NAME", "ADDR", "NOTE", "REFN", "RIN", "CHAN"}:
                    current_additional = {"tag": tag, "value": value, "details": []}
                    self.additional_fields.append(current_additional)

            # --- Niveau 2 : sous-sections de ADDR ---
            elif level == 2 and current_section == "ADDR":

                if tag == "CITY":
                    self.city = value

                elif tag == "ADR1":
                    self.address_line_1 = value

                elif tag == "ADR2":
                    self.address_line_2 = value

                elif tag == "STAE":  # oui, GEDCOM utilise parfois STAE
                    self.state = value

                elif tag == "POST":
                    self.postal_code = value

                elif tag == "CTRY":
                    self.country = value

                elif tag == "CONC" and value:
                    self.address = f"{self.address or ''}{value}"

                elif tag == "CONT" and value:
                    self.address = f"{self.address or ''}\n{value}"

            elif level >= 2 and current_section == "CHAN":
                if tag == "DATE":
                    self.change_date = value
                elif tag == "TIME":
                    self.change_time = value

            if current_additional is not None and level >= 2:
                current_additional["details"].append((tag, value))
