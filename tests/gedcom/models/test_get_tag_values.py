"""Tests de l'extraction des valeurs et de la fusion des continuations."""

import unittest
from types import SimpleNamespace

from gedcom.models.tag_values import get_tag_values


def make_entity(lines):
    """Construit une entité minimale exposant des lignes déjà parsées."""
    return SimpleNamespace(parsed_lines=lambda: lines)


class TestGetTagValues(unittest.TestCase):
    """Vérifie l'extraction des valeurs et la fusion des continuations."""

    # Vérifie merges continuations into matching tag.
    def test_merges_continuations_into_matching_tag(self):
        # Given une entité avec un tag continué
        entity = make_entity(
            [
                (1, None, "NOTE", "first"),
                (2, None, "CONT", "second"),
                (2, None, "CONC", "!"),
            ]
        )
        # When on extrait les valeurs du tag
        values = get_tag_values(entity, "NOTE")
        # Then la continuation est fusionnée
        self.assertEqual(values, ["first\nsecond!"])

    # Vérifie ignores continuations of other tags.
    def test_ignores_continuations_of_other_tags(self):
        # Given une entité avec une continuation sous un autre tag
        entity = make_entity(
            [
                (1, None, "NOTE", "note"),
                (2, None, "SOUR", "@S1@"),
                (3, None, "CONT", "source detail"),
            ]
        )
        # When on extrait les valeurs du tag
        values = get_tag_values(entity, "NOTE")
        # Then la continuation du sous-tag n'est pas fusionnée
        self.assertEqual(values, ["note"])

    # Vérifie level filter ignores nested same tag.
    def test_level_filter_ignores_nested_same_tag(self):
        # Given une entité avec un tag imbriqué dans un autre
        entity = make_entity(
            [
                (1, None, "NOTE", "top"),
                (2, None, "NOTE", "nested"),
                (3, None, "CONT", "nested detail"),
            ]
        )
        # When on extrait uniquement les valeurs de niveau 1
        values = get_tag_values(entity, "NOTE", level=1)
        # Then la note imbriquée et sa continuation sont ignorées
        self.assertEqual(values, ["top"])


if __name__ == "__main__":
    unittest.main()
