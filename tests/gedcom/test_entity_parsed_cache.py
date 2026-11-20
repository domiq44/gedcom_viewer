"""Tests du parseur GEDCOM : test entity parsed cache."""

import unittest

from gedcom.parser import (
    GedcomParser,
)
from tests.gedcom.test_gedcom_parser_common import (
    SAMPLE_GEDCOM,
)


class TestGedcomEntityParsedCache(unittest.TestCase):
    """Vérifie la mise en cache des lignes parsées par entité."""

    def _build_entity(self):
        parser = GedcomParser()
        parser.lines = SAMPLE_GEDCOM.splitlines()
        parser._parse_entities()
        return parser.get_entity("@I1@")

    # Vérifie parsed lines are cached.
    def test_parsed_lines_are_cached(self):
        # Given (Arrange) une entité parsée
        entity = self._build_entity()
        # When (Act) on demande deux fois les lignes parsées
        first = entity.parsed_lines()
        second = entity.parsed_lines()
        # Then (Assert) la même liste en cache est renvoyée
        self.assertIs(first, second)

    # Vérifie get tag values uses cache.
    def test_get_tag_values_uses_cache(self):
        # Given (Arrange) une entité
        entity = self._build_entity()
        # When (Act) on extrait une valeur de tag
        entity.get_tag_values("NAME")
        # Then (Assert) le cache de parsing est peuplé
        self.assertIsNotNone(entity._parsed)


if __name__ == "__main__":
    unittest.main()
