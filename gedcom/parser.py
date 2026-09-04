import logging
import re

logger = logging.getLogger(__name__)

REFERENCE_TAGS = {
    "ASSO",
    "CHIL",
    "FAMC",
    "FAMS",
    "HUSB",
    "NOTE",
    "OBJE",
    "REPO",
    "SOUR",
    "SUBM",
    "WIFE",
}


def _parse_line(line):
    stripped = line.strip()

    if not stripped:
        return None, None, None, None

    parts = stripped.split()

    if len(parts) == 0:
        return None, None, None, None

    try:
        level = int(parts[0])
    except ValueError:
        return None, None, None, None

    remainder = " ".join(parts[1:])
    if not remainder:
        return None, None, None, None

    pointer = None
    tag = None
    value = ""

    if level == 0 and remainder.startswith("@"):
        sub = remainder.split(" ", 2)

        pointer = sub[0]
        tag = sub[1] if len(sub) >= 2 else None
        value = sub[2] if len(sub) == 3 else ""

        return level, pointer, tag, value

    sub = remainder.split(" ", 1)
    tag = sub[0] if len(sub) >= 1 else None
    value = sub[1] if len(sub) == 2 else ""

    return level, pointer, tag, value


class GedcomParser:
    def __init__(self):
        self.lines = []
        self.entities = {}  # dict: type → liste de GedcomEntity
        self._by_pointer = {}  # dict: pointer → GedcomEntity
        self.malformed_lines = []
        self.encoding_replacements = 0
        self.validation_errors = []

    def load(self, filename, strict=False):
        with open(filename, "r", encoding="utf-8-sig", errors="replace") as f:
            raw_lines = f.readlines()

        self.encoding_replacements = sum(line.count("\ufffd") for line in raw_lines)
        if self.encoding_replacements:
            logger.warning(
                "%s caractère(s) invalide(s) remplacé(s) lors de la lecture de %s",
                self.encoding_replacements,
                filename,
            )

        self.lines = [line.replace("\xa0", " ").rstrip("\r\n") for line in raw_lines]

        self._parse_entities()
        self.validation_errors = self.validate()
        for error in self.validation_errors:
            logger.warning("Validation GEDCOM: %s", error)
        if strict and self.validation_errors:
            raise ValueError(
                "Fichier GEDCOM invalide: " + "; ".join(self.validation_errors)
            )

    def validate(self):
        """Retourne les anomalies structurelles détectées dans le fichier chargé."""
        errors = []
        previous_level = None
        pointer_counts = {}
        head_count = 0
        trailer_count = 0
        level_zero_records = []

        for idx, line in enumerate(self.lines):
            if not line.strip():
                continue

            level, pointer, tag, value = _parse_line(line)
            line_number = idx + 1
            if level is None or tag is None:
                errors.append(f"ligne {line_number} malformée")
                continue

            if level < 0:
                errors.append(f"niveau négatif ligne {line_number}")
            if previous_level is not None and level > previous_level + 1:
                errors.append(f"saut de niveau ligne {line_number}")
            previous_level = level

            if level == 0:
                level_zero_records.append((line_number, tag))
                if tag in {"HEAD", "TRLR"} and pointer is not None:
                    errors.append(f"pointeur inattendu ligne {line_number}")
                if tag == "HEAD":
                    head_count += 1
                elif tag == "TRLR":
                    trailer_count += 1
                if pointer:
                    pointer_counts[pointer] = pointer_counts.get(pointer, 0) + 1
                    if not re.fullmatch(r"@[^@\s]+@", pointer):
                        errors.append(f"pointeur invalide ligne {line_number}")

            if tag in REFERENCE_TAGS and re.fullmatch(r"@[^@\s]+@", value or ""):
                if value not in self._by_pointer:
                    errors.append(f"référence inconnue {value} ligne {line_number}")

        errors.extend(
            f"pointeur dupliqué {pointer}"
            for pointer, count in pointer_counts.items()
            if count > 1
        )
        if head_count != 1:
            errors.append("HEAD absent ou multiple")
        if trailer_count != 1:
            errors.append("TRLR absent ou multiple")
        if level_zero_records and level_zero_records[0][1] != "HEAD":
            errors.append("HEAD doit être le premier enregistrement")
        if trailer_count == 1 and level_zero_records[-1][1] != "TRLR":
            trailer_line = next(
                line_number for line_number, tag in level_zero_records if tag == "TRLR"
            )
            errors.append(
                f"TRLR doit être le dernier enregistrement ligne {trailer_line}"
            )
        return errors

    def _parse_entities(self):
        self.entities = {}
        self._by_pointer = {}
        self.malformed_lines = []

        current_lines = []
        current_pointer = None
        current_tag = None
        current_start_index = None

        for idx, line in enumerate(self.lines):
            level, pointer, tag, _ = _parse_line(line)
            if level is None:
                if line.strip():
                    line_number = idx + 1
                    self.malformed_lines.append(line_number)
                    logger.warning(
                        "Ligne GEDCOM malformée ignorée (%s): %s",
                        line_number,
                        line.strip(),
                    )
                continue

            if level == 0:
                if current_tag is not None:
                    entity = GedcomEntity(
                        pointer=current_pointer,
                        tag=current_tag,
                        start_index=current_start_index,
                        lines=current_lines,
                    )
                    self._register_entity(entity)

                current_pointer = pointer
                current_tag = tag
                current_start_index = idx
                current_lines = [line + "\n"]
            else:
                if current_tag is not None:
                    current_lines.append(line + "\n")

        if current_tag is not None:
            entity = GedcomEntity(
                pointer=current_pointer,
                tag=current_tag,
                start_index=current_start_index,
                lines=current_lines,
            )
            self._register_entity(entity)

    def _register_entity(self, entity: GedcomEntity):
        if entity.tag is None:
            return

        self.entities.setdefault(entity.tag, []).append(entity)

        if entity.pointer:
            if entity.pointer in self._by_pointer:
                logger.warning(
                    "Pointeur GEDCOM dupliqué, première occurrence conservée: %s",
                    entity.pointer,
                )
            else:
                self._by_pointer[entity.pointer] = entity

    def get_entity(self, pointer):
        return self._by_pointer.get(pointer)

    def extract_block(self, pointer):
        """
        Retourne le bloc brut pour une entité donnée par son pointeur (@I1@).
        """
        entity = self._by_pointer.get(pointer)
        if not entity:
            return ""
        return entity.raw_block()

    def extract_head(self):
        """
        Retourne le bloc HEAD (0 HEAD ...), même sans pointeur.
        """
        heads = self.entities.get("HEAD", [])
        if heads:
            return heads[0].raw_block()

        head_lines = []
        inside = False

        for line in self.lines:
            level, _, tag, _ = _parse_line(line)
            if tag is None:
                continue

            if tag == "HEAD" and level == 0:
                inside = True
                head_lines = [line.strip()]
                continue

            if inside:
                if level == 0:
                    break
                head_lines.append(line.strip())

        return "\n".join(head_lines).strip()

    def extract_trailer(self):
        """
        Retourne le bloc TRLR (0 TRLR ...), même sans pointeur.
        """
        trailers = self.entities.get("TRLR", [])
        if trailers:
            return trailers[0].raw_block()

        trailer_lines = []
        inside = False

        for line in self.lines:
            level, _, tag, _ = _parse_line(line)
            if tag is None:
                continue

            if tag == "TRLR" and level == 0:
                inside = True
                trailer_lines = [line.strip()]
                continue

            if inside:
                if level == 0:
                    break
                trailer_lines.append(line.strip())

        return "\n".join(trailer_lines).strip()


class GedcomEntity:
    __slots__ = ("pointer", "tag", "start_index", "lines")

    def __init__(self, pointer, tag, start_index, lines):
        self.pointer = pointer  # ex: "@I1@" ou None
        self.tag = tag  # ex: "INDI", "FAM", "HEAD", "NOTE"
        self.start_index = start_index  # index de la ligne "0 ..."
        self.lines = lines  # liste de lignes brutes (incluant sous-niveaux)

    def raw_block(self):
        return "".join(self.lines)

    def _append_continuation(self, values, line_tag, value):
        suffix = value or ""
        if line_tag == "CONC":
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
        elif line_tag == "CONT":
            if values:
                values[-1] += "\n" + suffix
            else:
                values.append(suffix)

    def get_tag_values(self, tag):
        values = []
        collecting = False
        current_level = None

        for line in self.lines:
            level, _, line_tag, value = _parse_line(line)
            if line_tag is None:
                continue

            if line_tag == tag:
                collecting = True
                current_level = level
                values.append(value or "")
                continue

            if collecting:
                if line_tag in {"CONC", "CONT"} and level >= current_level:
                    self._append_continuation(values, line_tag, value)
                    continue

                if level <= current_level and line_tag != tag:
                    collecting = False

        return [item.strip() for item in values if item is not None]

    def get_tag_value(self, tag):
        values = self.get_tag_values(tag)
        return values[0] if values else ""

    def get_subtag_values(self, parent_tag, child_tag):
        values = []
        collecting = False
        parent_level = None
        child_level = None

        for line in self.lines:
            level, _, line_tag, value = _parse_line(line)
            if line_tag is None:
                continue

            if line_tag == parent_tag and level == 1:
                collecting = True
                parent_level = level
                child_level = None
                continue

            if collecting:
                if level <= parent_level and line_tag not in {"CONC", "CONT"}:
                    collecting = False

                if line_tag == child_tag and level > parent_level:
                    values.append(value or "")
                    child_level = level
                    continue

                if line_tag in {"CONC", "CONT"} and child_level is not None:
                    if level >= child_level:
                        self._append_continuation(values, line_tag, value)
                    continue

        return [item.strip() for item in values if item is not None]
