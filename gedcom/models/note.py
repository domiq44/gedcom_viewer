from gedcom.parser import _parse_line


class Note:
    def __init__(self, entity):
        ###print(">>> NOTE MODEL CALLED FOR", entity.pointer)
        ###for l in entity.lines:
        ###    print("   >", repr(l))

        self.entity = entity
        self.pointer = entity.pointer

        self.text = ""
        self.source = None

        self._parse_lines(entity.lines)

    def _parse_lines(self, lines):
        ###print(">>> DEBUG LINES FOR NOTE", self.pointer)
        current_section = None
        current_level = None

        for raw in lines:
            level, pointer, tag, value = _parse_line(raw)

            if level is None:
                continue

            if level == 0 and tag == "NOTE":
                self.text = value or ""
                current_section = "NOTE"
                current_level = level
                continue

            if current_section == "NOTE":
                if tag == "NOTE" and level == 1:
                    self.text = (self.text + "\n" + (value or "")).strip("\n")
                    current_level = level
                    continue

                if tag in {"CONC", "CONT"} and level >= current_level:
                    suffix = value or ""
                    if tag == "CONC":
                        if self.text:
                            needs_space = (
                                not self.text.endswith(" ")
                                and suffix
                                and not suffix.startswith(" ")
                            )
                            if suffix and suffix[0] in {",", ".", ";", ":", "?", "!"}:
                                needs_space = False
                            self.text += (" " if needs_space else "") + suffix
                        else:
                            self.text = suffix
                    elif tag == "CONT":
                        self.text = (self.text + "\n" + suffix).strip("\n")
                    continue

                if level <= current_level and tag != "NOTE":
                    current_section = None
                    current_level = None

            if level == 1 and tag == "SOUR":
                self.source = value
