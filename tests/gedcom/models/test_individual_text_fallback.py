"""Tests du repli de chargement des textes sans get_tag_values de l'individu."""

import unittest
from types import SimpleNamespace

from gedcom.models.entity import GedcomEntity
from gedcom.models.individual import Individual


def make_individual(lines):
    """Construit un individu à partir de lignes GEDCOM."""
    entity = GedcomEntity("@I1@", "INDI", 0, lines=lines)
    return Individual(entity)


class TestIndividualTextFallback(unittest.TestCase):
    """Vérifie le repli de chargement des textes sans get_tag_values."""

    # Vérifie text ignores continuation under nested note.
    def test_text_ignores_continuation_under_nested_note(self):
        # Given un individu avec une continuation sous un sous-tag
        individual = make_individual(
            [
                "0 @I1@ INDI\n",
                "1 NAME John /Doe/\n",
                "1 TEXT hello\n",
                "2 NOTE note\n",
                "3 CONT more\n",
            ]
        )
        # When on lit les textes
        texts = individual.texts
        # Then le CONT du NOTE ne pollue pas le TEXT
        self.assertEqual(texts, ["hello"])

    # Vérifie texts fallback without get tag values.
    def test_texts_fallback_without_get_tag_values(self):
        # Given une entité sans get_tag_values
        entity = SimpleNamespace(
            pointer="@I1@",
            parsed_lines=lambda: [
                (None, None, None, None),
                (0, "@I1@", "INDI", ""),
                (1, None, "TEXT", "hello"),
                (2, None, "CONT", "world"),
                (1, None, "NAME", "x"),
            ],
        )
        individual = Individual(entity)
        # When on lit les textes
        texts = individual.texts
        # Then le repli fusionne les continuations
        self.assertEqual(texts, ["hello\nworld"])


if __name__ == "__main__":
    unittest.main()
