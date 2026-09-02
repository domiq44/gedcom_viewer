from gedcom.parser import _parse_line


class MultimediaObject:
    def __init__(self, entity):
        self.entity = entity
        self.pointer = entity.pointer

        self.file = None
        self.title = None
        self.format = None
        self.note = None

        self._parse_lines(entity.lines)

    def _parse_lines(self, lines):
        current_section = None

        for raw in lines:
            level, pointer, tag, value = _parse_line(raw)

            # Debug optionnel :
            # print("OBJE PARSED:", level, pointer, tag, value)

            if level is None:
                continue

            # --- Niveau 1 : champs principaux ---
            if level == 1:
                current_section = tag

                if tag == "FILE":
                    self.file = value

                elif tag == "TITL":
                    self.title = value

                elif tag == "FORM":
                    self.format = value

                elif tag == "NOTE":
                    self.note = value

            # --- Niveau 2 : continuation de NOTE ---
            elif level == 2 and current_section == "NOTE":

                if tag == "CONC" and value:
                    self.note = f"{self.note or ''}{value}"

                elif tag == "CONT" and value:
                    self.note = f"{self.note or ''}\n{value}"
