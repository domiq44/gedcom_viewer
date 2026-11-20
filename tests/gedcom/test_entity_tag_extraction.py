"""Tests du parseur GEDCOM : test entity tag extraction."""

import unittest

from gedcom.models.entity import GedcomEntity


class TestGedcomEntityTagExtraction(unittest.TestCase):
    """Vérifie l'extraction des tags et continuations d'une entité."""

    # Vérifie get tag values ignores malformed line.
    def test_get_tag_values_ignores_malformed_line(self):
        entity = GedcomEntity(
            "@I1@",
            "INDI",
            0,
            ["0 @I1@ INDI", "invalid", "1 NAME John /Doe/"],
        )

        self.assertEqual(entity.get_tag_values("NAME"), ["John /Doe/"])

    # Vérifie get subtag values ignores malformed line.
    def test_get_subtag_values_ignores_malformed_line(self):
        entity = GedcomEntity(
            "@I1@",
            "INDI",
            0,
            ["0 @I1@ INDI", "invalid", "1 BIRT", "2 DATE 1 JAN 1900"],
        )

        self.assertEqual(entity.get_subtag_values("BIRT", "DATE"), ["1 JAN 1900"])

    # Vérifie lines setter replaces lines and resets cache.
    def test_lines_setter_replaces_lines_and_resets_cache(self):
        entity = GedcomEntity("@I1@", "INDI", 0, ["0 @I1@ INDI"])
        entity.parsed_lines()

        entity.lines = ["0 @I1@ INDI", "1 NAME A"]

        self.assertEqual(entity.lines, ["0 @I1@ INDI", "1 NAME A"])
        self.assertIsNone(entity._parsed)


if __name__ == "__main__":
    unittest.main()
