"""Enregistrement GEDCOM paresseux (lignes et tags)."""

from gedcom.line_parser import parse_line
from gedcom.models.tag_values import (
    get_subtag_values as get_entity_subtag_values,
)
from gedcom.models.tag_values import (
    get_tag_values as get_entity_tag_values,
)


class GedcomEntity:
    """Enregistrement GEDCOM paresseux (lignes et tags)."""

    __slots__ = (
        "pointer",
        "tag",
        "start_index",
        "_lines",
        "_source_lines",
        "_end_index",
        "_filter_malformed",
        "_parsed",
        "_parsed_source",
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
        filter_malformed=False,
        parsed_source=None,
    ):
        """Initialise l'instance."""
        self.pointer = pointer  # ex: "@I1@" ou None
        self.tag = tag  # ex: "INDI", "FAM", "HEAD", "NOTE"
        self.start_index = start_index  # index de la ligne "0 ..."
        self._lines = lines
        self._source_lines = source_lines
        self._end_index = end_index
        self._filter_malformed = filter_malformed
        self._parsed = None
        self._parsed_source = parsed_source

    def _parsed_slice(self):
        """Retourne les tuples parsés de l'entité issus du parse global."""
        if self._parsed_source is None:
            return None
        return self._parsed_source[self.start_index : self._end_index]

    @property
    def lines(self):
        """Retourne les lignes de l'entité (chargement paresseux et cache)."""
        if self._lines is None and self._source_lines is not None:
            lines = self._source_lines[self.start_index : self._end_index]
            if self._filter_malformed:
                parsed_slice = self._parsed_slice()
                if parsed_slice is None:
                    lines = [line for line in lines if parse_line(line)[0] is not None]
                else:
                    lines = [
                        line
                        for line, parsed in zip(lines, parsed_slice)
                        if parsed[2] is not None
                    ]
            if not all(line.endswith("\n") for line in lines):
                lines = [line if line.endswith("\n") else line + "\n" for line in lines]
            self._lines = lines
        return self._lines

    @lines.setter
    def lines(self, value):
        """Définit les lignes de l'entité."""
        self._lines = value
        self._source_lines = None
        self._end_index = None
        self._filter_malformed = False
        self._parsed = None
        self._parsed_source = None

    def raw_block(self):
        """Retourne le bloc GEDCOM brut de l'entité."""
        return "".join(self.lines)

    def parsed_lines(self):
        """Retourne les tuples (niveau, pointeur, tag, valeur) parsés et mis en cache."""
        if self._parsed is None:
            parsed_slice = self._parsed_slice()
            if parsed_slice is None:
                self._parsed = [parse_line(line) for line in self.lines]
            elif self._filter_malformed:
                self._parsed = [item for item in parsed_slice if item[2] is not None]
            else:
                self._parsed = list(parsed_slice)
        return self._parsed

    def get_tag_values(self, tag, level=None):
        """Retourne toutes les valeurs du tag donné."""
        return get_entity_tag_values(self, tag, level)

    def get_tag_value(self, tag):
        """Retourne la première valeur du tag donné."""
        values = self.get_tag_values(tag)
        return values[0] if values else ""

    def get_subtag_values(self, parent_tag, child_tag):
        """Retourne les valeurs des sous-tags du tag donné."""
        return get_entity_subtag_values(self, parent_tag, child_tag)
