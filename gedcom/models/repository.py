from gedcom.parser import _parse_line


class Repository:
    def __init__(self, entity):
        self.entity = entity
        self.pointer = entity.pointer

        self.name = None
        self.address = None
        self.city = None
        self.state = None
        self.postal_code = None
        self.country = None

        self._parse_lines(entity.lines)

    def _parse_lines(self, lines):
        current_section = None

        for raw in lines:
            level, pointer, tag, value = _parse_line(raw)

            # Debug optionnel :
            # print("REPO PARSED:", level, pointer, tag, value)

            if level is None:
                continue

            # --- Niveau 1 : champs principaux ---
            if level == 1:
                current_section = tag

                if tag == "NAME":
                    self.name = value

                elif tag == "ADDR":
                    self.address = value

            # --- Niveau 2 : sous-sections de ADDR ---
            elif level == 2 and current_section == "ADDR":

                if tag == "CITY":
                    self.city = value

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
