"""Tests du parseur GEDCOM : test line store."""

import unittest

from gedcom.parser import (
    _GedcomLineStore,
)


class TestGedcomLineStore(unittest.TestCase):
    """Vérifie l'indexation paresseuse des lignes GEDCOM."""

    # Vérifie getitem supports negative index.
    def test_getitem_supports_negative_index(self):
        store = _GedcomLineStore("first\nsecond\n")

        self.assertEqual(store[-1], "second\n")

    # Vérifie getitem raises for out of range index.
    def test_getitem_raises_for_out_of_range_index(self):
        store = _GedcomLineStore("first\n")

        with self.assertRaises(IndexError):
            store[2]


if __name__ == "__main__":
    unittest.main()
