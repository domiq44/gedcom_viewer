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

        self._parse_lines(entity.lines)

    def _parse_lines(self, lines):
        current_section = None

        for raw in lines:
            level, pointer, tag, value = _parse_line(raw)

            # Debug optionnel :
            # print("SRC PARSED:", level, pointer, tag, value)

            if level is None:
                continue

            # --- Niveau 1 : champs principaux ---
            if level == 1:
                current_section = tag

                if tag == "TITL":
                    self.title = value

                elif tag == "AUTH":
                    self.author = value

                elif tag == "DATE":
                    self.pub_date = value

                elif tag == "TEXT":
                    self.text = value

                elif tag == "NOTE":
                    self.text = value

                elif tag == "REPO":
                    self.repository = value

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
                        self.text = f"{self.text or ''}{value}"
                    elif tag == "CONT":
                        self.text = f"{self.text or ''}\n{value}"
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
