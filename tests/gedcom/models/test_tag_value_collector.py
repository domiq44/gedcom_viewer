"""Tests du collecteur de valeurs de tags en une passe."""

import unittest
from types import SimpleNamespace

from gedcom.models.tag_values import (
    TagValueCollector,
    get_subtag_values,
    get_tag_values,
)


def make_entity(lines):
    """Construit une entité minimale exposant des lignes déjà parsées."""
    return SimpleNamespace(parsed_lines=lambda: lines)


class TestTagValueCollector(unittest.TestCase):
    """Vérifie que le collecteur reproduit les fonctions de référence."""

    # Vérifie collector matches get_tag_values.
    def test_collector_matches_get_tag_values(self):
        # Given une entité avec des tags et des continuations
        lines = [
            (1, None, "NAME", "John /Doe/"),
            (1, None, "SEX", "M"),
            (1, None, "NOTE", "first"),
            (2, None, "CONT", "second"),
        ]
        # When on collecte les valeurs en une passe
        collector = TagValueCollector(
            lines, tags=(("NAME", 1), ("SEX", 1), ("NOTE", None))
        )
        # Then chaque requête donne le même résultat que la fonction de référence
        entity = make_entity(lines)
        self.assertEqual(
            collector.values("NAME", level=1), get_tag_values(entity, "NAME", level=1)
        )
        self.assertEqual(
            collector.values("SEX", level=1), get_tag_values(entity, "SEX", level=1)
        )
        self.assertEqual(collector.values("NOTE"), get_tag_values(entity, "NOTE"))

    # Vérifie collector matches get_subtag_values.
    def test_collector_matches_get_subtag_values(self):
        # Given une entité avec des sous-tags
        lines = [
            (1, None, "BIRT", "b"),
            (2, None, "DATE", "1 JAN 1900"),
            (2, None, "PLAC", "Paris"),
            (1, None, "DEAT", "d"),
            (2, None, "DATE", "1980"),
        ]
        # When on collecte les sous-tags en une passe
        collector = TagValueCollector(
            lines,
            subtags=(("BIRT", "DATE"), ("BIRT", "PLAC"), ("DEAT", "DATE")),
        )
        # Then chaque requête donne le même résultat que la fonction de référence
        entity = make_entity(lines)
        for parent, child in (("BIRT", "DATE"), ("BIRT", "PLAC"), ("DEAT", "DATE")):
            self.assertEqual(
                collector.subtag_values(parent, child),
                get_subtag_values(entity, parent, child),
            )

    # Vérifie collector returns empty values for unknown queries.
    def test_collector_returns_empty_values_for_unknown_queries(self):
        # Given un collecteur sans requête
        collector = TagValueCollector([(1, None, "NAME", "John")])
        # When on interroge un tag inconnu
        # Then aucune valeur n'est retournée
        self.assertEqual(collector.values("UNKNOWN", level=1), [])
        self.assertIsNone(collector.last("UNKNOWN"))
        self.assertEqual(collector.subtag_values("BIRT", "DATE"), [])
        self.assertIsNone(collector.subtag("BIRT", "DATE"))

    # Vérifie collector exposes last values.
    def test_collector_exposes_last_values(self):
        # Given une entité avec deux valeurs pour le même tag
        lines = [(1, None, "NAME", "first"), (1, None, "NAME", "second")]
        # When on collecte puis on lit la dernière valeur
        collector = TagValueCollector(lines, tags=(("NAME", 1),))
        # Then la dernière valeur est retournée
        self.assertEqual(collector.values("NAME", level=1), ["first", "second"])
        self.assertEqual(collector.last("NAME", level=1), "second")


if __name__ == "__main__":
    unittest.main()
