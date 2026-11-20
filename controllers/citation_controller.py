"""Contrôleur des citations d'événements GEDCOM."""

import logging
import re
import threading

from gedcom.line_parser import parse_line
from gedcom.models.citation import Citation

logger = logging.getLogger(__name__)


class CitationController:
    """Indexe les citations pointant vers des enregistrements SOUR connus."""

    def __init__(self, parser):
        """Initialise le contrôleur sans construire l'index."""
        self.parser = parser
        self._citations = None
        self._citations_lock = threading.Lock()

    def _ensure_citations(self):
        """Construit l'index des citations au premier accès."""
        if self._citations is None:
            with self._citations_lock:
                if self._citations is None:
                    self._citations = self._build_citations()
        return self._citations

    def list_citations(self):
        """Retourne la liste des citations indexées."""
        return list(self._ensure_citations())

    @property
    def has_citations(self):
        """Indique si des citations sont présentes."""
        return bool(self._ensure_citations())

    def _build_citations(self):
        """Construit l'index des citations SOUR des enregistrements."""
        citations = []

        for records in self.parser.entities.values():
            for record in records:
                try:
                    citations.extend(self._record_citations(record))
                except Exception:
                    logger.exception(
                        "Échec de l'indexation des citations de %s",
                        getattr(record, "pointer", None),
                    )

        return citations

    def _record_citations(self, record):
        """Retourne les citations d'un enregistrement."""
        if not record.pointer:
            return []

        try:
            lines = record.lines
        except Exception:
            logger.exception(
                "Échec de lecture des lignes de %s",
                getattr(record, "pointer", None),
            )
            return []

        citations = []
        seen = set()
        current_section = ""
        active_citation = None

        for raw in lines:
            level, _pointer, tag, value = parse_line(raw)
            if level is None:
                continue

            # Nouveau niveau 1 : on quitte la section de citation en cours,
            # sauf si c'est une ligne SOUR qui démarre une nouvelle citation.
            if level == 1 and tag != "SOUR":
                active_citation = None

            if active_citation is not None:
                active_citation = self._continue_citation(
                    active_citation, raw, level, tag, value
                )

            if level == 1:
                current_section = tag

            citation = self._new_citation(
                record, current_section, level, raw, tag, value
            )
            if citation is not None:
                active_citation = citation
                # Dedoublonnage sur l'empreinte complete de la citation
                key = (
                    citation.source_pointer,
                    citation.owner_pointer,
                    citation.owner_type,
                    citation.level,
                    citation.context_tag,
                    tuple(citation.gedcom_lines),
                )
                if key not in seen:
                    seen.add(key)
                    citations.append(citation)

        return citations

    def _continue_citation(self, citation, raw, level, tag, value):
        """Met à jour une citation en cours ; renvoie None si elle se termine."""
        if level <= citation.level:
            return None
        citation.gedcom_lines.append(raw)
        if level == citation.level + 1 and tag == "PAGE":
            citation.page = (value or "").strip()
        return citation

    def _new_citation(self, record, current_section, level, raw, tag, value):
        """Construit une citation lorsqu'une ligne référence une source connue."""
        if tag != "SOUR" or level <= 0:
            return None
        source_pointer = (value or "").strip()
        if not re.fullmatch(r"@[^@\s]+@", source_pointer):
            return None
        source_record = self.parser.get_entity(source_pointer)
        if source_record is None or source_record.tag != "SOUR":
            return None
        return Citation(
            source_pointer=source_pointer,
            owner_pointer=record.pointer,
            owner_type=record.tag,
            level=level,
            context_tag=current_section if level > 1 else "",
            gedcom_lines=[raw],
        )
