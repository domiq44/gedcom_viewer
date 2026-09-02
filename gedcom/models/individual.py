from gedcom.parser import _parse_line


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
        self.death_confirmed = False  # DEAT Y = death confirmed
        self.age_at_death = None  # AGE tag
        self.nickname = None  # NICK tag
        self.occupations = []  # OCCU tags with dates
        self.notes = []  # NOTE tags
        self.baptism_date = None  # CHR/DATE
        self.baptism_place = None  # CHR/PLAC
        self.marriage_count = None  # NMR (nombre de mariages)
        self.properties = []  # PROP tags
        self.texts = []  # TEXT tags (can be long)

        self.famc = None
        self.fams = []

        self._parse_lines(entity.lines)
        self._load_text_tags()  # Load TEXT tags with continuation support

    def _parse_lines(self, lines):
        current_section = None

        for raw in lines:
            level, pointer, tag, value = _parse_line(raw)

            if level is None:
                continue

            # --- Niveau 1 : champs principaux ---
            if level == 1:
                current_section = tag

                if tag == "NAME":
                    self.name = value

                elif tag == "SEX":
                    self.sex = value

                elif tag == "FAMC":
                    self.famc = value

                elif tag == "FAMS":
                    self.fams.append(value)

                elif tag == "NICK":
                    self.nickname = value

                elif tag == "NMR":
                    try:
                        self.marriage_count = int(value)
                    except (ValueError, TypeError):
                        pass

                elif tag == "NOTE":
                    self.notes.append(value)

                elif tag == "OCCU":
                    self.occupations.append({"occupation": value, "date": None})

                elif tag == "PROP":
                    self.properties.append(value)

                elif tag == "DEAT":
                    self.death_confirmed = True

            # --- Niveau 2 : sous-sections ---
            elif level == 2 and current_section:

                # Sous NAME
                if current_section == "NAME":
                    if tag == "CONC" and value:
                        self.name = f"{self.name or ''}{value}"
                    elif tag == "CONT" and value:
                        self.name = f"{self.name or ''}\n{value}"

                # Sous BIRT
                elif current_section == "BIRT":
                    if tag == "DATE":
                        self.birth_date = value
                    elif tag == "PLAC":
                        self.birth_place = value
                    elif tag == "NOTE":
                        self.notes.append(value)

                # Sous DEAT
                elif current_section == "DEAT":
                    if tag == "DATE":
                        self.death_date = value
                    elif tag == "PLAC":
                        self.death_place = value
                    elif tag == "Y":
                        self.death_confirmed = True
                    elif tag == "AGE":
                        self.age_at_death = value
                    elif tag == "NOTE":
                        self.notes.append(value)

                # Sous CHR (baptism)
                elif current_section == "CHR":
                    if tag == "DATE":
                        self.baptism_date = value
                    elif tag == "PLAC":
                        self.baptism_place = value
                    elif tag == "NOTE":
                        self.notes.append(value)

                # Sous OCCU
                elif current_section == "OCCU" and self.occupations:
                    if tag == "DATE":
                        self.occupations[-1]["date"] = value

                # Sous NOTE (continuations)
                elif current_section == "NOTE":
                    if tag == "CONT" and value:
                        self.notes[-1] = f"{self.notes[-1] or ''}\n{value}"

            # --- Niveau 3+ : continuations ---
            elif level >= 3:
                # Gestion des continuations de notes et autres
                if current_section == "DEAT" and tag == "NOTE":
                    self.notes.append(value)
                elif current_section == "BIRT" and tag == "NOTE":
                    self.notes.append(value)

    def _load_text_tags(self):
        """Load TEXT tags with CONT/CONC continuation support.

        Prefer the parser helper when available, but keep a safe fallback for
        lightweight test doubles or objects created without that method.
        """
        if hasattr(self.entity, "get_tag_values"):
            self.texts = self.entity.get_tag_values("TEXT")
            return

        values = []
        collecting = False
        current_level = None

        for raw in self.entity.lines:
            level, _, tag, value = _parse_line(raw)
            if tag is None:
                continue

            if tag == "TEXT":
                collecting = True
                current_level = level
                values.append(value or "")
                continue

            if collecting:
                if tag in {"CONC", "CONT"} and level >= current_level:
                    suffix = value or ""
                    if tag == "CONC":
                        if values and values[-1]:
                            needs_space = (
                                not values[-1].endswith(" ")
                                and suffix
                                and not suffix.startswith(" ")
                            )
                            if suffix and suffix[0] in {",", ".", ";", ":", "?", "!"}:
                                needs_space = False
                            if needs_space:
                                values[-1] += " " + suffix
                            else:
                                values[-1] += suffix
                        else:
                            values.append(suffix)
                    elif tag == "CONT":
                        if values:
                            values[-1] += "\n" + suffix
                        else:
                            values.append(suffix)
                    continue

                if level <= current_level and tag != "TEXT":
                    collecting = False

        self.texts = [item.strip() for item in values if item is not None]
