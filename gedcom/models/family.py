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

        print("HUSB:", self.husband)
        print("WIFE:", self.wife)
        print("CHIL:", self.children)
        print("MARR:", self.marriage_date, self.marriage_place)
        print("DIV:", self.divorce_date, self.divorce_place)

    def _parse_lines(self, lines):
        current_section = None  # MARR, DIV, CHAN, etc.

        for line in lines:
            parts = line.strip().split(" ", 2)

            if len(parts) < 2:
                continue

            level = parts[0]
            tag = parts[1]
            value = parts[2] if len(parts) > 2 else None

            # Niveau 1 : nouvelle section
            if level == "1":
                current_section = tag

                if tag == "HUSB":
                    self.husband = value
                elif tag == "WIFE":
                    self.wife = value
                elif tag == "CHIL":
                    self.children.append(value)

            # Niveau 2 : sous-tags (DATE, PLAC…)
            elif level == "2":
                if current_section == "MARR":
                    if tag == "DATE":
                        self.marriage_date = value
                    elif tag == "PLAC":
                        self.marriage_place = value

                elif current_section == "DIV":
                    if tag == "DATE":
                        self.divorce_date = value
                    elif tag == "PLAC":
                        self.divorce_place = value
