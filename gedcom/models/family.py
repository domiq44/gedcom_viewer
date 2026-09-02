from gedcom.parser import _parse_line


class Family:
    """
    Représente une famille GEDCOM (FAM) basée sur entity.lines.
    """

    def __init__(self, entity):
        self.entity = entity
        self.pointer = entity.pointer

        # Valeurs par défaut
        self.husband = None
        self.wife = None
        self.children = []
        self.marriage_date = None
        self.marriage_place = None
        self.divorce_date = None
        self.divorce_place = None

        # Analyse des lignes brutes
        self._parse_lines(entity.lines)

    def _parse_lines(self, lines):
        current_section = None  # MARR, DIV, CHAN, etc.

        for raw in lines:
            level, pointer, tag, value = _parse_line(raw)

            # Debug optionnel :
            # print("FAM PARSED:", level, pointer, tag, value)

            if level is None:
                continue

            # --- Niveau 1 : sections principales ---
            if level == 1:
                current_section = tag

                if tag == "HUSB":
                    self.husband = value

                elif tag == "WIFE":
                    self.wife = value

                elif tag == "CHIL":
                    self.children.append(value)

            # --- Niveau 2 : sous-tags (DATE, PLAC…) ---
            elif level == 2:

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
