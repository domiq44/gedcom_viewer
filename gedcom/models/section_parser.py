"""Analyse générique des sections d'un enregistrement GEDCOM."""

from gedcom.models.details import new_field
from gedcom.models.lazy_list import _LazyList


class AdditionalLinesMixin:
    """Sépare les champs de niveau 1, les sous-sections et les détails."""

    __slots__ = ()

    additional_fields = _LazyList()

    KNOWN_LEVEL_ONE_TAGS: frozenset[str] = frozenset()

    def _parse_additional_lines(self, lines):
        """Analyse les lignes en isolant le niveau 1 et les sous-sections."""
        current_section = None
        current_additional = None

        for level, _pointer, tag, value in lines:
            if level is None:
                continue

            if level == 1:
                current_section = tag
                current_additional = self._start_section(tag, value)
                continue

            current_section, current_additional = self._parse_subsection(
                current_section, current_additional, level, tag, value
            )

    def _start_section(self, tag, value):
        """Affecte un champ de niveau 1 et retourne le champ additionnel ouvert."""
        self._assign_level_one(tag, value)
        if tag in self.KNOWN_LEVEL_ONE_TAGS:
            return None
        return self._new_additional_field(tag, value)

    def _parse_subsection(self, current_section, current_additional, level, tag, value):
        """Analyse une sous-section et retourne la section et le champ courants."""
        self._assign_subsection(current_section, level, tag, value)
        if current_additional is not None:
            current_additional["details"].append((tag, value))
        return current_section, current_additional

    def _assign_level_one(self, tag, value):
        """Affecte un champ de niveau 1 (à surcharger)."""

    def _assign_subsection(self, current_section, level, tag, value):
        """Affecte un champ de sous-section (à surcharger)."""

    def _new_additional_field(self, tag, value):
        """Crée un champ additionnel et l'ajoute à la liste."""
        field = new_field(tag, value)
        self.additional_fields.append(field)
        return field
