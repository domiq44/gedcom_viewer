from gedcom.parser import _parse_line


class Source:
    def __init__(self, entity):
        self.entity = entity
        self.pointer = entity.pointer

        self.title = None
        self.author = None
        self.pub_date = None
        self.text = None
        self.repository = None
        self.call_number = None
        self.media = None
        self.repo_note = None
        self.publication = None
        self.abbreviation = None
        self.notes = []
        self.sources = []
        self.references = []
        self.record_id = None
        self.data_events = []
        self.agency = None
        self.additional_fields = []

        self._parse_lines(entity.lines)

    def _parse_lines(self, lines):
        current_section = None
        current_additional = None

        for raw in lines:
            level, pointer, tag, value = _parse_line(raw)

            # Debug optionnel :
            # print("SRC PARSED:", level, pointer, tag, value)

            if level is None:
                continue

            # --- Niveau 1 : champs principaux ---
            if level == 1:
                current_section = tag
                current_additional = None

                if tag == "TITL":
                    self.title = value

                elif tag == "AUTH":
                    self.author = value

                elif tag == "DATE":
                    self.pub_date = value

                elif tag == "TEXT":
                    self.text = value

                elif tag == "NOTE":
                    self.notes.append(value)

                elif tag == "REPO":
                    self.repository = value

                elif tag == "PUBL":
                    self.publication = value

                elif tag == "ABBR":
                    self.abbreviation = value

                elif tag == "SOUR":
                    self.sources.append(value)

                elif tag == "REFN":
                    self.references.append(value)

                elif tag == "RIN":
                    self.record_id = value

                elif tag == "DATA":
                    current_section = "DATA"

                elif tag not in {
                    "TITL",
                    "AUTH",
                    "DATE",
                    "TEXT",
                    "NOTE",
                    "REPO",
                    "PUBL",
                    "ABBR",
                    "SOUR",
                    "REFN",
                    "RIN",
                    "DATA",
                }:
                    current_additional = {"tag": tag, "value": value, "details": []}
                    self.additional_fields.append(current_additional)

            # --- Niveau 2 : sous-sections ---
            elif level == 2 and current_section:

                # Sous TITL
                if current_section == "TITL":
                    if tag == "CONC":
                        self.title = f"{self.title or ''}{value}"
                    elif tag == "CONT":
                        self.title = f"{self.title or ''}\n{value}"
                    elif tag == "AUTH":
                        self.author = value

                # Sous TEXT / NOTE
                elif current_section in ("TEXT", "NOTE"):
                    if tag == "CONC":
                        if current_section == "NOTE" and self.notes:
                            self.notes[-1] = f"{self.notes[-1] or ''}{value}"
                        else:
                            self.text = f"{self.text or ''}{value}"
                    elif tag == "CONT":
                        if current_section == "NOTE" and self.notes:
                            self.notes[-1] = f"{self.notes[-1] or ''}\n{value}"
                        else:
                            self.text = f"{self.text or ''}\n{value}"

                elif current_section == "DATA":
                    if tag == "EVEN":
                        self.data_events.append({"value": value, "details": []})
                    elif self.data_events:
                        self.data_events[-1]["details"].append((tag, value))
                    elif tag == "AGNC":
                        self.agency = value
                    elif tag == "NOTE":
                        self.text = f"{self.text or ''}\n{value}"

                # Sous REPO
                elif current_section == "REPO":
                    if tag == "CALN":
                        self.call_number = value
                    elif tag == "NOTE":
                        self.repo_note = value

            # --- Niveau 3 : sous REPO ---
            elif level == 3 and current_section == "REPO":
                if tag == "MEDI":
                    self.media = value

            if current_additional is not None and level >= 2:
                current_additional["details"].append((tag, value))
