from array import array
import logging
import operator
import re

logger = logging.getLogger(__name__)

REFERENCE_TARGET_TAGS = {
    "ALIA": "INDI",
    "ASSO": "INDI",
    "CHIL": "INDI",
    "FAMC": "FAM",
    "FAMS": "FAM",
    "HUSB": "INDI",
    "NOTE": "NOTE",
    "OBJE": "OBJE",
    "REPO": "REPO",
    "SOUR": "SOUR",
    "SUBM": "SUBM",
    "WIFE": "INDI",
}
REFERENCE_SOURCE_TAGS = {
    "ALIA": "INDI",
    "ASSO": "INDI",
    "CHIL": "FAM",
    "FAMC": "INDI",
    "FAMS": "INDI",
    "HUSB": "FAM",
    "REPO": "SOUR",
    "SUBM": "HEAD",
    "WIFE": "FAM",
}
REFERENCE_TAGS = set(REFERENCE_TARGET_TAGS)
POINTER_REQUIRED_RECORD_TAGS = {"FAM", "INDI", "OBJE", "REPO", "SOUR", "SUBM"}
POINTER_REQUIRED_TAGS = {
    "ALIA",
    "ASSO",
    "CHIL",
    "FAMC",
    "FAMS",
    "HUSB",
    "REPO",
    "SUBM",
    "WIFE",
}


class _GedcomLineStore:
    __slots__ = ("_text", "_offsets")

    def __init__(self, text):
        self._text = text
        offsets = array("Q", [0])
        line_end = text.find("\n")
        while line_end >= 0:
            offsets.append(line_end + 1)
            line_end = text.find("\n", line_end + 1)
        self._offsets = offsets

    def __len__(self):
        return len(self._offsets) - 1

    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            return [self[line_index] for line_index in range(start, stop, step)]

        line_index = operator.index(index)
        if line_index < 0:
            line_index += len(self)
        if line_index < 0 or line_index >= len(self):
            raise IndexError("GEDCOM line index out of range")

        return self._text[self._offsets[line_index] : self._offsets[line_index + 1]]

    def __iter__(self):
        text = self._text
        start = 0
        for end in self._offsets[1:]:
            yield text[start:end]
            start = end


def _parse_line(line):
    stripped = line.strip()

    if not stripped:
        return None, None, None, None

    parts = stripped.split(None, 1)

    try:
        level = int(parts[0])
    except ValueError:
        return None, None, None, None

    if len(parts) == 1:
        return None, None, None, None

    pointer = None
    remainder = parts[1]

    if level == 0 and remainder.startswith("@"):
        sub = remainder.split(None, 2)

        pointer = sub[0]
        tag = sub[1] if len(sub) >= 2 else None
        value = sub[2] if len(sub) == 3 else ""

        return level, pointer, tag, value

    sub = remainder.split(None, 1)
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
            text = f.read()

        self.encoding_replacements = text.count("\ufffd")
        text = text.replace("\xa0", " ")
        if text and not text.endswith("\n"):
            text += "\n"
        self.lines = _GedcomLineStore(text)

        if self.encoding_replacements:
            logger.warning(
                "%s caractère(s) invalide(s) remplacé(s) lors de la lecture GEDCOM",
                self.encoding_replacements,
            )

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
        duplicate_pointers = set()
        duplicate_pointer_order = []
        unindexed_pointers = set()
        head_count = 0
        trailer_count = 0
        current_record_tag = None
        current_header_section = None
        head_level_one_tags = set()
        head_level_one_values = {}
        head_gedc_line = None
        head_gedc_count = 0
        head_gedc_version_count = 0
        head_gedc_form_count = 0
        head_gedc_version = None
        first_level_zero_tag = None
        last_level_zero_tag = None
        trailer_line = None

        for idx, line in enumerate(self.lines):
            line_number = idx + 1
            if not line.strip():
                errors.append(f"ligne {line_number} malformée")
                continue

            level, pointer, tag, value = _parse_line(line)
            if level is None or tag is None:
                errors.append(f"ligne {line_number} malformée")
                continue

            if level < 0:
                errors.append(f"niveau négatif ligne {line_number}")
            if previous_level is not None and level > previous_level + 1:
                errors.append(f"saut de niveau ligne {line_number}")
            previous_level = level

            if level > 0 and current_record_tag == "TRLR":
                errors.append(
                    f"TRLR ne doit pas contenir de sous-lignes ligne {line_number}"
                )

            if (
                level > 0
                and tag in {"HEAD", "TRLR"}
                and not (tag == "TRLR" and current_record_tag == "TRLR")
            ):
                errors.append(f"{tag} doit être au niveau 0 ligne {line_number}")

            if level == 0:
                current_record_tag = tag
                current_header_section = None
                if first_level_zero_tag is None:
                    first_level_zero_tag = tag
                last_level_zero_tag = tag
                if tag in POINTER_REQUIRED_RECORD_TAGS and pointer is None:
                    errors.append(
                        f"pointeur manquant pour l'enregistrement {tag} "
                        f"ligne {line_number}"
                    )
                if tag in {"HEAD", "TRLR"} and pointer is not None:
                    errors.append(f"pointeur inattendu ligne {line_number}")
                if tag in {"HEAD", "TRLR"} and value:
                    errors.append(
                        f"{tag} ne doit pas avoir de valeur ligne {line_number}"
                    )
                if tag == "HEAD":
                    head_count += 1
                elif tag == "TRLR":
                    trailer_count += 1
                    if trailer_line is None:
                        trailer_line = line_number
                if pointer:
                    indexed_entity = self._by_pointer.get(pointer)
                    if indexed_entity is not None:
                        if indexed_entity.start_index != idx:
                            if pointer not in duplicate_pointers:
                                duplicate_pointers.add(pointer)
                                duplicate_pointer_order.append(pointer)
                    elif pointer in unindexed_pointers:
                        if pointer not in duplicate_pointers:
                            duplicate_pointers.add(pointer)
                            duplicate_pointer_order.append(pointer)
                    else:
                        unindexed_pointers.add(pointer)
                    if not re.fullmatch(r"@[^@\s]+@", pointer):
                        errors.append(f"pointeur invalide ligne {line_number}")
            elif level == 1 and current_record_tag == "HEAD":
                current_header_section = tag
                head_level_one_tags.add(tag)
                head_level_one_values.setdefault(tag, []).append((line_number, value))
                if tag == "GEDC":
                    head_gedc_count += 1
                    if head_gedc_line is None:
                        head_gedc_line = line_number

            if current_record_tag == "HEAD" and current_header_section == "GEDC":
                if level == 2 and tag == "VERS":
                    head_gedc_version_count += 1
                    if head_gedc_version is None:
                        head_gedc_version = value.strip()
                    if not value.strip():
                        errors.append(
                            f"HEAD.GEDC.VERS ne doit pas être vide ligne {line_number}"
                        )
                elif level == 2 and tag == "FORM":
                    head_gedc_form_count += 1
                    if not value.strip():
                        errors.append(
                            f"HEAD.GEDC.FORM ne doit pas être vide ligne {line_number}"
                        )

            if tag == "GEDC" and not (level == 1 and current_record_tag == "HEAD"):
                errors.append(f"GEDC doit être au niveau 1 de HEAD ligne {line_number}")
            if (
                current_record_tag == "HEAD"
                and tag == "VERS"
                and not (
                    level == 2 and current_header_section in {"GEDC", "SOUR", "CHAR"}
                )
            ):
                errors.append(
                    f"VERS doit être au niveau 2 de HEAD.GEDC ou HEAD.SOUR "
                    f"ligne {line_number}"
                )
            if (
                current_record_tag == "HEAD"
                and tag == "FORM"
                and not (
                    level == 2 and current_header_section in {"GEDC", "CHAR", "PLAC"}
                )
            ):
                errors.append(
                    f"FORM doit être au niveau 2 de HEAD.GEDC ou HEAD.CHAR "
                    f"ligne {line_number}"
                )

            if level > 0:
                expected_source_tag = REFERENCE_SOURCE_TAGS.get(tag)
                if expected_source_tag and (
                    level != 1 or current_record_tag != expected_source_tag
                ):
                    errors.append(
                        f"{tag} doit être au niveau 1 d'un enregistrement "
                        f"{expected_source_tag} ligne {line_number}"
                    )

            if level > 0 and tag in REFERENCE_TAGS:
                if (value or "").startswith("@"):
                    if not re.fullmatch(r"@[^@\s]+@", value):
                        errors.append(
                            f"pointeur de référence invalide {value} ligne {line_number}"
                        )
                    else:
                        target = self._by_pointer.get(value)
                        if target is None:
                            errors.append(
                                f"référence inconnue {value} ligne {line_number}"
                            )
                        else:
                            expected_tag = REFERENCE_TARGET_TAGS[tag]
                            if target.tag != expected_tag:
                                errors.append(
                                    f"référence {value} de type {target.tag} incompatible "
                                    f"avec {tag} (type {expected_tag} attendu) "
                                    f"ligne {line_number}"
                                )
                elif tag in POINTER_REQUIRED_TAGS:
                    errors.append(
                        f"pointeur de référence manquant pour {tag} ligne {line_number}"
                    )

        errors.extend(
            f"pointeur dupliqué {pointer}" for pointer in duplicate_pointer_order
        )
        if head_count != 1:
            errors.append("HEAD absent ou multiple")
        if trailer_count != 1:
            errors.append("TRLR absent ou multiple")
        if first_level_zero_tag is not None and first_level_zero_tag != "HEAD":
            errors.append("HEAD doit être le premier enregistrement")
        if trailer_count == 1 and last_level_zero_tag != "TRLR":
            errors.append(
                f"TRLR doit être le dernier enregistrement ligne {trailer_line}"
            )
        if head_gedc_line is not None:
            if head_gedc_count > 1:
                errors.append("HEAD.GEDC multiple")
            if head_gedc_version_count == 0:
                errors.append(f"HEAD.GEDC.VERS manquant ligne {head_gedc_line}")
            elif head_gedc_version_count > 1:
                errors.append("HEAD.GEDC.VERS multiple")
            if head_gedc_form_count == 0:
                errors.append(f"HEAD.GEDC.FORM manquant ligne {head_gedc_line}")
            elif head_gedc_form_count > 1:
                errors.append("HEAD.GEDC.FORM multiple")
        if head_gedc_version == "5.5.1":
            for required_tag in ("SOUR", "CHAR"):
                if required_tag not in head_level_one_tags:
                    errors.append(f"HEAD.{required_tag} manquant pour GEDCOM 5.5.1")
                else:
                    for line_number, value in head_level_one_values[required_tag]:
                        if not value.strip():
                            errors.append(
                                f"HEAD.{required_tag} ne doit pas être vide "
                                f"ligne {line_number}"
                            )
        return errors

    def _parse_entities(self):
        self.entities = {}
        self._by_pointer = {}
        self.malformed_lines = []

        current_pointer = None
        current_tag = None
        current_start_index = None
        current_has_malformed_lines = False

        for idx, line in enumerate(self.lines):
            level, pointer, tag, _ = _parse_line(line)
            if level is None:
                if line.strip():
                    line_number = idx + 1
                    self.malformed_lines.append(line_number)
                    logger.warning(
                        "Ligne GEDCOM malformée ignorée (%s)",
                        line_number,
                    )
                    if current_tag is not None:
                        current_has_malformed_lines = True
                continue

            if level == 0:
                if current_tag is not None:
                    entity = self._make_entity(
                        pointer=current_pointer,
                        tag=current_tag,
                        start_index=current_start_index,
                        end_index=idx,
                        has_malformed_lines=current_has_malformed_lines,
                    )
                    self._register_entity(entity)

                current_pointer = pointer
                current_tag = tag
                current_start_index = idx
                current_has_malformed_lines = False

        if current_tag is not None:
            entity = self._make_entity(
                pointer=current_pointer,
                tag=current_tag,
                start_index=current_start_index,
                end_index=len(self.lines),
                has_malformed_lines=current_has_malformed_lines,
            )
            self._register_entity(entity)

    def _make_entity(self, pointer, tag, start_index, end_index, has_malformed_lines):
        if has_malformed_lines:
            lines = [
                line if line.endswith("\n") else line + "\n"
                for line in self.lines[start_index:end_index]
                if _parse_line(line)[0] is not None
            ]
            return GedcomEntity(pointer, tag, start_index, lines)

        return GedcomEntity(
            pointer,
            tag,
            start_index,
            source_lines=self.lines,
            end_index=end_index,
        )

    def _register_entity(self, entity: "GedcomEntity"):
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
    __slots__ = (
        "pointer",
        "tag",
        "start_index",
        "_lines",
        "_source_lines",
        "_end_index",
    )

    def __init__(
        self,
        pointer,
        tag,
        start_index,
        lines=None,
        *,
        source_lines=None,
        end_index=None,
    ):
        self.pointer = pointer  # ex: "@I1@" ou None
        self.tag = tag  # ex: "INDI", "FAM", "HEAD", "NOTE"
        self.start_index = start_index  # index de la ligne "0 ..."
        self._lines = lines
        self._source_lines = source_lines
        self._end_index = end_index

    @property
    def lines(self):
        if self._source_lines is None:
            return self._lines
        lines = self._source_lines[self.start_index : self._end_index]
        if all(line.endswith("\n") for line in lines):
            return lines
        return [line if line.endswith("\n") else line + "\n" for line in lines]

    @lines.setter
    def lines(self, value):
        self._lines = value
        self._source_lines = None
        self._end_index = None

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
