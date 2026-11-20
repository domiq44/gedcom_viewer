"""Tests de l'ajout d'une continuation à une liste de valeurs."""

import unittest

from gedcom.models.tag_values import append_tag_value


class TestAppendTagValue(unittest.TestCase):
    """Vérifie l'ajout d'une continuation à une liste de valeurs."""

    # Vérifie creates value when list is empty.
    def test_creates_value_when_list_is_empty(self):
        # Given une liste vide
        values = []
        # When on ajoute une continuation CONT
        append_tag_value(values, "CONT", "first")
        # Then la valeur est créée
        self.assertEqual(values, ["first"])

    # Vérifie appends conc to last value.
    def test_appends_conc_to_last_value(self):
        # Given une valeur existante
        values = ["first"]
        # When on ajoute une continuation CONC
        append_tag_value(values, "CONC", " second")
        # Then la valeur est concaténée
        self.assertEqual(values, ["first second"])


if __name__ == "__main__":
    unittest.main()
