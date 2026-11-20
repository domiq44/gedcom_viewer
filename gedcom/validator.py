"""Validateur de structure GEDCOM 5.5.1."""

import re

from gedcom.errors import GedcomLoadCancelled

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
VALID_SEX_VALUES = {"M", "F", "X"}
KNOWN_LEVEL_ONE_TAGS = {
    "ABBR",
    "ADDR",
    "AFN",
    "AGE",
    "ALIA",
    "ANUL",
    "ASSO",
    "AUTH",
    "BAPL",
    "BAPM",
    "BARM",
    "BASM",
    "BIRT",
    "BLES",
    "CENS",
    "CHAN",
    "CHAR",
    "CHIL",
    "CHR",
    "CHRA",
    "CONF",
    "CONT",
    "CONC",
    "DATA",
    "DATE",
    "DEAT",
    "DEST",
    "DIV",
    "DIVF",
    "EMAIL",
    "EMIG",
    "ENGA",
    "EVEN",
    "FACT",
    "FAX",
    "FAMC",
    "FAMS",
    "FILE",
    "FORM",
    "GEDC",
    "GRAD",
    "HEAD",
    "HUSB",
    "IDNO",
    "IMMI",
    "LANG",
    "LATI",
    "LONG",
    "MAP",
    "MARR",
    "MARB",
    "MARC",
    "MARL",
    "MARS",
    "MEDI",
    "NAME",
    "NATU",
    "NCHI",
    "NICK",
    "NMR",
    "NOTE",
    "OBJE",
    "OCCU",
    "PHON",
    "PLAC",
    "POST",
    "PROB",
    "PROP",
    "PUBL",
    "REFN",
    "REPO",
    "RESN",
    "RESI",
    "RFN",
    "RIN",
    "SEX",
    "SETI",
    "SOUR",
    "SSN",
    "STAE",
    "SUBM",
    "TIME",
    "TITL",
    "TRLR",
    "TYPE",
    "VERS",
    "WIFE",
    "WILL",
    "WWW",
    "CTRY",
    "ADR1",
    "ADR2",
    "CITY",
    "CALN",
    "AGNC",
}
DATE_RE = re.compile(
    r"^(?:@#[A-Z0-9_]+@\s+)?"
    r"(?:(?:ABT|CAL|EST|BEF|AFT|INT)\s+)?"
    r"(?:"
    r"\d{4}(?:-\d{2}(?:-\d{2})?)?"
    r"|\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{4}"
    r"|(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{4}"
    r"|(?:FROM|BET)\s+.+\s+(?:TO|AND)\s+.+"
    r")$",
    re.IGNORECASE,
)


class _ValidationState:
    """État mutable accumulé pendant la validation d'un flux GEDCOM."""

    MAX_ERRORS = 1000

    def __init__(self):
        """Initialise l'état de validation."""
        self.errors = []
        self.total_errors = 0
        self.truncated = False
        self.previous_level = None
        self.duplicate_pointers = set()
        self.duplicate_pointer_order = []
        self.unindexed_pointers = set()
        self.head_count = 0
        self.trailer_count = 0
        self.current_record_tag = None
        self.record_tag_counts = {}
        self.record_start_line = None
        self.first_level_zero_tag = None
        self.last_level_zero_tag = None
        self.trailer_line = None
        self.header_record_tag = None
        self.header_section = None
        self.head_level_one_tags = set()
        self.head_level_one_values: dict[str, list[tuple[int, str]]] = {}
        self.gedc_count = 0
        self.gedc_line = None
        self.version_count = 0
        self.form_count = 0
        self.version = None

    def add_error(self, message):
        """Ajoute une erreur en bornant la taille du rapport."""
        self.total_errors += 1
        if self.truncated:
            return
        if len(self.errors) >= self.MAX_ERRORS:
            self.errors.append(
                f"... erreurs supplémentaires ignorées ({self.total_errors} au total)"
            )
            self.truncated = True
            return
        self.errors.append(message)


class GedcomValidator:
    """Valide la structure d’un flux GEDCOM déjà découpé en enregistrements."""

    def __init__(self, parse_line):
        """Initialise le validateur avec son parseur de ligne."""
        self._parse_line = parse_line

    def validate(self, lines, pointer_index, parsed_lines=None, cancel_event=None):
        """Valide la structure GEDCOM et retourne les erreurs."""
        state = _ValidationState()
        for idx, line in enumerate(lines):
            if cancel_event is not None and cancel_event.is_set():
                raise GedcomLoadCancelled("Validation GEDCOM annulée")
            line_number = idx + 1
            if parsed_lines is not None:
                level, pointer, tag, value = parsed_lines[idx]
            else:
                level, pointer, tag, value = self._parse_line(line)
            self._validate_record_line(
                state,
                line,
                line_number,
                idx,
                level,
                pointer,
                tag,
                value,
                pointer_index,
            )
            if level is None or tag is None:
                continue
            self._validate_header_line(state, line_number, level, tag, value)
            self._validate_reference_line(
                state, line_number, level, tag, value, pointer_index
            )
        self._finalize(state)
        return state.errors

    def _validate_record_line(
        self,
        state,
        line,
        line_number,
        idx,
        level,
        pointer,
        tag,
        value,
        pointer_index,
    ):
        """Valide la structure d'une ligne et les pointeurs d'enregistrement."""
        if not line.strip() or level is None or tag is None:
            state.add_error(f"ligne {line_number} malformée")
            return

        self._check_level_consistency(state, line, line_number, idx, level)
        self._check_level_one_value(state, line_number, level, tag, value)
        self._check_tag_line(state, line_number, level, tag)

        if level == 0:
            self._validate_level_zero(
                state, line_number, pointer, tag, value, idx, pointer_index
            )

    def _check_level_consistency(self, state, line, line_number, idx, level):
        """Vérifie la forme du niveau et la progression d'imbrication."""
        if idx == 0 and level != 0:
            state.add_error("la première ligne doit être un enregistrement de niveau 0")

        raw_level = line.strip().split(None, 1)[0]
        if level >= 0 and not re.fullmatch(r"0|[1-9][0-9]*", raw_level):
            state.add_error(f"niveau invalide ligne {line_number}")

        if level < 0:
            state.add_error(f"niveau négatif ligne {line_number}")
        if state.previous_level is not None and level > state.previous_level + 1:
            state.add_error(f"saut de niveau ligne {line_number}")
        state.previous_level = level

    def _check_level_one_value(self, state, line_number, level, tag, value):
        """Vérifie les valeurs propres aux tags de niveau 1."""
        if level == 1:
            state.record_tag_counts[tag] = state.record_tag_counts.get(tag, 0) + 1
            if tag not in KNOWN_LEVEL_ONE_TAGS and not tag.startswith("_"):
                state.add_error(f"tag inconnu {tag} ligne {line_number}")
            if tag == "SEX" and value.upper() not in VALID_SEX_VALUES:
                state.add_error(f"valeur SEX invalide {value} ligne {line_number}")
            if state.current_record_tag == "INDI" and tag in {"DATE", "PLAC", "TITL"}:
                state.add_error(
                    f"{tag} ne doit pas être au niveau 1 sous INDI ligne {line_number}"
                )

        if tag == "DATE" and not DATE_RE.fullmatch((value or "").strip()):
            state.add_error(f"date invalide {value} ligne {line_number}")

    def _check_tag_line(self, state, line_number, level, tag):
        """Vérifie qu'un tag de niveau 0 ne devient pas un sous-tag."""
        if level > 0 and state.current_record_tag == "TRLR":
            state.add_error(
                f"TRLR ne doit pas contenir de sous-lignes ligne {line_number}"
            )

        if (
            level > 0
            and tag in {"HEAD", "TRLR"}
            and not (tag == "TRLR" and state.current_record_tag == "TRLR")
        ):
            state.add_error(f"{tag} doit être au niveau 0 ligne {line_number}")

    def _validate_level_zero(
        self, state, line_number, pointer, tag, value, idx, pointer_index
    ):
        """Valide un enregistrement de niveau 0."""
        if state.current_record_tag is not None:
            self._finalize_record(state)
        state.current_record_tag = tag
        state.record_tag_counts = {}
        state.record_start_line = line_number
        if state.first_level_zero_tag is None:
            state.first_level_zero_tag = tag
        state.last_level_zero_tag = tag

        if tag in POINTER_REQUIRED_RECORD_TAGS and pointer is None:
            state.add_error(
                f"pointeur manquant pour l'enregistrement {tag} " f"ligne {line_number}"
            )
        if tag in {"HEAD", "TRLR"} and pointer is not None:
            state.add_error(f"pointeur inattendu ligne {line_number}")
        if tag in {"HEAD", "TRLR"} and value:
            state.add_error(f"{tag} ne doit pas avoir de valeur ligne {line_number}")

        if tag == "HEAD":
            state.head_count += 1
        elif tag == "TRLR":
            state.trailer_count += 1
            if state.trailer_line is None:
                state.trailer_line = line_number

        if pointer:
            self._validate_pointer(state, line_number, pointer, idx, pointer_index)

    def _validate_pointer(self, state, line_number, pointer, idx, pointer_index):
        """Valide le format et l'unicité d'un pointeur d'enregistrement."""
        indexed_entity = pointer_index.get(pointer)
        if indexed_entity is not None:
            if indexed_entity.start_index != idx:
                if pointer not in state.duplicate_pointers:
                    state.duplicate_pointers.add(pointer)
                    state.duplicate_pointer_order.append(pointer)
        elif pointer in state.unindexed_pointers:
            if pointer not in state.duplicate_pointers:
                state.duplicate_pointers.add(pointer)
                state.duplicate_pointer_order.append(pointer)
        else:
            state.unindexed_pointers.add(pointer)

        if not re.fullmatch(r"@[^@\s]+@", pointer):
            state.add_error(f"pointeur invalide ligne {line_number}")

    def _validate_header_line(self, state, line_number, level, tag, value):
        """Met à jour l'état d'en-tête pour une ligne."""
        if level == 0:
            state.header_record_tag = tag
            state.header_section = None
        elif state.header_record_tag == "HEAD":
            if level == 1:
                state.header_section = tag
                state.head_level_one_tags.add(tag)
                state.head_level_one_values.setdefault(tag, []).append(
                    (line_number, value)
                )
                if tag == "GEDC":
                    state.gedc_count += 1
                    if state.gedc_line is None:
                        state.gedc_line = line_number
            elif state.header_section == "GEDC" and level == 2:
                self._validate_gedc_line(state, line_number, tag, value)

        self._validate_header_tag(
            state,
            line_number,
            level,
            tag,
            state.header_record_tag,
            state.header_section,
        )

    def _validate_gedc_line(self, state, line_number, tag, value):
        """Valide une ligne VERS ou FORM de HEAD.GEDC."""
        if tag == "VERS":
            state.version_count += 1
            if state.version is None:
                state.version = value.strip()
            if not value.strip():
                state.add_error(
                    f"HEAD.GEDC.VERS ne doit pas être vide ligne {line_number}"
                )
        elif tag == "FORM":
            state.form_count += 1
            if not value.strip():
                state.add_error(
                    f"HEAD.GEDC.FORM ne doit pas être vide ligne {line_number}"
                )

    def _validate_header_tag(
        self, state, line_number, level, tag, current_record_tag, current_section
    ):
        """Valide le contexte d'un tag d'en-tête."""
        if tag == "GEDC" and not (level == 1 and current_record_tag == "HEAD"):
            state.add_error(f"GEDC doit être au niveau 1 de HEAD ligne {line_number}")
        if (
            current_record_tag == "HEAD"
            and tag == "VERS"
            and not (level == 2 and current_section in {"GEDC", "SOUR", "CHAR"})
        ):
            state.add_error(
                f"VERS doit être au niveau 2 de HEAD.GEDC ou HEAD.SOUR "
                f"ligne {line_number}"
            )
        if (
            current_record_tag == "HEAD"
            and tag == "FORM"
            and not (level == 2 and current_section in {"GEDC", "CHAR", "PLAC"})
        ):
            state.add_error(
                f"FORM doit être au niveau 2 de HEAD.GEDC ou HEAD.CHAR "
                f"ligne {line_number}"
            )

    def _finalize_header(self, state):
        """Finalise les règles d'en-tête GEDCOM 5.5.1."""
        self._check_gedc_header(state)
        if state.version == "5.5.1":
            self._check_required_level_one_tags(state)

    def _check_gedc_header(self, state):
        """Vérifie la présence et l'unicité du bloc HEAD.GEDC."""
        if state.head_count == 1 and state.gedc_line is None:
            state.add_error("HEAD.GEDC manquant")
        if state.gedc_line is None:
            return

        if state.gedc_count > 1:
            state.add_error("HEAD.GEDC multiple")
        if state.version_count == 0:
            state.add_error(f"HEAD.GEDC.VERS manquant ligne {state.gedc_line}")
        elif state.version_count > 1:
            state.add_error("HEAD.GEDC.VERS multiple")
        if state.form_count == 0:
            state.add_error(f"HEAD.GEDC.FORM manquant ligne {state.gedc_line}")
        elif state.form_count > 1:
            state.add_error("HEAD.GEDC.FORM multiple")

    def _check_required_level_one_tags(self, state):
        """Vérifie les tags obligatoires de HEAD pour la version courante."""
        for required_tag in ("SOUR", "CHAR"):
            values = state.head_level_one_values.get(required_tag, [])
            if required_tag not in state.head_level_one_tags:
                state.add_error(f"HEAD.{required_tag} manquant pour GEDCOM 5.5.1")
                continue
            if len(values) > 1:
                state.add_error(f"HEAD.{required_tag} multiple pour GEDCOM 5.5.1")
            for line_number, value in values:
                if not value.strip():
                    state.add_error(
                        f"HEAD.{required_tag} ne doit pas être vide "
                        f"ligne {line_number}"
                    )

        head_submitters = state.head_level_one_values.get("SUBM", [])
        if not head_submitters:
            state.add_error("HEAD.SUBM manquant pour GEDCOM 5.5.1")
        elif len(head_submitters) > 1:
            state.add_error("HEAD.SUBM multiple pour GEDCOM 5.5.1")

    def _validate_reference_line(
        self, state, line_number, level, tag, value, pointer_index
    ):
        """Valide le contexte et la valeur d'un tag de référence."""
        if level <= 0:
            return

        expected_source_tag = REFERENCE_SOURCE_TAGS.get(tag)
        if expected_source_tag and (
            level != 1 or state.current_record_tag != expected_source_tag
        ):
            state.add_error(
                f"{tag} doit être au niveau 1 d'un enregistrement "
                f"{expected_source_tag} ligne {line_number}"
            )

        if tag in REFERENCE_TAGS:
            self._validate_reference_value(
                state, line_number, tag, value, pointer_index
            )

    def _validate_reference_value(self, state, line_number, tag, value, pointer_index):
        """Valide la valeur d'un tag de référence."""
        if (value or "").startswith("@"):
            if not re.fullmatch(r"@[^@\s]+@", value):
                state.add_error(
                    f"pointeur de référence invalide {value} ligne {line_number}"
                )
                return

            target = pointer_index.get(value)
            if target is None:
                state.add_error(f"référence inconnue {value} ligne {line_number}")
                return

            expected_tag = REFERENCE_TARGET_TAGS[tag]
            if target.tag != expected_tag:
                state.add_error(
                    f"référence {value} de type {target.tag} incompatible "
                    f"avec {tag} (type {expected_tag} attendu) "
                    f"ligne {line_number}"
                )
        elif tag in POINTER_REQUIRED_TAGS:
            state.add_error(
                f"pointeur de référence manquant pour {tag} ligne {line_number}"
            )

    def _finalize_record(self, state):
        """Valide les cardinalités d'un enregistrement terminé."""
        tag = state.current_record_tag
        counts = state.record_tag_counts
        line_number = state.record_start_line or 0

        if tag == "INDI":
            if counts.get("NAME", 0) == 0:
                state.add_error(f"INDI NAME manquant ligne {line_number}")
            for child_tag in ("SEX", "BIRT", "DEAT", "CHR"):
                if counts.get(child_tag, 0) > 1:
                    state.add_error(
                        f"{child_tag} multiple dans INDI ligne {line_number}"
                    )
        elif tag == "FAM":
            for child_tag in ("HUSB", "WIFE", "MARR", "DIV"):
                if counts.get(child_tag, 0) > 1:
                    state.add_error(
                        f"{child_tag} multiple dans FAM ligne {line_number}"
                    )
        elif tag in {"REPO", "SUBM"}:
            if counts.get("NAME", 0) == 0:
                state.add_error(f"{tag} NAME manquant ligne {line_number}")

    def _finalize(self, state):
        """Ajoute les erreurs agrégées de fin de validation."""
        self._finalize_record(state)
        for pointer in state.duplicate_pointer_order:
            state.add_error(f"pointeur dupliqué {pointer}")
        if state.head_count != 1:
            state.add_error("HEAD absent ou multiple")
        if state.trailer_count != 1:
            state.add_error("TRLR absent ou multiple")
        if (
            state.first_level_zero_tag is not None
            and state.first_level_zero_tag != "HEAD"
        ):
            state.add_error("HEAD doit être le premier enregistrement")
        if state.trailer_count == 1 and state.last_level_zero_tag != "TRLR":
            state.add_error(
                f"TRLR doit être le dernier enregistrement ligne "
                f"{state.trailer_line}"
            )
        self._finalize_header(state)
