"""Analyseur GEDCOM et stockage paresseux des lignes."""

import codecs
import logging
import operator
import threading
from array import array

from gedcom.errors import GedcomLoadCancelled
from gedcom.line_parser import parse_line
from gedcom.models.entity import GedcomEntity
from gedcom.validator import GedcomValidator

logger = logging.getLogger(__name__)
_encoding_error_state = threading.local()


def _replace_invalid_utf8(error):
    """Encodeur d'erreurs remplaçant les octets UTF-8 invalides."""
    if not isinstance(error, UnicodeDecodeError):
        raise error
    _encoding_error_state.replacements += 1
    return "\ufffd", error.end


codecs.register_error("gedcom_viewer_replace_invalid_utf8", _replace_invalid_utf8)


class _GedcomLineStore:
    """Séquence paresseuse de lignes GEDCOM indexées par offsets."""

    __slots__ = ("_text", "_offsets")

    def __init__(self, text):
        """Initialise l'instance."""
        self._text = text
        offsets = array("Q", [0])
        line_end = text.find("\n")
        while line_end >= 0:
            offsets.append(line_end + 1)
            line_end = text.find("\n", line_end + 1)
        self._offsets = offsets

    def __len__(self):
        """Retourne le nombre de lignes."""
        return len(self._offsets) - 1

    def __getitem__(self, index):
        """Retourne la ligne demandée (ou une liste pour un slice)."""
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
        """Itère sur les lignes."""
        text = self._text
        start = 0
        for end in self._offsets[1:]:
            yield text[start:end]
            start = end


class GedcomParser:
    """Analyseur GEDCOM exposant les entités et les erreurs."""

    MAX_MALFORMED_LINES = 100
    MAX_REPORTED_MALFORMED_LINES = 10

    def __init__(self):
        """Initialise l'instance."""
        self.lines: _GedcomLineStore | list[str] = []
        self.entities = {}  # dict: type → liste de GedcomEntity
        self._by_pointer = {}  # dict: pointer → GedcomEntity
        self.malformed_lines = []
        self.malformed_count = 0
        self.encoding_replacements = 0
        self.validation_errors = []
        self._parsed_lines = None
        self._validator = GedcomValidator(parse_line)

    @staticmethod
    def _check_cancelled(cancel_event):
        """Lève une exception si le chargement a été annulé."""
        if cancel_event is not None and cancel_event.is_set():
            raise GedcomLoadCancelled("Chargement GEDCOM annulé")

    def load(self, filename, strict=False, cancel_event=None):
        """Charge et analyse un fichier GEDCOM."""
        self._check_cancelled(cancel_event)
        _encoding_error_state.replacements = 0
        try:
            with open(
                filename,
                "r",
                encoding="utf-8-sig",
                errors="gedcom_viewer_replace_invalid_utf8",
            ) as f:
                text = f.read()
            self.encoding_replacements = _encoding_error_state.replacements
        finally:
            del _encoding_error_state.replacements

        self._check_cancelled(cancel_event)
        text = text.replace("\xa0", " ")
        if text and not text.endswith("\n"):
            text += "\n"
        self.lines = _GedcomLineStore(text)

        if self.encoding_replacements:
            logger.warning(
                "%s caractère(s) invalide(s) remplacé(s) lors de la lecture GEDCOM",
                self.encoding_replacements,
            )

        self._parse_entities(cancel_event=cancel_event)
        self.validation_errors = self.validate(
            self._parsed_lines, cancel_event=cancel_event
        )
        self._log_validation_errors()
        if strict and self.validation_errors:
            raise ValueError(
                "Fichier GEDCOM invalide: " + "; ".join(self.validation_errors)
            )

    def _log_validation_errors(self):
        """Journalise les anomalies de validation de manière bornée."""
        errors = self.validation_errors
        if not errors:
            return

        reported = errors[: self.MAX_REPORTED_MALFORMED_LINES]
        for error in reported:
            logger.warning("Validation GEDCOM: %s", error)
        if len(errors) > len(reported):
            logger.warning(
                "Validation GEDCOM: %d anomalie(s) supplémentaire(s) non journalisée(s)",
                len(errors) - len(reported),
            )

    def validate(self, parsed_lines=None, cancel_event=None):
        """Retourne les anomalies structurelles détectées dans le fichier chargé."""
        return self._validator.validate(
            self.lines,
            self._by_pointer,
            parsed_lines=parsed_lines,
            cancel_event=cancel_event,
        )

    def _parse_entities(self, cancel_event=None):
        """Construit l'index des entités depuis les lignes."""
        self.entities = {}
        self._by_pointer = {}
        self.malformed_lines = []
        self.malformed_count = 0
        self._parsed_lines = []
        for line in self.lines:
            self._check_cancelled(cancel_event)
            self._parsed_lines.append(parse_line(line))

        current_pointer = None
        current_tag = None
        current_start_index = None
        current_has_malformed_lines = False

        for idx, line in enumerate(self.lines):
            self._check_cancelled(cancel_event)
            level, pointer, tag, _ = self._parsed_lines[idx]
            if level is None:
                if line.strip():
                    line_number = idx + 1
                    self._record_malformed_line(line_number)
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

        self._log_malformed_lines()

    def _record_malformed_line(self, line_number):
        """Enregistre une ligne malformée sans borner la mémoire du rapport."""
        self.malformed_count += 1
        if len(self.malformed_lines) < self.MAX_MALFORMED_LINES:
            self.malformed_lines.append(line_number)

    def _log_malformed_lines(self):
        """Journalise un unique avertissement agrégé pour les lignes malformées."""
        if not self.malformed_count:
            return

        reported = self.malformed_lines[: self.MAX_REPORTED_MALFORMED_LINES]
        locations = ", ".join(str(number) for number in reported)
        if self.malformed_count > len(reported):
            locations += ", …"
        logger.warning(
            "%d ligne(s) GEDCOM malformée(s) ignorée(s) (%s)",
            self.malformed_count,
            locations,
        )

    def _make_entity(self, pointer, tag, start_index, end_index, has_malformed_lines):
        """Crée l'entité correspondant à un enregistrement."""
        return GedcomEntity(
            pointer,
            tag,
            start_index,
            source_lines=self.lines,
            end_index=end_index,
            filter_malformed=has_malformed_lines,
            parsed_source=self._parsed_lines,
        )

    def _register_entity(self, entity: "GedcomEntity"):
        """Indexe l'entité par pointeur."""
        if entity.tag is None:
            logger.warning("Enregistrement GEDCOM sans tag ignoré: %s", entity.pointer)
            return

        if entity.pointer:
            if entity.pointer in self._by_pointer:
                logger.warning(
                    "Pointeur GEDCOM dupliqué, première occurrence conservée: %s",
                    entity.pointer,
                )
                return
            self._by_pointer[entity.pointer] = entity

        self.entities.setdefault(entity.tag, []).append(entity)

    def get_entity(self, pointer):
        """Retourne l'entité correspondant au pointeur."""
        return self._by_pointer.get(pointer)

    def _extract_level_zero_block(self, tag):
        """Retourne le bloc normalisé d'un enregistrement de niveau zéro."""
        parsed_lines = self._parsed_lines
        if parsed_lines is None or len(parsed_lines) != len(self.lines):
            parsed_lines = [parse_line(line) for line in self.lines]
        return self._format_level_zero_block(self.lines, parsed_lines, tag)

    @staticmethod
    def _format_level_zero_block(lines, parsed_lines, tag):
        """Formate le bloc d'un enregistrement de niveau zéro déjà analysé."""
        block_lines = []
        inside = False

        for line, (level, _, line_tag, _) in zip(lines, parsed_lines):
            if line_tag is None:
                continue

            if level == 0:
                if line_tag == tag and not inside:
                    inside = True
                    block_lines = [line.strip()]
                elif inside:
                    break
            elif inside:
                block_lines.append(line.strip())

        return "\n".join(block_lines).strip()

    def extract_head(self):
        """
        Retourne le bloc HEAD (0 HEAD ...), même sans pointeur.
        """
        return self._extract_level_zero_block("HEAD")

    def extract_trailer(self):
        """
        Retourne le bloc TRLR (0 TRLR ...), même sans pointeur.
        """
        return self._extract_level_zero_block("TRLR")
