from gedcom.parser import _parse_line
from gedcom.models.lazy_list import _LazyList


class Source:
    additional_fields = _LazyList()

    __slots__ = (
        "entity",
        "pointer",
        "title",
        "author",
        "pub_date",
        "text",
        "repository",
        "call_number",
        "media",
        "repo_note",
        "publication",
        "abbreviation",
        "_notes",
        "_reference_lists_loaded",
        "_sources",
        "_references",
        "record_id",
        "_data_events",
        "_data_events_loaded",
        "agency",
        "_additional_fields",
    )

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
        self._notes = None
        self._reference_lists_loaded = False
        self._sources = None
        self._references = None
        self.record_id = None
        self._data_events = None
        self._data_events_loaded = False
        self.agency = None
        self._additional_fields = None

        self._parse_lines(entity.lines)

    @property
    def notes(self):
        self._load_reference_lists()
        if self._notes is None:
            self._notes = []
        return self._notes

    @notes.setter
    def notes(self, value):
        self._load_reference_lists()
        self._notes = value if value else None

    @property
    def sources(self):
        self._load_reference_lists()
        if self._sources is None:
            self._sources = []
        return self._sources

    @sources.setter
    def sources(self, value):
        self._load_reference_lists()
        self._sources = value if value else None

    @property
    def references(self):
        self._load_reference_lists()
        if self._references is None:
            self._references = []
        return self._references

    @references.setter
    def references(self, value):
        self._load_reference_lists()
        self._references = value if value else None

    def _load_reference_lists(self):
        if self._reference_lists_loaded:
            return

        self._reference_lists_loaded = True
        self._notes = []
        self._sources = []
        self._references = []
        current_section = None

        for raw in self.entity.lines:
            level, _pointer, tag, value = _parse_line(raw)
            if level is None:
                continue

            if level == 1:
                current_section = tag
                if tag == "NOTE":
                    self._notes.append(value)
                elif tag == "SOUR":
                    self._sources.append(value)
                elif tag == "REFN":
                    self._references.append(value)
            elif level == 2 and current_section == "NOTE":
                if tag == "CONC" and self._notes:
                    self._notes[-1] = f"{self._notes[-1] or ''}{value or ''}"
                elif tag == "CONT" and self._notes:
                    self._notes[-1] = f"{self._notes[-1] or ''}\n{value or ''}"

    @property
    def data_events(self):
        self._load_data_events()
        if self._data_events is None:
            self._data_events = []
        return self._data_events

    @data_events.setter
    def data_events(self, value):
        self._load_data_events()
        self._data_events = value if value else None

    def _load_data_events(self):
        if self._data_events_loaded:
            return

        self._data_events_loaded = True
        current_section = None
        current_event = None

        for raw in self.entity.lines:
            level, _pointer, tag, value = _parse_line(raw)

            if level == 1:
                current_section = tag
                current_event = None
            elif current_section == "DATA":
                if level == 2:
                    if tag == "EVEN":
                        if self._data_events is None:
                            self._data_events = []
                        current_event = {"value": value, "details": []}
                        self._data_events.append(current_event)
                    else:
                        current_event = None
                elif level == 3 and current_event is not None:
                    current_event["details"].append((tag, value))

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

                elif tag == "REPO":
                    self.repository = value

                elif tag == "PUBL":
                    self.publication = value

                elif tag == "ABBR":
                    self.abbreviation = value

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
                elif current_section == "TEXT":
                    if tag == "CONC":
                        self.text = f"{self.text or ''}{value}"
                    elif tag == "CONT":
                        self.text = f"{self.text or ''}\n{value}"

                elif current_section == "DATA":
                    if tag == "AGNC":
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
