class Individual:
    def __init__(self, entity):
        self.entity = entity
        self.pointer = entity.pointer

        self.name = None
        self.sex = None
        self.birth_date = None
        self.birth_place = None
        self.death_date = None
        self.death_place = None

        self.famc = None      # une seule famille d’enfance
        self.fams = []        # plusieurs familles comme parent

        self._parse_lines(entity.lines)

    def _parse_lines(self, lines):
        for line in lines:
            parts = line.strip().split(" ", 2)
            if len(parts) < 2:
                continue

            level = parts[0]
            tag = parts[1]
            value = parts[2] if len(parts) > 2 else None

            if level == "1":
                if tag == "NAME":
                    self.name = value
                elif tag == "SEX":
                    self.sex = value
                elif tag == "FAMC":
                    self.famc = value
                elif tag == "FAMS":
                    self.fams.append(value)   # 🔥 CORRECTION ICI
