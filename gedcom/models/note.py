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
        self.sources = []
        self.references = []
        self.record_id = None
        self.submitters = []
        self.change_date = None
        self.change_time = None
        self.additional_fields = []

        self._parse_lines(entity.lines)

    def _parse_lines(self, lines):
        current_section = None
        current_level = None
        current_additional = None

        for raw in lines:
            level, pointer, tag, value = _parse_line(raw)

            if level is None:
                continue

            if level == 0 and tag == "NOTE":
                self.text = value or ""
                current_section = "NOTE"
                current_level = level
                continue

            if level == 1:
                if tag in {"CONC", "CONT"} and current_section == "NOTE":
                    suffix = value or ""
                    if tag == "CONT":
                        self.text = (self.text + "\n" + suffix).strip("\n")
                    elif suffix:
                        needs_space = (
                            bool(self.text)
                            and not self.text.endswith(" ")
                            and not suffix.startswith(" ")
                            and suffix[0] not in {",", ".", ";", ":", "?", "!"}
                        )
                        self.text += (" " if needs_space else "") + suffix
                    continue

                current_additional = None
                if tag == "NOTE":
                    self.text = (self.text + "\n" + (value or "")).strip("\n")
                    current_section = "NOTE"
                    current_level = level
                elif tag == "SOUR":
                    self.source = value
                    self.sources.append(value)
                elif tag == "REFN":
                    self.references.append(value)
                elif tag == "RIN":
                    self.record_id = value
                elif tag == "SUBM":
                    self.submitters.append(value)
                elif tag == "CHAN":
                    current_section = "CHAN"
                elif tag not in {"SOUR", "REFN", "RIN", "SUBM", "CHAN"}:
                    current_additional = {"tag": tag, "value": value, "details": []}
                    self.additional_fields.append(current_additional)
                if tag == "NOTE":
                    continue

            if current_section == "NOTE":
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

            if current_section == "CHAN" and level >= 2:
                if tag == "DATE":
                    self.change_date = value
                elif tag == "TIME":
                    self.change_time = value

            if current_additional is not None and level >= 2:
                current_additional["details"].append((tag, value))
