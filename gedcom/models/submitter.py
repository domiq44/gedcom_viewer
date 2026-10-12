from gedcom.parser import _parse_line
from gedcom.models.lazy_list import _LazyList


class Submitter:
    phones = _LazyList()
    emails = _LazyList()

    __slots__ = (
        "entity",
        "pointer",
        "name",
        "address",
        "phone",
        "email",
        "_phones",
        "_emails",
    )

    def __init__(self, entity):
        self.entity = entity
        self.pointer = entity.pointer

        self.name = None
        self.address = None
        self.phone = None
        self.email = None
        self._phones = None
        self._emails = None

        self._parse_lines(entity.lines)

    def _parse_lines(self, lines):
        current_section = None

        for raw in lines:
            level, pointer, tag, value = _parse_line(raw)

            # Debug optionnel :
            # print("SUB PARSED:", level, pointer, tag, value)

            if level is None:
                continue

            # --- Niveau 1 : champs principaux ---
            if level == 1:
                current_section = tag

                if tag == "NAME":
                    self.name = value

                elif tag == "ADDR":
                    self.address = value

                elif tag == "PHON":
                    self.phone = value
                    self.phones.append(value)

                elif tag == "EMAIL":
                    self.email = value
                    self.emails.append(value)

            # --- Niveau 2 : continuation de ADDR ---
            elif level == 2 and current_section == "ADDR":
                if tag == "CONC" and value:
                    self.address = f"{self.address or ''}{value}"

                elif tag == "CONT" and value:
                    self.address = f"{self.address or ''}\n{value}"
