"""Tests du point de conversion canonique des champs GEDCOM."""

import unittest

from gedcom.models.details import (
    field_details,
    field_parts,
    field_tag,
    field_value,
    new_field,
)


class TestDetails(unittest.TestCase):
    """Vérifie la création et la lecture des champs canoniques."""

    # Vérifie new field builds a canonical dict.
    def test_new_field_builds_a_canonical_dict(self):
        # Given (Arrange) un tag, une valeur et des détails
        # When (Act) on crée le champ
        field = new_field("EXTRA", "value", [("CHILD", "detail")])
        # Then (Assert) la forme canonique est respectée
        self.assertEqual(
            field,
            {"tag": "EXTRA", "value": "value", "details": [("CHILD", "detail")]},
        )

    # Vérifie new field copies the details list.
    def test_new_field_copies_the_details_list(self):
        # Given (Arrange) une liste de détails
        details = [("CHILD", "detail")]
        # When (Act) on crée le champ puis on modifie la liste source
        field = new_field("EXTRA", "value", details)
        details.append(("OTHER", "detail"))
        # Then (Assert) le champ n'est pas affecté
        self.assertEqual(field["details"], [("CHILD", "detail")])

    # Vérifie field parts reads a dict field.
    def test_field_parts_reads_a_dict_field(self):
        # Given (Arrange) un champ canonique
        field = {"tag": "EXTRA", "value": "value", "details": [("CHILD", "detail")]}
        # When (Act) on décompose le champ
        parts = field_parts(field)
        # Then (Assert) le tag, la valeur et les détails sont retournés
        self.assertEqual(parts, ("EXTRA", "value", [("CHILD", "detail")]))

    # Vérifie field parts reads a tuple field.
    def test_field_parts_reads_a_tuple_field(self):
        # Given (Arrange) un champ sous forme de tuple
        field = ("EVEN", "value", [("TYPE", "detail")])
        # When (Act) on décompose le champ
        parts = field_parts(field)
        # Then (Assert) le tag, la valeur et les détails sont retournés
        self.assertEqual(parts, ("EVEN", "value", [("TYPE", "detail")]))

    # Vérifie field parts defaults are empty.
    def test_field_parts_defaults_are_empty(self):
        # Given (Arrange) un tuple vide
        # When (Act) on décompose le champ
        tag, value, details = field_parts(())
        # Then (Assert) les valeurs par défaut sont vides
        self.assertEqual((tag, value, details), ("", "", []))

    # Vérifie accessors expose tag, value and details.
    def test_accessors_expose_tag_value_and_details(self):
        # Given (Arrange) un champ canonique
        field = new_field("EXTRA", "value", [("CHILD", "detail")])
        # When (Act) on lit les accesseurs
        # Then (Assert) chaque accesseur retourne la bonne partie
        self.assertEqual(field_tag(field), "EXTRA")
        self.assertEqual(field_value(field), "value")
        self.assertEqual(field_details(field), [("CHILD", "detail")])


if __name__ == "__main__":
    unittest.main()
